"""Qwen3-TTS-Worker (läuft in .venv-qwen, Apache-2.0, lokal auf der CPU).

Liest eine JSON-Liste von Aufträgen von stdin:
  [{"text": "...", "out": "/pfad.raw.wav", "ref": "/ref.wav", "ref_text": "Abschrift der Referenz", "seed": 1}]
Das Modell lädt nur einmal; Stimmklon-Vorlagen werden je Referenz zwischengespeichert.
Schreibt pro fertiger Datei eine JSON-Zeile nach stdout.
"""
import json
import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
MODEL = os.environ.get("STUDIO_QWEN_MODEL", "Qwen/Qwen3-TTS-12Hz-1.7B-Base")


def main():
    jobs = json.load(sys.stdin)
    import soundfile as sf
    import torch
    from qwen_tts import Qwen3TTSModel
    torch.set_num_threads(os.cpu_count() or 4)
    from huggingface_hub import snapshot_download
    t0 = time.time()
    path = snapshot_download(MODEL, local_files_only=True)  # lokaler Ordner, kein Netz nötig
    model = Qwen3TTSModel.from_pretrained(path, device_map="cpu", dtype=torch.float32)
    print(json.dumps({"geladen": round(time.time() - t0, 1)}), flush=True)
    prompts = {}
    for j in jobs:
        t = time.time()
        key = (j["ref"], j.get("ref_text") or "")
        if key not in prompts:
            prompts[key] = model.create_voice_clone_prompt(ref_audio=j["ref"], ref_text=j.get("ref_text") or None,
                                                           x_vector_only_mode=not j.get("ref_text"))
        torch.manual_seed(int(j.get("seed", 1)))
        wavs, sr = model.generate_voice_clone(text=j["text"], language="German", voice_clone_prompt=prompts[key])
        tmp = j["out"] + ".tmp.wav"
        sf.write(tmp, wavs[0], sr)
        os.replace(tmp, j["out"])
        print(json.dumps({"out": j["out"], "seconds": round(time.time() - t, 1),
                          "dur": round(len(wavs[0]) / sr, 2)}), flush=True)


if __name__ == "__main__":
    main()
