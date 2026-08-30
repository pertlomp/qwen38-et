#!/usr/bin/env python3
"""Ring 5: kirurgiline fraasikäänamise annus (nõukoda 2 retsept).

Koostis (PLAAN-RANK16-EDASI reegel: AINULT sihitud materjal + replay):
  - 3000 fraasikäänamist (16_gen_fraasid.py, sondi veakaardi kaaludega)
  - 101 sondi veaparandust (mudeli enda vead, õige vastusega)
  - ~18% replay (inglise + kood, ring 4 samad kirjed — deterministlik valim)

MITTE ballasti: ei saatevestlusi, ei sõnaseletusi (ring 3 õppetund).
"""
import json, random

P = "/mnt/varu/qwen38-et-data/processed"
SEEME = 20260825
random.seed(SEEME)

def loe(tee):
    return [json.loads(r) for r in open(tee)]

fraasid = loe(f"{P}/fraas_gen.jsonl")
parandused = loe(f"{P}/sft_fraasiparandused.jsonl")
siht = fraasid + parandused

# replay ring 4 andmestikust: samad kirjed, mis mudel juba edukalt läbis
replay = [d for d in loe(f"{P}/sft_v1_ring4.jsonl")
          if d.get("kategooria", "").startswith("replay")]
# 18% koguannusest: siht / 0.82 * 0.18
n_replay = round(len(siht) / 0.82 * 0.18)
replay = random.sample(replay, min(n_replay, len(replay)))

koik = siht + replay
random.shuffle(koik)

valjund = f"{P}/sft_v1_ring5.jsonl"
with open(valjund, "w") as f:
    for d in koik:
        f.write(json.dumps({"messages": d["messages"]}, ensure_ascii=False) + "\n")

print(f"RING 5: {len(koik)} näidet ({len(fraasid)} fraasi + {len(parandused)} "
      f"parandust + {len(replay)} replay = {len(replay)/len(koik)*100:.1f}%)")
print(f"→ {valjund}")
