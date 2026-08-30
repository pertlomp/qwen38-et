#!/usr/bin/env python3
"""Ring 13: koondkorpuse stiiliannus + stabiilsus + replay."""
import json, random

P = "/mnt/varu/qwen38-et-data/processed"
random.seed(20260828)

def loe(tee):
    return [json.loads(r) for r in open(tee)]

siht = loe(f"{P}/ring13_stiil.jsonl")
# stabiilsus: oskused (astmevaheldus, ring10/12 moodulid) + ring12 head osad
stab = random.sample(
    loe(f"{P}/fraas_astmevaheldus.jsonl") + loe(f"{P}/ring10_moodulid.jsonl")
    + loe(f"{P}/ring12_moodulid.jsonl") + loe(f"{P}/ring8_moodulid.jsonl"), 450)
siht += stab
replay = [d for d in loe(f"{P}/sft_v1_ring4.jsonl")
          if d.get("kategooria", "").startswith("replay")]
replay = random.sample(replay, min(round(len(siht) / 0.85 * 0.15), len(replay)))
koik = siht + replay
random.shuffle(koik)
with open(f"{P}/sft_v1_ring13.jsonl", "w") as f:
    for d in koik:
        f.write(json.dumps({"messages": d["messages"]}, ensure_ascii=False) + "\n")
print(f"RING 13: {len(koik)} näidet ({len(siht)} sihitud, sh {len(stab)} "
      f"stabiilsust + {len(replay)} replay)")
