#!/usr/bin/env python3
"""Ring 6: viis kirurgilist moodulit dpo3 vigade peale + fraaside jätk.

Koostis:
  - 1402 moodulinäidet (20_gen_ring6.py: olemasolu, verbimorf, JSON, tehniline,
    arvliitsõnad — kõik dpo3 evali PÄRIS vigade tüüpidest)
  - 500 värsket fraasi (16_gen_fraasid.py, uus seeme 20260827)
  - 62 dpo3-sondi veaparandust
  - 18% replay (ring 4 inglise + kood, uus deterministlik valim)
"""
import json, random

P = "/mnt/varu/qwen38-et-data/processed"
random.seed(20260827)

def loe(tee):
    return [json.loads(r) for r in open(tee)]

siht = (loe(f"{P}/ring6_moodulid.jsonl") + loe(f"{P}/fraas_gen_r6.jsonl")
        + loe(f"{P}/sft_fraasiparandused_dpo3.jsonl"))

replay = [d for d in loe(f"{P}/sft_v1_ring4.jsonl")
          if d.get("kategooria", "").startswith("replay")]
n_replay = round(len(siht) / 0.82 * 0.18)
replay = random.sample(replay, min(n_replay, len(replay)))

koik = siht + replay
random.shuffle(koik)

valjund = f"{P}/sft_v1_ring6.jsonl"
with open(valjund, "w") as f:
    for d in koik:
        f.write(json.dumps({"messages": d["messages"]}, ensure_ascii=False) + "\n")

print(f"RING 6: {len(koik)} näidet ({len(siht)} sihitud + {len(replay)} replay "
      f"= {len(replay)/len(koik)*100:.1f}%) → {valjund}")
