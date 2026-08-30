#!/usr/bin/env python3
"""Liidab välise mudeli vastused (JSONL {"id","vastus"}) lukustatud evaliga
ja kirjutab runs/<run_id>/vastused.jsonl, mida 08_score.py oskab skoorida.

Kasutus: python 11_liida_valised.py --run claude-fable --vastused /tee/vastused.jsonl
Talub mürarida (mitte-JSON read jäetakse vahele) ja raporteerib puuduvad id-d.
"""
import argparse, json, os, re

EVAL = "/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/eval"

ap = argparse.ArgumentParser()
ap.add_argument("--run", required=True)
ap.add_argument("--vastused", required=True)
a = ap.parse_args()

kirjed = {json.loads(r)["id"]: json.loads(r)
          for r in open(f"{EVAL}/et_locked_v1.jsonl", encoding="utf-8") if r.strip()}

vastused = {}
for rida in open(a.vastused, encoding="utf-8", errors="replace"):
    rida = rida.strip().strip("`")
    if not rida or rida in ("json", "jsonl"): continue
    # mõni CLI mähib koodiplokki või lisab prefiksi — otsi JSON-objekt realt
    m = re.search(r"\{.*\}", rida)
    if not m: continue
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        continue
    if isinstance(d, dict) and d.get("id") and "vastus" in d:
        vastused[d["id"]] = str(d["vastus"])

vd = f"{EVAL}/runs/{a.run}"
os.makedirs(vd, exist_ok=True)
puudu = []
with open(f"{vd}/vastused.jsonl", "w", encoding="utf-8") as f:
    for kid, k in kirjed.items():
        v = vastused.get(kid)
        if v is None:
            puudu.append(kid)
            v = ""                      # tühi = 0 punkti, aus karistus puudumise eest
        f.write(json.dumps({**k, "vastus": v}, ensure_ascii=False) + "\n")

with open(f"{vd}/konfiguratsioon.json", "w", encoding="utf-8") as f:
    json.dump({"run": a.run, "allikas": a.vastused, "vastuseid": len(vastused),
               "puudu": puudu, "markus": "väline mudel, vastas ilma õigeid vastuseid nägemata"},
              f, ensure_ascii=False, indent=1)

print(f"{a.run}: {len(vastused)} vastust, {len(puudu)} puudu → {vd}/vastused.jsonl")
if puudu:
    print("puuduvad:", ", ".join(puudu[:15]), "…" if len(puudu) > 15 else "")
