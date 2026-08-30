#!/usr/bin/env python3
"""Ring 7: kuju-täpne mikroannus (610 moodulit + 60 ring6-sondi parandust + replay)."""
import json, random

P = "/mnt/varu/qwen38-et-data/processed"
random.seed(20260828)

def loe(tee):
    return [json.loads(r) for r in open(tee)]

siht = loe(f"{P}/ring7_moodulid.jsonl") + loe(f"{P}/sft_fraasiparandused_ring6.jsonl")
replay = [d for d in loe(f"{P}/sft_v1_ring4.jsonl")
          if d.get("kategooria", "").startswith("replay")]
replay = random.sample(replay, min(round(len(siht) / 0.82 * 0.18), len(replay)))
koik = siht + replay
random.shuffle(koik)
with open(f"{P}/sft_v1_ring7.jsonl", "w") as f:
    for d in koik:
        f.write(json.dumps({"messages": d["messages"]}, ensure_ascii=False) + "\n")
print(f"RING 7: {len(koik)} näidet ({len(siht)} sihitud + {len(replay)} replay)")
