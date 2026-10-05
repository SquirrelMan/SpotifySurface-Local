"""使用 Windows 媒體狀態顯示免權杖同步歌詞。"""
import asyncio
import bisect
import concurrent.futures
import datetime
import logging
import queue
import re
import threading
import time
import tkinter as tk
import tkinter.font as tkFont
from typing import Any

import requests
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager


class PlaybackClock:
    """保留播放時間錨點，避免重複的 Windows 快照將字幕拉回。"""

    def __init__(self) -> None:
        self.position = 0.0
        self.anchor = 0.0
        self.playing = False
        self.snapshot: tuple[float, float] | None = None

    def currentPosition(self, now: float) -> float:
        """以單調時鐘推進播放時間。"""
        return max(0.0, self.position + (now - self.anchor if self.playing else 0.0))

    def accept(self, track: dict[str, Any], reset: bool = False) -> None:
        """新快照才校時；小幅誤差不回跳，拖曳進度則立即跟隨。"""
        now = track["received"]
        snapshot = (track["position"], track["updated"])
        candidate = track["position"]
        if track["playing"]:
            candidate += track["age"]
        predicted = self.currentPosition(now)
        changed = snapshot != self.snapshot
        # NOTE: 同一份快照每次輪詢都出現，不能把讀取時間當成新的播放起點。
        if reset or self.snapshot is None or track["playing"] != self.playing:
            self.position, self.anchor = candidate, now
        elif changed and (not track["playing"] or abs(candidate - predicted) > 1.5):
            self.position, self.anchor = candidate, now
        self.snapshot = snapshot
        self.playing = track["playing"]


def parseLyrics(text: str) -> list[tuple[float, str]]:
    """解析多時間標記的 LRC，保留空白間奏。"""
    result = []
    for line in text.splitlines():
        stamps = re.findall(r"\[(\d+):(\d+(?:\.\d+)?)\]", line)
        lyric = re.sub(r"\[[^]]*\]", "", line).strip()
        for minutes, seconds in stamps:
            result.append((int(minutes) * 60 + float(seconds), lyric))
    return sorted(result, key=lambda item: item[0])


def fetchLyrics(track: dict[str, Any]) -> dict[str, Any]:
    """優先精確比對歌曲，避免將不同版本歌詞套用至播放進度。"""
    params = {"track_name": track["title"], "artist_name": track["artist"]}
    if track["album"]:
        params["album_name"] = track["album"]
    if track["duration"] > 0:
        params["duration"] = str(round(track["duration"]))
    response = requests.get("https://lrclib.net/api/get", params=params,
                            headers={"User-Agent": "SpotifySurfaceLocal/1.0"}, timeout=15)
    if response.status_code == 404:
        return {}
    response.raise_for_status()
    body = response.json()
    return body if isinstance(body, dict) else {}


async def monitor(events: queue.Queue, stopEvent: threading.Event) -> None:
    """在背景執行 WinRT，避免阻塞歌詞視窗。"""
    while not stopEvent.is_set():
        try:
            manager = await MediaManager.request_async()
            sessions = list(manager.get_sessions())
            session = next((item for item in sessions if "spotify" in item.source_app_user_model_id.lower()), None)
            if session is None:
                events.put(("track", None))
            else:
                info = await session.try_get_media_properties_async()
                timeline = session.get_timeline_properties()
                status = session.get_playback_info().playback_status
                updated = timeline.last_updated_time.timestamp()
                age = max(0.0, datetime.datetime.now(datetime.timezone.utc).timestamp() - updated)
                events.put(("track", {"title": info.title, "artist": info.artist,
                            "album": info.album_title, "duration": timeline.end_time.total_seconds(),
                            "position": timeline.position.total_seconds(),
                            "playing": status.name == "PLAYING", "received": time.monotonic(),
                            "updated": updated, "age": age}))
        except (OSError, RuntimeError) as error:
            logging.warning("Media session unavailable: %s", type(error).__name__)
            events.put(("error", "無法讀取 Spotify，請確認桌面版已開啟並播放歌曲。"))
        await asyncio.sleep(0.5)


