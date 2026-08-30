#!/usr/bin/env python3
"""Paki CPT-korpus käsitsi ~2000-tokenisteks tükkideks.

Miks: TRL packing=True ei rakendunud multimodaalse protsessoriga (mõõdetud:
78045 sammu = 1,25M lõiku / 16, s.t iga lõik eraldi polsterdatud näitena,
6,5 päeva). Faili tasandil pakkimine on deterministlik ja treener-sõltumatu.
~8000 tähemärki ≈ 2000 tokenit (eesti ~2,4 tok/sõna, ~4 tähte/sõna).
"""
import json

SISSE = "/mnt/varu/qwen38-et-data/processed/cpt_korpus.jsonl"
VALJA = "/mnt/varu/qwen38-et-data/processed/cpt_korpus_pakitud.jsonl"
SIHT = 8000   # tähemärki tüki kohta

puhver, pikkus, n = [], 0, 0
with open(VALJA, "w") as f:
    for r in open(SISSE):
        t = json.loads(r)["text"]
        puhver.append(t)
        pikkus += len(t) + 2
        if pikkus >= SIHT:
            f.write(json.dumps({"text": "\n\n".join(puhver)},
                               ensure_ascii=False) + "\n")
            n += 1
            puhver, pikkus = [], 0
    if puhver:
        f.write(json.dumps({"text": "\n\n".join(puhver)}, ensure_ascii=False) + "\n")
        n += 1
print(f"pakitud: {n} tükki → {VALJA}")
