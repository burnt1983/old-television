# Old Television

A small CSS 3D television for the Linux desktop. The cabinet is drawn, not a photograph. The picture sits inside the glass, so it shares the cabinet's perspective. The page background is clear.

Four sets use the same build: Walnut box, Floor console, Portable, and Round tube.

## Install

Needs Python 3, GTK 3, PyGObject, cairo, and WebKitGTK 4.1
(`python3-gi`, `python3-cairo`, `gir1.2-gtk-3.0`, `gir1.2-webkit2-4.1`).

```bash
git clone https://github.com/burnt1983/old-television.git
cd old-television
bash install.sh
old-television
```

The window position is saved in `~/.config/lee-old-television/place.json`. Nothing else is stored. It does not start at login.

## How to use it

The set opens on static. Click the glass for the first channel, and click again for the next one.

| Action | What happens |
|---|---|
| Click the glass | Next channel |
| Click the cabinet | Shows the set buttons |
| Keys 1–4 | Walnut box, Floor console, Portable, Round tube |
| Left / Right | Previous / next channel |
| Up / Down | Volume |
| Escape | Back to static |
| Drag the wood | Moves the window |
| Ctrl+Q | Closes the window |

## Channels

Thirty-three public HLS streams. The first eight are the original dial. A station can go offline. The glass shows "No signal" and the next click moves on.

DW English, Bloomberg, VOA Africa, CGTN, Red Bull TV, France 24, DW Español, DW Arabic, BBC One (London), BBC Two, BBC Four, BBC News, CBBC, CBeebies, BBC Arabic, Pop, Tiny Pop, GREAT! movies, Blaze, Trace UK, talkSPORT, NASA TV, QVC, QVC Beauty, Gemporia, Hobby Maker, TJC, TalkTV, Sky News Weather, CNBC, Al Jazeera Arabic, TRT World, CNA.

These are the broadcasters' own public playlists. Locked channels are not included.

## Uninstall

```bash
bash uninstall.sh
```

## Credits

The page plays HLS with [hls.js](https://github.com/video-dev/hls.js) 1.5.20. The player is included under `vendor/` and joined into `hls.min.js` on install. hls.js is Apache-2.0. See [NOTICE](NOTICE).

## Licence

MIT. See [LICENSE](LICENSE).
