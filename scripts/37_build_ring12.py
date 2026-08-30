#!/usr/bin/env python3
"""Ring 12: kaja-malli ja pikkuse parandus. KAJA-MALLI näited EI LÄHE kaasa —
ring11 vestlus-mitte-gec visatakse stabiilsusest VÄLJA (see oli disainiviga)."""
import json, random

P = "/mnt/varu/qwen38-et-data/processed"
random.seed(20260904)

def loe(tee):
    return [json.loads(r) for r in open(tee)]

siht = loe(f"{P}/ring12_moodulid.jsonl")
# stabiilsus: ring11 HEAD osad (pikk-vastus, kokkuvõtted, gec-kysitud) + oskused
r11 = [d for d in loe(f"{P}/ring11_vestlus.jsonl")
       if d.get("kategooria") in ("pikk-vastus", "uudise-kokkuvote", "gec-kysitud")]
stab = random.sample(r11, 300) + random.sample(
    loe(f"{P}/fraas_astmevaheldus.jsonl") + loe(f"{P}/ring10_moodulid.jsonl"), 250)
siht += stab
replay = [d for d in loe(f"{P}/sft_v1_ring4.jsonl")
          if d.get("kategooria", "").startswith("replay")]
replay = random.sample(replay, min(round(len(siht) / 0.85 * 0.15), len(replay)))
koik = siht + replay
random.shuffle(koik)
with open(f"{P}/sft_v1_ring12.jsonl", "w") as f:
    for d in koik:
        f.write(json.dumps({"messages": d["messages"]}, ensure_ascii=False) + "\n")
print(f"RING 12: {len(koik)} näidet ({len(siht)} sihitud + {len(replay)} replay)")
