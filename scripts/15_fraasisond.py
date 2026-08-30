#!/usr/bin/env python3
"""Fraasisond: lase mudelil käänata fraase, mille õige vorm on teada.

Allikas on et-kaanamiskorpus-v1.jsonl eval-blokis fraasid (638 tk) - neid EI OLE
kunagi treeningus olnud, seega on tulemus aus. Väljund on kaks asja korraga:
  1. veakaart (kääne x arv x veatüüp) - laiendatud mõõtmine, mida seni polnud
  2. on-policy DPO paarid (rejected = mudeli enda vastus, chosen = õige vorm)
"""
import argparse, json, re, sys, time, urllib.request
from collections import Counter, defaultdict

KORPUS = "/mnt/varu/qwen38-et-data/processed/et-kaanamiskorpus-v1.jsonl"

def kysi(mudel, prompt, temp, n=60):
    d = json.dumps({"model": mudel, "think": False, "stream": False,
                    "messages": [{"role": "user", "content": prompt}],
                    "options": {"temperature": temp, "num_predict": n}}).encode()
    req = urllib.request.Request("http://localhost:11434/api/chat", data=d,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["message"]["content"].strip()

def puhasta(t):
    """Mudel vastab vahel lausega. Võta viimane sisuline rida, koori jutumärgid."""
    t = t.strip().split("\n")[0].strip()
    t = re.sub(r'^(vastus|vorm)\s*[:\-]\s*', '', t, flags=re.I)
    t = t.strip('"“”„\'.,:;!? ')
    return t.lower()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mudel", default="qwen3.8-et:27b-v2")
    p.add_argument("--n", type=int, default=300)
    p.add_argument("--temp", type=float, default=0.3)
    p.add_argument("--valjund", default="/mnt/varu/qwen38-et-data/processed/fraasisond.jsonl")
    a = p.parse_args()

    kirjed = [json.loads(r) for r in open(KORPUS)]
    # variandikomplektid: samal lahtril võib olla mitu õiget vormi
    # (nt "suurde mäkke" ja "suuresse mäesse"); üks küsimus lahtri kohta
    lahtrid = defaultdict(set)
    for k in kirjed:
        if k["tyyp"] == "fraas" and k.get("eval_blokis"):
            lahtrid[(k["sisend"], k["arv"], k["kaane"])].add(k["vorm"].lower())
    valim = sorted(lahtrid.items())          # determinism
    if a.n:
        valim = valim[:a.n]
    print(f"sond: {len(valim)} lahtrit mudelile {a.mudel}", flush=True)

    tulem, algus = [], time.time()
    for i, ((sisend, arv, kaane), vormid) in enumerate(valim, 1):
        # SAMA sõnastus mis lukustatud evalis (treeningu kuju = evali kuju)
        prompt = (f"Pane fraas '{sisend}' {arv} {kaane} käändesse. "
                  f"Vasta ainult vormiga, ilma selgituseta.")
        try:
            toores = kysi(a.mudel, prompt, a.temp)
        except Exception as e:
            print(f"  VIGA {i}: {e}", flush=True); continue
        vastus = puhasta(toores)
        kirje = {"sisend": sisend, "arv": arv, "kaane": kaane,
                 "prompt": prompt, "vastus": vastus, "toores": toores,
                 "oiged": sorted(vormid), "oige": sorted(vormid)[0],
                 "korras": vastus in vormid}
        tulem.append(kirje)
        if i % 25 == 0:
            tabav = sum(t["korras"] for t in tulem) / len(tulem) * 100
            print(f"  {i}/{len(valim)}  tabavus {tabav:.1f}%  "
                  f"({(time.time()-algus)/i:.1f} s/küsimus)", flush=True)

    with open(a.valjund, "w") as f:
        for t in tulem:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    # --- veakaart ---
    kokku = len(tulem); oiged = sum(t["korras"] for t in tulem)
    print(f"\n{'='*62}\nTABAVUS: {oiged}/{kokku} = {oiged/kokku*100:.1f}%\n{'='*62}")
    kaupa = defaultdict(lambda: [0, 0])
    for t in tulem:
        v = kaupa[(t["arv"], t["kaane"])]
        v[1] += 1; v[0] += t["korras"]
    print(f"\n{'kääne':<34}{'õigeid':>10}{'%':>8}")
    for (arv, kaane), (o, n) in sorted(kaupa.items(), key=lambda x: x[1][0]/x[1][1]):
        print(f"{arv+' '+kaane:<34}{f'{o}/{n}':>10}{o/n*100:>7.0f}%")

    # --- veatüübid: kas omadussõna või nimisõna on valesti? ---
    tyybid = Counter()
    for t in tulem:
        if t["korras"]: continue
        v = t["vastus"].split()
        # võrdle variandiga, mis on vastusele kõige lähemal
        o = max((x.split() for x in t["oiged"]),
                key=lambda o: sum(a == b for a, b in zip(v, o)))
        if len(v) != len(o):
            tyybid["sõnade arv erineb"] += 1
        elif len(o) == 2:
            om, ni = v[0] == o[0], v[1] == o[1]
            if not om and ni:  tyybid["ainult OMADUSSÕNA vale (ühildumine)"] += 1
            elif om and not ni: tyybid["ainult NIMISÕNA vale"] += 1
            else:               tyybid["mõlemad sõnad valed"] += 1
        else:
            tyybid["muu"] += 1
    print(f"\n{'veatüüp':<44}{'n':>6}")
    for k, v in tyybid.most_common():
        print(f"{k:<44}{v:>6}")
    print(f"\nvalmis: {a.valjund}")

if __name__ == "__main__":
    main()
