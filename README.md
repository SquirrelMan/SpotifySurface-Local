# SpotifySurface Local

A token-free, always-on-top, single-line lyrics window for the Spotify desktop app on Windows. Follow the lyrics while working or browsing, with text that automatically grows to fit the window.

## Origin and upstream tracking

This project is based on [PureAspiration/SpotifySurface](https://github.com/PureAspiration/SpotifySurface). Credit for the original project goes to **PureAspiration**. The original source, Git history, and MIT license are retained. See [the original README](README-upstream.md).

This is an independent adaptation, not an official upstream release. Upstream changes can be reviewed and merged manually; updates are not synchronized automatically.

## Main use case

Show the current lyric line over other desktop windows while listening to Spotify. The local version connects to the already signed-in Spotify desktop app through Windows media sessions. No Spotify API credentials, Musixmatch token, or additional sign-in is required.

## Changes in this version

| Area | Local version |
| --- | --- |
| Spotify connection | Reads track metadata, playback position, and pause state through Windows media sessions instead of Spotify API tokens. |
| Lyrics provider | Fetches lyrics from [LRCLIB](https://lrclib.net), without a Musixmatch token. |
| Display | Shows only the current lyric line, with the largest font that fits the available width and height. |
| Subtitle jumping | Keeps a playback clock anchored across repeated Windows timeline snapshots, rather than resetting progress on every poll. Small timing corrections are ignored; larger changes follow seeks. |
| Track switching | Associates lyric responses with the requested track so delayed results do not overwrite a different song. |
| Timing adjustment | Provides a manual offset from -5 to +5 seconds. |
| Distribution | Can be packaged as a standalone Windows EXE using PyInstaller. |

The token-free entry point is `spotify-surface-local.py`. The original `main.py` is retained for reference and still requires the original token setup.

## Usage

The settings interface and app status messages are in English. Lyrics remain in their original language.

Download the standalone Windows EXE from the [latest release](https://github.com/SquirrelMan/SpotifySurface-Local/releases/latest).

1. Open Spotify desktop on Windows and play a song.
2. Run `SpotifySurface.exe`.
3. Resize the window to enlarge the lyric text. Adjust the timing slider if the lyrics are consistently early or late.
   Click the small **⋯** button in the upper-right corner to access track information, connection status, timing adjustment, window dimensions, and Quit. **Hold and drag this button to move the overlay.** Dragging visible lyric strokes is also supported; transparent spaces pass mouse input through to the window underneath.

The window stays on top. The default overlay has a transparent background and no title bar, showing only the current lyric and the small settings button. In settings, toggle **Transparent background** to switch between transparency and a solid dark background. With the dark background enabled, the whole lyric area can be dragged. Running the packaged EXE does not require Python or conda.

## Install from source

Tested with 64-bit Windows and Python 3.10. The original dependency versions are retained for compatibility.

```bat
conda create -n spotify_surface python=3.10 pip -y
conda activate spotify_surface
python -m pip install -r requirements-lock.txt
python spotify-surface-local.py
```

## Build the EXE

```bat
python -m PyInstaller --noconfirm --clean --onefile --windowed --name SpotifySurface --collect-all winsdk --icon assets/app-icon.ico --add-data "assets/app-icon.ico;assets" spotify-surface-local.py
```

Output: `dist/SpotifySurface.exe`. The exact installed dependencies are listed in [requirements-lock.txt](requirements-lock.txt).

## Validation

```bat
python test-playback-clock.py
python -m pip check
```

Playback clock tests cover repeated snapshots, small timing errors, forward and backward seeks, pause/resume, and track resets. Spotify media-session access, LRCLIB requests, and EXE startup have been verified on the development machine. Broader Windows compatibility testing has not yet been performed.

## Limitations and privacy

- Synced lyrics depend on LRCLIB coverage. When only plain lyrics are available, the app displays the first line; it does not generate timing information.
- This app does not translate lyrics or transcribe audio.
- Support targets the local Spotify desktop app. Browser playback, phones, and other playback devices are not guaranteed to work.
- Windows timeline updates may be delayed. Different song recordings or lyric timestamps can still cause timing differences.
- Track title, artist, album, and duration are sent to LRCLIB to find lyrics. Spotify account credentials are not read.
- Playback controls from the original app are not included in this simplified local interface.

## Track upstream changes

```bash
git remote add upstream https://github.com/PureAspiration/SpotifySurface.git
git fetch upstream
```

Skip the first command if `upstream` already exists. Review upstream changes before merging them.

## License and acknowledgments

Distributed under the [MIT License](LICENSE.md), retaining the original author's copyright notice.

- Original project: [PureAspiration/SpotifySurface](https://github.com/PureAspiration/SpotifySurface)
- Lyrics service: [LRCLIB](https://lrclib.net)
- Windows media-session Python bindings: `winsdk`
