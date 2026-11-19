"""python -m larp <befehl>

  render <video-id|datei.json> [--workers 4] [--audio datei] [--audio-offset s]
  still  <video-id> <sekunde> [ausgabe.png]      Einzelbild zum Prüfen
  list                                          vorhandene Video-Spezifikationen
"""
import argparse
import sys

from . import render as R


def main(argv=None):
    ap = argparse.ArgumentParser(prog="larp", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd")
    ap.add_argument("args", nargs="*")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--audio")
    ap.add_argument("--audio-offset", type=float, default=0.0)
    a = ap.parse_args(argv)
    if a.cmd == "render":
        out, dur = R.render(a.args[0], a.workers, a.audio, a.audio_offset)
        print(f"fertig: {out} ({dur:.1f} s)")
    elif a.cmd == "still":
        out = a.args[2] if len(a.args) > 2 else f"still_{a.args[1]}.png"
        R.still(a.args[0], float(a.args[1]), out)
        print(out)
    elif a.cmd == "list":
        for p in sorted((R.CHANNEL / "videos").glob("*.json")):
            print(p.stem)
    else:
        ap.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
