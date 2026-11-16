"""Chatterbox-Multilingual-Worker (läuft in .venv-tts, MIT-Lizenz, lokal auf der CPU).

Liest eine JSON-Liste von Aufträgen von stdin:
  [{"text": "...", "out": "/pfad.wav", "ref": "/ref.wav", "exaggeration": 0.5, "cfg": 0.5,
    "temperature": 0.8, "seed": 1}]
und schreibt pro fertiger Datei eine JSON-Zeile nach stdout.
"""
import json
import sys
import time
import warnings

warnings.filterwarnings("ignore")


def main():
    jobs = json.load(sys.stdin)
    import torch
    import torchaudio as ta
    torch.set_num_threads(4)
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    for j in jobs:
        t = time.time()
        torch.manual_seed(int(j.get("seed", 1)))
        kw = dict(language_id="de", exaggeration=j.get("exaggeration", 0.5), cfg_weight=j.get("cfg", 0.5),
                  temperature=j.get("temperature", 0.8))
        if j.get("ref"):
            kw["audio_prompt_path"] = j["ref"]
        wav = model.generate(j["text"], **kw)
        ta.save(j["out"], wav, model.sr)
        print(json.dumps({"out": j["out"], "seconds": round(time.time() - t, 1),
                          "dur": round(wav.shape[-1] / model.sr, 2)}), flush=True)


if __name__ == "__main__":
    main()
