#!/usr/bin/env python3
"""SFT-kombo: ringide 5-13 sihitud materjali parim koond ÜHE annusena.

Mõte: CPT-haru saab sama õpetuse, mille rank16-rada sai 9 ringiga — aga ühe
2-tunnise treeninguga. Ainult SIHITUD materjal (ballasti reegel), dedup,
<nooutput>-filter, 15% replay.
"""
import json, random

P = "/mnt/varu/qwen38-et-data/processed"
random.seed(20260828)

def loe(tee, max_n=None):
    try:
        read = [json.loads(r) for r in open(tee)]
    except FileNotFoundError:
        print(f"  puudub: {tee}")
        return []
    if max_n and len(read) > max_n:
        read = random.sample(read, max_n)
    return read

OSAD = [
    ("fraas_gen.jsonl", None),            # 3000 fraasikäänamist
    ("fraas_gen_r6.jsonl", None),         # 500
    ("fraas_gen_r8.jsonl", None),         # 400
    ("fraas_astmevaheldus.jsonl", None),  # 800
    ("sft_fraasiparandused.jsonl", None),
    ("sft_fraasiparandused_r5.jsonl", None),
    ("sft_fraasiparandused_ring6.jsonl", None),
    ("sft_fraasiparandused_ring7.jsonl", None),
    ("sft_fraasiparandused_ring8.jsonl", None),
    ("sft_fraasiparandused_ring9.jsonl", None),
    ("ring6_moodulid.jsonl", None),       # 1402
    ("ring7_moodulid.jsonl", None),       # 610
    ("ring8_moodulid.jsonl", None),       # 272
    ("ring10_moodulid.jsonl", None),      # 148
    ("ring12_moodulid.jsonl", None),      # 515
    ("ring11_vestlus.jsonl", None),       # 1214 (pikk-vastus, gec-kysitud jt)
    ("ring13_stiil.jsonl", None),         # 1160 koondkorpuse stiil
]

siht, nahtud = [], set()
for fail, max_n in OSAD:
    for d in loe(f"{P}/{fail}", max_n):
        k = d["messages"][0]["content"]
        v = d["messages"][-1]["content"]
        if k in nahtud or "nooutput" in v.lower():
            continue
        # ring11 kaja-mall VÄLJA (teadaolev disainiviga)
        if d.get("kategooria") == "vestlus-mitte-gec":
            continue
        nahtud.add(k)
        siht.append(d)

# ring4 sihitud varad: tööriistad, JSON, meta, grammatika
r4 = loe(f"{P}/sft_v1_ring4.jsonl")
for d in r4:
    kat = d.get("kategooria", "")
    if kat in ("tooriistad", "json-struktuur", "morfoloogia-meta"):
        k = d["messages"][0]["content"] if d["messages"][0]["role"] == "user" \
            else d["messages"][1]["content"]
        if k in nahtud:
            continue
        nahtud.add(k)
        siht.append(d)
gram = [d for d in r4 if d.get("kategooria") == "grammatikaparandus"]
siht += random.sample(gram, min(1500, len(gram)))

replay = [d for d in r4 if d.get("kategooria", "").startswith("replay")]
replay = random.sample(replay, min(round(len(siht) / 0.85 * 0.15), len(replay)))
koik = siht + replay
random.shuffle(koik)
with open(f"{P}/sft_kombo.jsonl", "w") as f:
    for d in koik:
        f.write(json.dumps({"messages": d["messages"]}, ensure_ascii=False) + "\n")
print(f"SFT-KOMBO: {len(koik)} näidet ({len(siht)} sihitud + {len(replay)} replay)")
