# Legiscrape - Legistar Meetings / Granicus Video Toolbox

## Note

This is software is alpha quality.  This is a first step in allowing
constiuents to have full access to data currently locked up in
their city's Legistar systems.

I'm building it for Oakland with the intention that it can be used
in other cities with minimal modification.

## What can it do now?

* Download video and remux into valid MP4
* Download using multiple connections (2-4x speed up)
* Manipulate proprietary JSON captions
  * Create plaintext transcript
  * Generate standard format captions (SRT and WEBVTT)
  * Extract Chapter Metadata
* Combine audio, video, chapters, captions into a single clean MP4

## Usage:

Prerequisites:
* [Python 3.x](https://www.python.org/downloads/) (Tested with 3.6.0)
* `brew install ffmpeg mp4box aria2c`

````
pip3 install legiscrape
legiscrape-video 20170314_PublicSafetyCommittee.mp4 "http://oakland.granicus.com/MediaPlayer.php?view_id=2&clip_id=2225"
````

## Why?

Legistar and Granicus video are sucky systems.

In my first week trying to report on an Oakland City Council meeting
I ran into a number of issues which drove me insane:

1. Chrome/Firefox/Safari don't if you don't have flash. Period.
2. MP4 video files aren't always valid MP4 files.
If VLC can't play it back, good luck seeking, keeping voice sync or
using a less forgiving player.
3. No ability to link to timestamp in a video (ala YouTube
t=15m32s)
4. Captions are in a closed format (and not included in MP4 download)
5. Underprovisioned servers so playback/download isn't reliable.
6. No permalinks. Agenda's from 2010 link to servers which don't exist.
7. It's all a closed system.

## Who

Built by Peter Tripp in Oakland.

* github.com/notpeter
* twitter.com/notpeter
