#!/usr/bin/env python3
"""Ring 8: järelvigade täpsparandus + stabiilsuskordus eelmistest moodulitest."""
import json, random

P = "/mnt/varu/qwen38-et-data/processed"
random.seed(20260829)

def loe(tee):
    return [json.loads(r) for r in open(tee)]

siht = (loe(f"{P}/ring8_moodulid.jsonl") + loe(f"{P}/fraas_gen_r8.jsonl")
        + loe(f"{P}/sft_fraasiparandused_ring7.jsonl"))
# stabiilsuskordus: 25% eelmiste ringide moodulitest (flippide vastu)
r6 = random.sample(loe(f"{P}/ring6_moodulid.jsonl"), 250)
r7 = random.sample(loe(f"{P}/ring7_moodulid.jsonl"), 150)
siht += r6 + r7
replay = [d for d in loe(f"{P}/sft_v1_ring4.jsonl")
          if d.get("kategooria", "").startswith("replay")]
replay = random.sample(replay, min(round(len(siht) / 0.82 * 0.18), len(replay)))
koik = siht + replay
random.shuffle(koik)
with open(f"{P}/sft_v1_ring8.jsonl", "w") as f:
    for d in koik:
        f.write(json.dumps({"messages": d["messages"]}, ensure_ascii=False) + "\n")
print(f"RING 8: {len(koik)} näidet ({len(siht)} sihitud, sh {len(r6)+len(r7)} "
      f"stabiilsuskordust + {len(replay)} replay)")