class LyricsWindow:
    """將媒體事件與歌詞結果統一交由 Tk 主執行緒更新。"""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("SpotifySurface 免 Token 歌詞")
        self.root.geometry("620x330")
        self.root.configure(bg="#161616")
        self.root.attributes("-topmost", True)
        self.events: queue.Queue = queue.Queue()
        self.stopEvent = threading.Event()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self.track: dict[str, Any] | None = None
        self.trackKey: tuple[str, str, str] | None = None
        self.clock = PlaybackClock()
        self.lines: list[tuple[float, str]] = []
        self.timestamps: list[float] = []
        self.title = tk.Label(self.root, text="請在 Spotify 桌面版播放歌曲", fg="#1ed760", bg="#161616", font=("Microsoft JhengHei", 15), wraplength=590)
        self.title.pack(pady=15)
        self.status = tk.Label(self.root, text="正在連接目前已登入的 Spotify…", fg="#aaaaaa", bg="#161616")
        self.status.pack()
        self.lyricFont = tkFont.Font(family="Microsoft JhengHei", size=40, weight="bold")
        self.current = tk.Label(self.root, text="等待播放", fg="white", bg="#161616", font=self.lyricFont)
        self.offset = tk.DoubleVar(value=0)
        tk.Scale(self.root, from_=-5, to=5, resolution=0.1, orient="horizontal", variable=self.offset,
                 label="字幕時間微調（秒）", bg="#161616", fg="white", highlightthickness=0).pack(side="bottom", fill="x", padx=20)
        self.current.pack(fill="both", expand=True, padx=15, pady=10)
        self.current.bind("<Configure>", self.fitLyricFont)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        threading.Thread(target=self.runMonitor, daemon=True).start()
        self.root.after(100, self.update)

    def runMonitor(self) -> None:
        """背景執行媒體監聽。"""
        asyncio.run(monitor(self.events, self.stopEvent))

    def fitLyricFont(self, event: Any = None) -> None:
        """依可用寬高找出能完整容納單行歌詞的最大字體。"""
        text = self.current.cget("text") or "♪"
        width = max(1, self.current.winfo_width() - 12)
        height = max(1, self.current.winfo_height() - 12)
        low, high = 1, 300
        while low < high:
            size = (low + high + 1) // 2
            self.lyricFont.configure(size=size)
            if self.lyricFont.measure(text) <= width and self.lyricFont.metrics("linespace") <= height:
                low = size
            else:
                high = size - 1
        self.lyricFont.configure(size=low)

    def showLyric(self, text: str) -> None:
        """只有歌詞改變才重算字體，減少不必要的版面更新。"""
        if text != self.current.cget("text"):
            self.current.config(text=text)
            self.fitLyricFont()

    def loadLyrics(self, key: tuple[str, str, str], track: dict[str, Any]) -> None:
        """回傳歌曲識別碼，避免快速切歌時舊結果覆蓋新歌。"""
        try:
            self.events.put(("lyrics", (key, fetchLyrics(track))))
        except (requests.RequestException, ValueError):
            self.events.put(("lyrics", (key, {"error": True})))

    def update(self) -> None:
        """處理狀態並依播放時間選取目前歌詞。"""
        while not self.events.empty():
            event, data = self.events.get_nowait()
            if event == "error":
                self.status.config(text=data)
            elif event == "track":
                self.track = data
                if data is None:
                    self.status.config(text="等待 Spotify 桌面版播放歌曲")
                    continue
                key = (data["title"], data["artist"], data["album"])
                self.clock.accept(data, reset=key != self.trackKey)
                if key != self.trackKey:
                    self.trackKey = key
                    self.lines, self.timestamps = [], []
                    self.title.config(text=f'{data["title"]} · {data["artist"]}')
                    self.status.config(text="正在查詢歌詞…")
                    self.showLyric("載入中…")
                    self.executor.submit(self.loadLyrics, key, dict(data))
            elif event == "lyrics":
                key, body = data
                if key != self.trackKey:
                    continue
                self.lines = parseLyrics(body.get("syncedLyrics") or "")
                self.timestamps = [line[0] for line in self.lines]
                if self.lines:
                    self.status.config(text="同步歌詞 · LRCLIB")
                else:
                    message = "歌詞服務連線失敗，請切歌後重試" if body.get("error") else "此歌曲暫無同步歌詞"
                    self.status.config(text=message)
                    plain = body.get("plainLyrics") or ("純音樂" if body.get("instrumental") else "找不到可用歌詞")
                    self.showLyric(plain.splitlines()[0] if plain.splitlines() else "找不到可用歌詞")
        if self.track and self.lines:
            position = self.clock.currentPosition(time.monotonic())
            index = bisect.bisect_right(self.timestamps, position + self.offset.get()) - 1
            self.showLyric((self.lines[index][1] or "♪") if index >= 0 else "♪")
        self.root.after(100, self.update)

    def close(self) -> None:
        """停止背景監聽後關閉視窗。"""
        self.stopEvent.set()
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.root.destroy()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    LyricsWindow().root.mainloop()
