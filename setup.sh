#!/usr/bin/env bash
# Installiert alle lokalen Open-Source-Werkzeuge des Studios (idempotent).
set -euo pipefail
cd "$(dirname "$0")"

python3 -m pip install --quiet piper-tts pycairo faster-whisper opencv-python-headless numpy pillow requests

# Comic-Schriften (SIL Open Font License, aus dem Google-Fonts-Repository)
mkdir -p assets/fonts ~/.fonts
for f in bangers/Bangers-Regular.ttf comicneue/ComicNeue-Bold.ttf; do
  [ -s "assets/fonts/$(basename $f)" ] || curl -sSL -o "assets/fonts/$(basename $f)" "https://raw.githubusercontent.com/google/fonts/main/ofl/$f"
done
cp assets/fonts/*.ttf ~/.fonts/ && fc-cache -f >/dev/null

# Deutsche Piper-Stimmen (MIT/CC-Lizenzen laut rhasspy/piper-voices)
mkdir -p assets/voices
B=https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE
for v in thorsten/medium/de_DE-thorsten-medium thorsten_emotional/medium/de_DE-thorsten_emotional-medium \
         eva_k/x_low/de_DE-eva_k-x_low kerstin/low/de_DE-kerstin-low ramona/low/de_DE-ramona-low \
         karlsson/low/de_DE-karlsson-low mls/medium/de_DE-mls-medium; do
  n=$(basename $v)
  [ -s "assets/voices/$n.onnx" ] || { curl -sSL -o "assets/voices/$n.onnx" "$B/$v.onnx"; curl -sSL -o "assets/voices/$n.onnx.json" "$B/$v.onnx.json"; }
done

# Hauptstimmen: Chatterbox Multilingual (Resemble AI, MIT-Lizenz) in eigener Umgebung, CPU-Version von PyTorch
if [ ! -x .venv-tts/bin/python ] || ! .venv-tts/bin/python -c "import chatterbox" 2>/dev/null; then
  python3 -m venv .venv-tts
  .venv-tts/bin/pip install --quiet --upgrade pip
  .venv-tts/bin/pip install --quiet torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu
  .venv-tts/bin/pip install --quiet chatterbox-tts
fi

# Hauptstimmen: ZONOS3-Mini (Zyphra, Apache-2.0) – C++/ggml-Server für die CPU, Stimmklon + Emotions-Regler
Z=vendor/ZONOS3-Mini
if [ ! -x $Z/servers/ggml/build/zonos3-server ]; then
  [ -d $Z ] || git clone -q --depth 1 https://github.com/Zyphra/ZONOS3-Mini.git $Z
  (cd $Z && git submodule update --init --depth 1 servers/ggml/ggml third_party/zyphra-textnorm)
  (cd $Z/servers/ggml && cmake -B build -DCMAKE_BUILD_TYPE=Release >/dev/null && cmake --build build -j"$(nproc)" >/dev/null)
fi
mkdir -p $Z/servers/ggml/gguf
for f in backbone-ptq.gguf zac-keep2.gguf spk-encoder.gguf steer.gguf; do
  [ -s "$Z/servers/ggml/gguf/$f" ] || curl -sSL --fail -o "$Z/servers/ggml/gguf/$f" "https://huggingface.co/Zyphra/ZONOS3-Mini/resolve/main/gguf/$f"
done

# Whisper-Modell für die Sprach-QC (wird beim ersten Aufruf geladen)
python3 -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8', download_root='assets/whisper')" 2>/dev/null

python3 -m studio check
