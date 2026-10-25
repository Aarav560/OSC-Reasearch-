# OSC research showreel

`osc-showreel.mp4`: 50 s, 1080×1920 at 30 fps, H.264 + AAC, ready for Shorts.

Every frame comes from code. `reel.html` is a pure function `renderFrame(t)` built from
three.js (the voxel cannon assembling under an orbiting pan camera) and DOM/canvas kinetic
type. `render.js` steps it frame by frame in headless Chromium. `soundtrack.py`
synthesizes the music with numpy. The numbers on screen come from
`paper-tests/lab-results-paper-26.3-214.json`.

The cannon is a stylized voxel model, not a block-accurate schematic.

Rebuild:

    cd showcase && python3 -m http.server 8765 --bind 127.0.0.1 &
    NODE_PATH=$(npm root -g) node render.js /tmp/frames 30 0 50
    python3 soundtrack.py /tmp/soundtrack.wav
    ffmpeg -framerate 30 -i /tmp/frames/f%05d.jpg -i /tmp/soundtrack.wav -c:v libx264 -crf 18 \
      -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart osc-showreel.mp4

# Zephyr Mk1-A live-fire video

`zephyr-livefire.mp4`: 44 s, 1080×1920 at 30 fps. It records the live shot logged by
`paper-tests/mk1a_livefire.py`: 8 TNT, 150 X and 120 Z charges, fired on Paper 26.3 build 214.

- The blocks are meshed from the saved world with real 26.3 textures
  (`build_livefire_scene.py`, `tools/mcmesh.py`, `tools/worldread.py`). The target is shown as
  placed before the shot, then as read back from the world afterwards, crater included.
- The staging, launch timing, stored velocity, per-tick fall and crater come from
  `paper-tests/livefire-8x150x120.json`, extracted to `lf/data.json`.
- The charge sequence (~98 s real) is time-compressed on screen; the HUD shows the speed-up.
  The release is one game tick, drawn out so its X-then-Z path can be followed.

Rebuild (meshes and textures are generated locally, not committed: they contain Mojang assets):

    python3 build_livefire_scene.py <world> <client assets> <blocks.json> \
        ../paper-tests/livefire-8x150x120.json lf
    cp <client assets>/assets/minecraft/textures/block/tnt_{side,top,bottom}.png lf/textures/
    python3 -m http.server 8765 --bind 127.0.0.1 &
    PAGE=livefire.html NODE_PATH=$(npm root -g) node render.js /tmp/lf 30 0 44
    python3 livefire_sound.py /tmp/lf.wav
    ffmpeg -framerate 30 -i /tmp/lf/f%05d.jpg -i /tmp/lf.wav -c:v libx264 -crf 18 -pix_fmt yuv420p \
      -c:a aac -b:a 192k -shortest -movflags +faststart zephyr-livefire.mp4
