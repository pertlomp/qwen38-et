#!/usr/bin/env python3
"""Väliste testide (MMLU_et, EstQA) patarei suurte mudelite jaoks.

SAMAD deterministlikud valimid mis meie mudelil (seeme 20260825, MMLU 300,
EstQA 200). Kolm sammu:
  --ehita   : kirjuta batch-promptifailid (MMLU 50 küsimust/batch, EstQA 10/batch)
  --skoori M: parsi mudeli M vastusefailid ja arvuta skoor

Vastused kogub bash-jooksutaja (oo_valised.sh): iga batch → CLI → väljund
kataloogi valised/<mudel>/. Vastuseformaat: JSONL {"id": ..., "vastus": ...}.
"""
import argparse, collections, glob, json, os, random, re

import sys
BAAS = "/mnt/varu/qwen38-et-data/valised"
MMLU = "/mnt/varu/qwen38-et-data/raw/taltech/MMLU_et"
ESTQA = "/mnt/varu/qwen38-et-data/raw/taltech/EstQA/data/test-00000-of-00001.parquet"
SEEME = 20260825

def mmlu_valim(n=300):
    random.seed(SEEME)
    koik = []
    for f in sorted(glob.glob(f"{MMLU}/test_*.jsonl")):
        for rida in open(f):
            try:
                d = json.loads(rida)
            except Exception:
                continue
            if d.get("question") and len(d.get("choices", [])) == 4:
                koik.append(d)
    random.shuffle(koik)
    return koik[:n]

def estqa_valim(n=200):
    import pandas as pd
    random.seed(SEEME)
    df = pd.read_parquet(ESTQA)
    idx = list(range(len(df)))
    random.shuffle(idx)
    return [df.iloc[i] for i in idx[:n]]

def ehita():
    os.makedirs(f"{BAAS}/promptid", exist_ok=True)
    m = mmlu_valim()
    for b in range(0, len(m), 25):
        osad = []
        for i, d in enumerate(m[b:b+25], start=b):
            tahed = ["A", "B", "C", "D"]
            valikud = "\n".join(f"{t}) {v}" for t, v in zip(tahed, d["choices"]))
            osad.append(f"### {i}\n{d['question']}\n{valikud}")
        sisu = ("Vasta järgmistele valikvastustega küsimustele. Väljasta AINULT "
                "JSONL-read, iga küsimuse kohta üks rida kujul "
                '{"id": <number>, "vastus": "<A|B|C|D>"}. Ei mingit muud teksti.\n\n'
                + "\n\n".join(osad))
        open(f"{BAAS}/promptid/mmlu-{b//25:02d}.txt", "w").write(sisu)
    q = estqa_valim()
    for b in range(0, len(q), 10):
        osad = []
        for r in q[b:b+10]:
            osad.append(f"### {r['id']}\nTekst: {r['context']}\n"
                        f"Küsimus: {r['question']}")
        sisu = ("Loe iga teksti ja vasta küsimusele LÜHIDALT, täpselt tekstis "
                "esineva fraasiga, ilma selgituseta. Väljasta AINULT JSONL-read "
                'kujul {"id": "<id>", "vastus": "<fraas>"}. Ei mingit muud teksti.\n\n'
                + "\n\n".join(osad))
        open(f"{BAAS}/promptid/estqa-{b//10:02d}.txt", "w").write(sisu)
    print(f"promptid: {len(glob.glob(f'{BAAS}/promptid/*.txt'))} faili → {BAAS}/promptid/")

def loe_vastused(kaust, prefiks):
    v = {}
    for f in sorted(glob.glob(f"{kaust}/{prefiks}-*.out")):
        for rida in open(f, errors="replace"):
            m = re.search(r"\{.*\}", rida)
            if not m:
                continue
            try:
                d = json.loads(m.group(0))
            except Exception:
                continue
            if isinstance(d, dict) and "id" in d and "vastus" in d:
                v[d["id"]] = str(d["vastus"])
    return v

def normi(t):
    t = t.lower().strip()
    t = re.sub(r"[\"'«»„“”.,:;!?()]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def f1(vastus, oige):
    v, o = normi(vastus).split(), normi(oige).split()
    if not v or not o:
        return 0.0
    yhised = sum((collections.Counter(v) & collections.Counter(o)).values())
    if yhised == 0:
        return 0.0
    p, r = yhised / len(v), yhised / len(o)
    return 2 * p * r / (p + r)

def skoori(mudel):
    kaust = f"{BAAS}/{mudel}"
    # MMLU
    m = mmlu_valim()
    v = loe_vastused(kaust, "mmlu")
    oiged = kokku = 0
    for i, d in enumerate(m):
        vast = v.get(i) or v.get(str(i))
        if vast is None:
            continue
        kokku += 1
        ml = re.search(r"[ABCD]", vast.upper())
        if ml and ml.group(0) == ["A", "B", "C", "D"][d["answer"]]:
            oiged += 1
    mmlu_t = oiged / kokku * 100 if kokku else 0
    # EstQA
    q = estqa_valim()
    v2 = loe_vastused(kaust, "estqa")
    f1s, em, n2 = 0.0, 0, 0
    for r in q:
        vast = v2.get(r["id"])
        if vast is None:
            continue
        n2 += 1
        variandid = [x["text"] for x in r["answers"]]
        f1s += max(f1(vast, o) for o in variandid)
        em += any(normi(vast) == normi(o) for o in variandid)
    print(f"{mudel}: MMLU {mmlu_t:.1f}% (n={kokku})  "
          f"EstQA F1 {f1s/n2*100 if n2 else 0:.1f} EM {em/n2*100 if n2 else 0:.1f} (n={n2})")
    json.dump({"mudel": mudel, "mmlu": mmlu_t, "mmlu_n": kokku,
               "estqa_f1": f1s / n2 * 100 if n2 else 0,
               "estqa_em": em / n2 * 100 if n2 else 0, "estqa_n": n2},
              open(f"{kaust}/skoor.json", "w"))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ehita", action="store_true")
    ap.add_argument("--skoori")
    a = ap.parse_args()
    if a.ehita:
        ehita()
    if a.skoori:
        skoori(a.skoori)
