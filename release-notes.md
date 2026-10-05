# SpotifySurface Local v1.0.0

Token-free, single-line lyrics for the already signed-in Spotify desktop app on Windows.

## Highlights

- Reads Spotify playback through Windows media sessions; no Spotify or Musixmatch token required.
- Retrieves lyrics from LRCLIB.
- Shows one current lyric line with a font that automatically fits the window.
- Fixes lyric jumps caused by resetting playback progress on repeated timeline snapshots.
- Provides a manual timing adjustment from -5 to +5 seconds.

## Download and run

Download **SpotifySurface.exe**, open Spotify desktop, play a song, and run the EXE. Python and conda are not required for the packaged app.

Tested on the development Windows 64-bit machine. Synced lyrics depend on LRCLIB coverage; other playback devices and the Spotify web player are not guaranteed to work. The EXE is not digitally signed.

Based on [PureAspiration/SpotifySurface](https://github.com/PureAspiration/SpotifySurface). Original author credit and the MIT license are retained. This is an independent adaptation, not an official upstream release.
