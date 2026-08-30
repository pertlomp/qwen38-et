#!/usr/bin/env python3
"""Jooksutab evali mudeli vastu ja salvestab MUUTMATA vastused.

Kasutus:
  python 07_eval.py --run baseline                    # kogu eval
  python 07_eval.py --run test --limit 20             # kiire tehniline kontroll
  python 07_eval.py --run cpt-10m --model qwen3.8-et:27b-v1

Salvestab eval/runs/<run_id>/: vastused.jsonl + konfiguratsioon.json.
Inferentsiseaded on FIKSEERITUD — enne/pärast võrdlus nõuab identseid seadeid.
"""
import argparse, json, os, platform, subprocess, time, urllib.request

EVAL_TEE = "/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/eval"
# LUKUSTATUD inferentsiseaded — ära muuda ilma uue run_id-ta
SEADED = {"temperature": 0.3, "top_p": 0.9, "top_k": 40, "seed": 20260822,
          "num_predict": 800, "num_ctx": 8192}
SYSTEM = "Sa oled abivalmis assistent. Vasta eesti keeles, kui kasutaja kirjutab eesti keeles."

def kysi(mudel, prompt, think=False):
    keha = {"model": mudel, "prompt": prompt, "system": SYSTEM, "stream": False,
            "think": think, "options": SEADED}
    req = urllib.request.Request("http://localhost:11434/api/generate",
                                 data=json.dumps(keha).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    r = json.loads(urllib.request.urlopen(req, timeout=900).read())
    return {"vastus": r.get("response", ""), "thinking": r.get("thinking", ""),
            "latents_s": round(time.time() - t0, 2),
            "eval_count": r.get("eval_count"), "prompt_eval_count": r.get("prompt_eval_count")}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="run_id, nt baseline")
    ap.add_argument("--model", default="qwen3.8:27b")
    ap.add_argument("--eval", default=f"{EVAL_TEE}/et_locked_v1_draft.jsonl")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--think", action="store_true")
    a = ap.parse_args()

    kirjed = [json.loads(r) for r in open(a.eval, encoding="utf-8") if r.strip()]
    if a.limit: kirjed = kirjed[:a.limit]

    vd = f"{EVAL_TEE}/runs/{a.run}"
    os.makedirs(vd, exist_ok=True)

    # Mudeli täpne identiteet — ilma selleta pole jooks korratav
    try:
        info = subprocess.run(["ollama", "show", a.model], capture_output=True,
                              text=True, timeout=60).stdout
    except Exception:
        info = "(ollama show ebaõnnestus)"

    with open(f"{vd}/konfiguratsioon.json", "w", encoding="utf-8") as f:
        json.dump({"run_id": a.run, "mudel": a.model, "eval_fail": a.eval,
                   "ulesandeid": len(kirjed), "seaded": SEADED, "system": SYSTEM,
                   "think": a.think, "mudeli_info": info,
                   "platvorm": platform.platform()}, f, ensure_ascii=False, indent=1)

    tulemused = []
    t_algus = time.time()
    for i, k in enumerate(kirjed, 1):
        try:
            v = kysi(a.model, k["prompt"], think=a.think)
        except Exception as e:
            v = {"vastus": "", "viga": f"{type(e).__name__}: {str(e)[:200]}", "latents_s": None}
        tulemused.append({**k, **v})
        if i % 10 == 0 or i == len(kirjed):
            m = (time.time() - t_algus) / 60
            print(f"{i}/{len(kirjed)}  ({m:.1f} min)", flush=True)

    with open(f"{vd}/vastused.jsonl", "w", encoding="utf-8") as f:
        for t in tulemused:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    tyhjad = sum(1 for t in tulemused if not t.get("vastus", "").strip())
    vead = sum(1 for t in tulemused if t.get("viga"))
    kesk = sum(t["latents_s"] for t in tulemused if t.get("latents_s")) / max(len(tulemused), 1)
    print(f"\nVALMIS → {vd}/vastused.jsonl")
    print(f"tühje vastuseid: {tyhjad} | vigu: {vead} | keskmine latents: {kesk:.1f} s")
    if tyhjad:
        print("HOIATUS: tühjad vastused — kontrolli think-režiimi ja num_predict'i.")

if __name__ == "__main__":
    main()
