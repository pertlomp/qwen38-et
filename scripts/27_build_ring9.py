#!/usr/bin/env python3
"""Ring 9: astmevaheldus-fookus + stabiilsus, ILMA tehniliseta (Perti otsus)."""
import json, random

P = "/mnt/varu/qwen38-et-data/processed"
random.seed(20260901)

def loe(tee):
    return [json.loads(r) for r in open(tee)]

siht = loe(f"{P}/fraas_astmevaheldus.jsonl") + loe(f"{P}/sft_fraasiparandused_ring8.jsonl")
# stabiilsus: eelmiste ringide moodulid ILMA tehniliseta
stab = [d for d in (loe(f"{P}/ring6_moodulid.jsonl") + loe(f"{P}/ring7_moodulid.jsonl")
                    + loe(f"{P}/ring8_moodulid.jsonl"))
        if d.get("kategooria") != "tehniline"]
stab = random.sample(stab, 400)
siht += stab
replay = [d for d in loe(f"{P}/sft_v1_ring4.jsonl")
          if d.get("kategooria", "").startswith("replay")]
replay = random.sample(replay, min(round(len(siht) / 0.82 * 0.18), len(replay)))
koik = siht + replay
random.shuffle(koik)
with open(f"{P}/sft_v1_ring9.jsonl", "w") as f:
    for d in koik:
        f.write(json.dumps({"messages": d["messages"]}, ensure_ascii=False) + "\n")
print(f"RING 9: {len(koik)} näidet ({len(siht)} sihitud, sh {len(stab)} stabiilsust "
      f"+ {len(replay)} replay)")
