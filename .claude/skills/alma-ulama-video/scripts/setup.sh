#!/bin/bash
# One-time setup for a fresh container. Idempotent.
set -e
command -v ffmpeg >/dev/null || { apt-get update -qq && apt-get install -y -qq ffmpeg; }
python3 -c "import faster_whisper" 2>/dev/null || pip install -q faster-whisper
python3 -c "from PIL import features; assert features.check('raqm')" 2>/dev/null || pip install -q --upgrade pillow
# The bundled font is passed to libass via fontsdir; also install it for fontconfig as a fallback.
mkdir -p ~/.fonts && cp "$(dirname "$0")/../assets/fonts/"*.ttf ~/.fonts/ && fc-cache -f >/dev/null 2>&1 || true
echo "alma-ulama-video: ready"
