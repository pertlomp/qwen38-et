#!/usr/bin/env python3
"""Ring 10: viimased augud + DEGENERATSIOONI RAVI.

Uus element: 600 avatud vastust (saatevestlus-qa + sõnatähendus ring3 poolist)
— mitte oskuse, vaid VABA GENEREERIMISE kaitseks. Ring9 näitas drilli-kahju:
"liiteosaga liiteosaga...", "tervisandur". Drillid õpetavad lühivastust;
avatud materjal hoiab lausegeneraatori elus.
"""
import json, random

P = "/mnt/varu/qwen38-et-data/processed"
random.seed(20260902)

def loe(tee):
    return [json.loads(r) for r in open(tee)]

siht = loe(f"{P}/ring10_moodulid.jsonl") + loe(f"{P}/sft_fraasiparandused_ring9.jsonl")

r3 = loe(f"{P}/sft_v1_ring3.jsonl")
avatud = [d for d in r3 if d.get("kategooria") in ("saatevestlus-qa", "sonatahendus")]
avatud = random.sample(avatud, 600)
toor = [d for d in loe(f"{P}/sft_v1_ring4.jsonl") if d.get("kategooria") == "tooriistad"]
toor = random.sample(toor, 150)
stab = [d for d in (loe(f"{P}/ring8_moodulid.jsonl") + loe(f"{P}/fraas_astmevaheldus.jsonl"))
        ]
stab = random.sample(stab, 250)
siht += avatud + toor + stab

replay = [d for d in loe(f"{P}/sft_v1_ring4.jsonl")
          if d.get("kategooria", "").startswith("replay")]
replay = random.sample(replay, min(round(len(siht) / 0.85 * 0.15), len(replay)))
koik = siht + replay
random.shuffle(koik)
with open(f"{P}/sft_v1_ring10.jsonl", "w") as f:
    for d in koik:
        f.write(json.dumps({"messages": d["messages"]}, ensure_ascii=False) + "\n")
print(f"RING 10: {len(koik)} näidet ({len(siht)} sihitud, sh {len(avatud)} avatud "
      f"+ {len(toor)} tööriista + {len(stab)} stabiilsust; {len(replay)} replay)")
