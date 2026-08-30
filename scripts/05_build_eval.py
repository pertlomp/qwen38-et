#!/usr/bin/env python3
"""Ehitab lukustatud evali: 90 käsitsi + 110 TalTechi andmetest genereeritud.

Genereeritud osal on kontrollitav õige vastus (inflection_et annab õige vormi,
grammar_et annab õige paranduse). Fikseeritud seeme → korratav.

Väljund:
  eval/et_locked_v1_draft.jsonl   — eval ise
  eval/leke_blokk.json            — kirjed, mis EI TOHI SFT-sse sattuda
  eval/et_locked_v1_draft.sha256  — hash (lukustamisel fikseeritakse)
"""
import hashlib, json, os, random

RAW = "/mnt/varu/qwen38-et-data/raw/taltech"
EVAL = "/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/eval"
SEEME = 20260822
random.seed(SEEME)

kirjed, leke = [], {"inflection_et": [], "grammar_et": [], "grammar2_et": []}

# ---- 1. Käsitsi kirjutatud ----
with open(f"{EVAL}/kasitsi_promptid.jsonl", encoding="utf-8") as f:
    for rida in f:
        rida = rida.strip()
        if rida:
            kirjed.append(json.loads(rida))
print(f"käsitsi: {len(kirjed)}")

# ---- 2. Käänamine (inflection_et) → 60 ülesannet ----
read = []
with open(f"{RAW}/inflection_et/word_inflections_hf.jsonl", encoding="utf-8") as f:
    for rida in f:
        try: d = json.loads(rida)
        except: continue
        if d.get("noun_phrase") and d.get("inflection") and d.get("case"):
            read.append(d)
valim = random.sample(read, 60)
for i, d in enumerate(valim, 1):
    arv = d.get("plurality", "ainsuse")
    kirjed.append({
        "id": f"inf-{i:03d}", "kategooria": "kaanamine", "tyyp": "kontrollitav",
        "prompt": f"Pane fraas '{d['noun_phrase']}' {arv} {d['case']} käändesse. "
                  f"Vasta ainult vormiga, ilma selgituseta.",
        "oige_vastus": "; ".join(d["inflection"]),
        "markus": "TalTechNLP/inflection_et; kontrollib ka omadussõna ühildumist"})
    leke["inflection_et"].append(d["noun_phrase"])
print(f"+ käänamine: 60")

# ---- 3. Grammatikaparandus (grammar_et L2 + grammar2_et L1) → 50 ----
def loe_paarid(tee):
    v = []
    if not os.path.exists(tee): return v
    with open(tee, encoding="utf-8") as f:
        for rida in f:
            try: d = json.loads(rida)
            except: continue
            o, c = d.get("original"), d.get("correct")
            if o and c and o != c and 20 < len(o) < 300:
                v.append((o, c))
    return v

l2 = loe_paarid(f"{RAW}/grammar_et/grammar_l2_test.jsonl")
l1 = loe_paarid(f"{RAW}/grammar2_et/grammar_l1.jsonl")
val_l2 = random.sample(l2, min(30, len(l2)))
val_l1 = random.sample(l1, min(20, len(l1)))
for i, (o, c) in enumerate(val_l2 + val_l1, 1):
    allikas = "grammar_et" if i <= len(val_l2) else "grammar2_et"
    kirjed.append({
        "id": f"gec-{i:03d}", "kategooria": "grammatikaparandus", "tyyp": "kontrollitav",
        "prompt": f"Paranda selle lause keelevead. Vasta ainult parandatud lausega, "
                  f"ilma selgituseta:\n\n{o}",
        "oige_vastus": c,
        "markus": f"TalTechNLP/{allikas}"})
    leke[allikas].append(o)
print(f"+ grammatikaparandus: {len(val_l2) + len(val_l1)}")

# ---- Kirjuta välja ----
os.makedirs(EVAL, exist_ok=True)
tee = f"{EVAL}/et_locked_v1_draft.jsonl"
with open(tee, "w", encoding="utf-8") as f:
    for k in kirjed:
        f.write(json.dumps(k, ensure_ascii=False) + "\n")
with open(f"{EVAL}/leke_blokk.json", "w", encoding="utf-8") as f:
    json.dump(leke, f, ensure_ascii=False, indent=1)

h = hashlib.sha256(open(tee, "rb").read()).hexdigest()
with open(f"{EVAL}/et_locked_v1_draft.sha256", "w") as f:
    f.write(f"{h}  et_locked_v1_draft.jsonl\n")

kat = {}
for k in kirjed:
    kat[k["kategooria"]] = kat.get(k["kategooria"], 0) + 1
print(f"\nKOKKU {len(kirjed)} ülesannet")
print(f"kontrollitava vastusega: {sum(1 for k in kirjed if k['tyyp']=='kontrollitav')}")
print(f"rubriigi järgi hinnatavad: {sum(1 for k in kirjed if k['tyyp']=='rubriik')}")
print("\nKategooriad:")
for k, v in sorted(kat.items(), key=lambda x: -x[1]):
    print(f"  {k:26} {v:3}")
print(f"\nSHA-256: {h}")
print(f"Seeme: {SEEME} (korratav)")
