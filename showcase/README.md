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
