#!/usr/bin/env bash
# Installiert alle lokalen Open-Source-Werkzeuge des Studios (idempotent).
set -euo pipefail
export HF_HUB_DISABLE_XET=1  # Xet-Server von Hugging Face ist im Netz der Umgebung gesperrt; normale Downloads gehen
cd "$(dirname "$0")"
# Downloads dürfen den Sitzungsstart nie abbrechen: Fehler werden gemeldet, 'studio check' zeigt, was fehlt,
# und die Stimmen fallen automatisch zurück (Qwen3 → ZONOS3 → Piper).
WARN=0
warn() { echo "WARNUNG setup.sh: $*" >&2; WARN=$((WARN + 1)); }
get() { curl -sSL --fail --retry 3 -o "$1.part" "$2" && mv "$1.part" "$1" || { rm -f "$1.part"; warn "Download fehlgeschlagen: $2"; }; }

python3 -m pip install --quiet piper-tts pycairo faster-whisper opencv-python-headless numpy pillow requests cryptography \
  || warn "pip-Installation unvollständig"

# Comic-Schriften (SIL Open Font License, aus dem Google-Fonts-Repository)
mkdir -p assets/fonts ~/.fonts
for f in bangers/Bangers-Regular.ttf comicneue/ComicNeue-Bold.ttf; do
  [ -s "assets/fonts/$(basename $f)" ] || get "assets/fonts/$(basename $f)" "https://raw.githubusercontent.com/google/fonts/main/ofl/$f"
done
cp assets/fonts/*.ttf ~/.fonts/ 2>/dev/null && fc-cache -f >/dev/null || warn "Schriften fehlen"

# Deutsche Piper-Stimmen (MIT/CC-Lizenzen laut rhasspy/piper-voices)
mkdir -p assets/voices
B=https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE
for v in thorsten/medium/de_DE-thorsten-medium thorsten_emotional/medium/de_DE-thorsten_emotional-medium \
         eva_k/x_low/de_DE-eva_k-x_low kerstin/low/de_DE-kerstin-low ramona/low/de_DE-ramona-low \
         karlsson/low/de_DE-karlsson-low mls/medium/de_DE-mls-medium; do
  n=$(basename $v)
  [ -s "assets/voices/$n.onnx" ] || { get "assets/voices/$n.onnx.json" "$B/$v.onnx.json"; get "assets/voices/$n.onnx" "$B/$v.onnx"; }
done

# Rückfall-Stimmen: Chatterbox Multilingual (Resemble AI, MIT) – nur mit STUDIO_CHATTERBOX=1 (spart ~5 Min./Tag)
if [ "${STUDIO_CHATTERBOX:-0}" = "1" ] && { [ ! -x .venv-tts/bin/python ] || ! .venv-tts/bin/python -c "import chatterbox" 2>/dev/null; }; then
  python3 -m venv .venv-tts
  .venv-tts/bin/pip install --quiet --upgrade pip
  .venv-tts/bin/pip install --quiet torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu
  .venv-tts/bin/pip install --quiet chatterbox-tts
fi

# Hauptstimmen: Qwen3-TTS (Alibaba Qwen, Apache-2.0) – eigene Umgebung .venv-qwen, Modell in assets/qwen
if ! .venv-qwen/bin/python -c "import qwen_tts" 2>/dev/null; then
  { python3 -m venv .venv-qwen && .venv-qwen/bin/pip install --quiet --upgrade pip \
    && .venv-qwen/bin/pip install --quiet torch torchaudio --index-url https://download.pytorch.org/whl/cpu \
    && .venv-qwen/bin/pip install --quiet qwen-tts==0.1.1 soundfile; } || warn "Qwen3-TTS nicht installiert"
fi
# Modell (~4,3 GB); abgebrochene Downloads werden fortgesetzt, bis zu 4 Versuche
if [ -x .venv-qwen/bin/python ]; then
  ok=0
  for i in 1 2 3 4; do
    HF_HUB_CACHE=assets/qwen .venv-qwen/bin/python -c \
      "import huggingface_hub as h; h.snapshot_download('Qwen/Qwen3-TTS-12Hz-1.7B-Base')" >/dev/null 2>&1 && { ok=1; break; }
    sleep $((i * 10))
  done
  [ $ok = 1 ] || warn "Qwen3-Modell nicht vollständig geladen (Stimmen fallen auf ZONOS3 zurück)"
fi

# Rückfall-Stimmen: ZONOS3-Mini (Zyphra, Apache-2.0) – C++/ggml-Server für die CPU, Stimmklon + Emotions-Regler
Z=vendor/ZONOS3-Mini
if [ ! -x $Z/servers/ggml/build/zonos3-server ]; then
  { { [ -d $Z ] || git clone -q --depth 1 https://github.com/Zyphra/ZONOS3-Mini.git $Z; } \
    && (cd $Z && git submodule update --init --depth 1 servers/ggml/ggml third_party/zyphra-textnorm) \
    && (cd $Z/servers/ggml && cmake -B build -DCMAKE_BUILD_TYPE=Release >/dev/null && cmake --build build -j"$(nproc)" >/dev/null); } \
    || warn "ZONOS3 nicht gebaut"
fi
mkdir -p $Z/servers/ggml/gguf
for f in backbone-ptq.gguf zac-keep2.gguf spk-encoder.gguf steer.gguf; do
  [ -s "$Z/servers/ggml/gguf/$f" ] || get "$Z/servers/ggml/gguf/$f" "https://huggingface.co/Zyphra/ZONOS3-Mini/resolve/main/gguf/$f"
done

# Whisper-Modell für die Sprach-QC (wird beim ersten Aufruf geladen)
python3 -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8', download_root='assets/whisper')" 2>/dev/null \
  || warn "Whisper-Modell nicht geladen"

python3 -m studio check || warn "Systemprüfung meldet fehlende Teile (siehe oben)"
[ "$WARN" = 0 ] || echo "setup.sh: fertig mit $WARN Warnung(en) – Sitzung startet trotzdem."
