#!/usr/bin/env python3
"""Ehitab DPO-korpuse (eelistuspaarid) kolmest kihist.

Kiht 1 — GEC (olemas): inimese vigane lause = rejected, toimetaja parandus = chosen.
Kiht 2 — stiilipaarid (Sol + agy genereeritud): AI-kohmakas = rejected, loomulik = chosen.
Kiht 3 — mudeli enda vead (tekib hiljem): meie mudeli väljund = rejected, toimetatud = chosen.

Väljund on MUDELISÕLTUMATU: puhas {prompt, chosen, rejected} + metaandmed.
Chat-mall rakendatakse alles treeningu ajal, nii et korpus sobib igale mudelile.

Kasutus:
  python 13_build_dpo.py                 # ehitab kihid 1-2 sellest, mis olemas
  python 13_build_dpo.py --lisa-stiil X  # liidab uue stiilipaaride faili juurde
"""
import argparse, glob, hashlib, json, os, random

RAW = "/mnt/varu/qwen38-et-data/raw"
PROC = "/mnt/varu/qwen38-et-data/processed"
EVAL = "/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/eval"
VALJUND = f"{PROC}/dpo_korpus.jsonl"
SEEME = 20260824
random.seed(SEEME)

ap = argparse.ArgumentParser()
ap.add_argument("--lisa-stiil", action="append", default=[],
                help="JSONL fail väljadega prompt/chosen/rejected (Sol, agy vms)")
a = ap.parse_args()

# --- Eval-lekke blokk: evalis kasutatud laused EI TOHI DPO-sse sattuda ---
leke = json.load(open(f"{EVAL}/leke_blokk.json", encoding="utf-8"))
LEKE = {x.strip().lower() for x in
        (leke.get("grammar_et", []) + leke.get("grammar2_et", []) + leke.get("inflection_et", []))}
evalp = {json.loads(r)["prompt"].lower() for r in open(f"{EVAL}/et_locked_v1.jsonl", encoding="utf-8")}

paarid, nahtud = [], set()

def lisa(prompt, chosen, rejected, kiht, allikas, litsents="puhas", markus=None):
    if not (prompt and chosen and rejected): return False
    if str(chosen).strip() == str(rejected).strip(): return False
    if str(prompt).lower() in evalp: return False
    v = hashlib.md5(f"{prompt}|{chosen}|{rejected}".encode()).hexdigest()
    if v in nahtud: return False
    nahtud.add(v)
    kirje = {"prompt": str(prompt).strip(), "chosen": str(chosen).strip(),
             "rejected": str(rejected).strip(), "kiht": kiht,
             "allikas": allikas, "litsents": litsents}
    if markus: kirje["markus"] = markus
    paarid.append(kirje)
    return True

# ---------- KIHT 1: GEC — päris inimeste vead ----------
JUHISED = [
    "Paranda selle teksti keelevead. Vasta ainult parandatud tekstiga:",
    "Toimeta see lause korrektseks eesti keeleks. Vasta ainult tulemusega:",
    "Kirjuta see lause õigesse eesti keelde:",
]
n1 = 0
for tee, nimi in [(f"{RAW}/taltech/grammar_et/grammar_l2_train.jsonl", "grammar_et"),
                  (f"{RAW}/taltech/grammar_et/grammar_l2_test.jsonl", "grammar_et"),
                  (f"{RAW}/taltech/grammar2_et/grammar_l1.jsonl", "grammar2_et")]:
    if not os.path.exists(tee): continue
    for r in open(tee, encoding="utf-8"):
        try: d = json.loads(r)
        except Exception: continue
        o, c = d.get("original"), d.get("correct")
        if not (o and c) or o == c: continue
        if o.strip().lower() in LEKE: continue          # eval-lekke blokk
        if not (20 < len(o) < 600): continue
        juhis = JUHISED[n1 % len(JUHISED)]
        if lisa(f"{juhis}\n\n{o}", c, o, "gec", f"TalTechNLP/{nimi}",
                "kontrollimata", "rejected = inimese algne vigane lause"):
            n1 += 1
print(f"kiht 1 (GEC, päris vead): {n1}")

# ---------- KIHT 2: stiilipaarid välistest failidest ----------
n2 = 0
for f in a.lisa_stiil:
    if not os.path.exists(f):
        print(f"  ! puudub: {f}"); continue
    allikas = os.path.basename(f).replace(".jsonl", "")
    for rida in open(f, encoding="utf-8", errors="replace"):
        rida = rida.strip().strip("`")
        if not rida.startswith("{"): continue
        try: d = json.loads(rida)
        except Exception: continue
        if lisa(d.get("prompt"), d.get("chosen"), d.get("rejected"), "stiil",
                allikas, "hall-genereeritud", d.get("markus")):
            n2 += 1
print(f"kiht 2 (stiil, genereeritud): {n2}")

# ---------- Väljund ----------
random.shuffle(paarid)
os.makedirs(PROC, exist_ok=True)
with open(VALJUND, "w", encoding="utf-8") as f:
    for p in paarid:
        f.write(json.dumps(p, ensure_ascii=False) + "\n")

h = hashlib.sha256(open(VALJUND, "rb").read()).hexdigest()
kihid, lits = {}, {}
for p in paarid:
    kihid[p["kiht"]] = kihid.get(p["kiht"], 0) + 1
    lits[p["litsents"]] = lits.get(p["litsents"], 0) + 1
manifest = {
    "nimi": "et-dpo-korpus-v1", "kirjeid": len(paarid), "sha256": h,
    "koostatud": "2026-08-24", "seeme": SEEME,
    "kihid": kihid, "litsentsid": lits,
    "vorming": "mudelisõltumatu: {prompt, chosen, rejected}; chat-mall rakendatakse treeningul",
    "eval_lekke_blokk": f"{len(LEKE)} lauset/fraasi välistatud",
    "koostaja": {"nimi": "Pert Lomp", "aasta": 2026,
                 "panus": "korpuse koosseis, kihtide loogika, lekkeblokk, litsentsimärgistus"},
    "hoiatused": [
        "GEC-kiht: TalTechi litsents on kontrollimata — enne avaldamist küsi.",
        "Stiilikiht: LLM-genereeritud, ToS-hall — avaldamisel teadusklausel.",
        "Kiht 3 (mudeli enda vead) tuleb lisada pärast lõpliku mudeli valmimist.",
    ],
}
with open(f"{PROC}/dpo_korpus_manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)
print(f"\nDPO KORPUS: {len(paarid)} paari → {VALJUND}")
print(f"kihid: {json.dumps(kihid, ensure_ascii=False)} | litsentsid: {json.dumps(lits, ensure_ascii=False)}")
print(f"SHA-256: {h}")
