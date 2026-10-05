"""驗證重複媒體快照、暫停及使用者拖曳進度。"""
import runpy
import unittest

PlaybackClock = runpy.run_path("spotify-surface-local.py")["PlaybackClock"]


def makeTrack(position: float, received: float, updated: float, age: float = 0, playing: bool = True) -> dict:
    """建立可重現 Windows 媒體更新間隔的測試資料。"""
    return {"position": position, "received": received, "updated": updated, "age": age, "playing": playing}


class PlaybackClockTests(unittest.TestCase):
    """確認字幕時鐘不因輪詢而反覆倒退。"""

    def testRepeatedSnapshot(self) -> None:
        """舊快照保持不變時，播放仍應持續推進。"""
        clock = PlaybackClock()
        clock.accept(makeTrack(10, 100, 90))
        clock.accept(makeTrack(10, 100.5, 90, 0.5))
        clock.accept(makeTrack(10, 104, 90, 4))
        self.assertAlmostEqual(clock.currentPosition(104.2), 14.2)

    def testJitterAndSeek(self) -> None:
        """略落後的快照不回跳，真正往前或往後拖曳則重設。"""
        clock = PlaybackClock()
        clock.accept(makeTrack(10, 100, 90))
        clock.accept(makeTrack(10.8, 101, 91))
        self.assertEqual(clock.currentPosition(101), 11)
        clock.accept(makeTrack(40, 102, 92))
        self.assertEqual(clock.currentPosition(102), 40)
        clock.accept(makeTrack(5, 103, 93))
        self.assertEqual(clock.currentPosition(103), 5)

    def testPauseResumeAndReset(self) -> None:
        """暫停不推進，恢復播放及切歌重新建立錨點。"""
        clock = PlaybackClock()
        clock.accept(makeTrack(10, 100, 90, 2))
        self.assertEqual(clock.currentPosition(100), 12)
        clock.accept(makeTrack(13, 101, 91, playing=False))
        self.assertEqual(clock.currentPosition(110), 13)
        clock.accept(makeTrack(13, 110, 100))
        self.assertEqual(clock.currentPosition(111), 14)
        clock.accept(makeTrack(0, 112, 102), reset=True)
        self.assertEqual(clock.currentPosition(112), 0)


if __name__ == "__main__":
    unittest.main()
