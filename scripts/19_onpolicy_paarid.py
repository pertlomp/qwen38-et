#!/usr/bin/env python3
"""On-policy DPO paaride korjaja: genereeri värskeid fraase, lase mudelil
vastata, Vabamorf kontrollib — vead muutuvad DPO paarideks.

Nõukoja 2 üksmeelne retsept: rejected peab olema mudeli ENDA usutav viga,
mitte kunstlik halb näide. See skript skaleerib seda piiramatult, sest
generaator teab õiget vastust (variandikomplektina) ja mudel vastab ise.

Käivita AINULT siis, kui GPU on vaba (Ollama laadib mudeli).
"""
import argparse, json, random, re, urllib.request
from collections import Counter
from estnltk.vabamorf.morf import Vabamorf, synthesize

_VM = Vabamorf.instance()
SEEME = 20260826

KOOD = {"nimetav": "n", "omastav": "g", "osastav": "p", "sisseütlev": "ill",
        "seesütlev": "in", "seestütlev": "el", "alaleütlev": "all",
        "alalütlev": "ad", "alaltütlev": "abl", "saav": "tr", "rajav": "ter",
        "olev": "es", "ilmaütlev": "ab", "kaasaütlev": "kom"}
OMASTAVSED = {"rajav", "olev", "ilmaütlev", "kaasaütlev"}
# ring5-sondi veakaart: nõrgim mitmuse omastav/sisseütlev 76%
KAALUD = {("mitmuse", "omastav"): 4, ("mitmuse", "sisseütlev"): 4,
          ("ainsuse", "sisseütlev"): 3, ("mitmuse", "osastav"): 3,
          ("ainsuse", "omastav"): 2, ("ainsuse", "osastav"): 2,
          ("mitmuse", "nimetav"): 2}

def kaandumatu(om):
    if om.endswith(("nud", "tud", "dud")):
        return True
    return om in {"täis", "valmis", "eri", "kogu", "tänu", "vaba", "katki",
                  "lahti", "kinni", "eht", "väärt", "loid"}

def ring_kontroll(vorm, lemma, liik):
    try:
        a = _VM.analyze(words=[vorm], guess=False, propername=False)
        return any(x["lemma"].replace("_", "") == lemma
                   for x in a[0]["analysis"] if x["partofspeech"] == liik)
    except Exception:
        return False

def kysi(mudel, prompt, temp=0.4):
    d = json.dumps({"model": mudel, "think": False, "stream": False,
                    "messages": [{"role": "user", "content": prompt}],
                    "options": {"temperature": temp, "num_predict": 60}}).encode()
    req = urllib.request.Request("http://localhost:11434/api/chat", data=d,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["message"]["content"].strip()

def puhasta(t):
    t = t.strip().split("\n")[0].strip()
    t = re.sub(r'^(vastus|vorm)\s*[:\-]\s*', '', t, flags=re.I)
    return t.strip('"“”„\'.,:;!? ').lower()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mudel", default="qwen3.8-et:27b-v3")
    p.add_argument("--n", type=int, default=1500)
    p.add_argument("--valjund",
                   default="/mnt/varu/qwen38-et-data/processed/dpo_onpolicy_r5.jsonl")
    a = p.parse_args()
    random.seed(SEEME)

    oms, nims = set(), set()
    for r in open("/mnt/varu/qwen38-et-data/processed/morf_gen.jsonl"):
        d = json.loads(r)
        if d["sonaliik"] == "A" and not kaandumatu(d["lemma"]) and d["lemma"].isalpha():
            oms.add(d["lemma"])
        elif d["sonaliik"] == "S" and d["lemma"].isalpha() and "_" not in d["lemma"]:
            nims.add(d["lemma"])
    oms, nims = sorted(oms), sorted(nims)

    blokk = set()
    for r in open("/mnt/varu/qwen38-et-data/processed/et-kaanamiskorpus-v1.jsonl"):
        d = json.loads(r)
        if d.get("eval_blokis"):
            blokk.add(d["sisend"]); blokk.update(d["sisend"].split())

    lahtrid = list(KAALUD)
    kaalud = [KAALUD[l] for l in lahtrid]

    paarid, oigeid, katsed, nahtud = [], 0, 0, set()
    while (len(paarid) + oigeid) < a.n and katsed < a.n * 30:
        katsed += 1
        om, ni = random.choice(oms), random.choice(nims)
        if om in blokk or ni in blokk:
            continue
        arv, kaane = random.choices(lahtrid, weights=kaalud, k=1)[0]
        if (om, ni, arv, kaane) in nahtud:
            continue
        vm_arv = "sg" if arv == "ainsuse" else "pl"
        kd = KOOD[kaane]
        om_kd = "g" if kaane in OMASTAVSED else kd
        A = synthesize(om, f"{vm_arv} {om_kd}", "A")
        B = synthesize(ni, f"{vm_arv} {kd}", "S")
        if not A or not B:
            continue
        if not (ring_kontroll(A[-1], om, "A") and ring_kontroll(B[-1], ni, "S")):
            continue
        nahtud.add((om, ni, arv, kaane))
        variandid = {f"{x} {y}" for x in A for y in B}
        prompt = (f"Pane fraas '{om} {ni}' {arv} {kaane} käändesse. "
                  f"Vasta ainult vormiga, ilma selgituseta.")
        try:
            vastus = puhasta(kysi(a.mudel, prompt))
        except Exception as e:
            print(f"  VIGA: {e}", flush=True); continue
        if vastus in variandid:
            oigeid += 1
        elif vastus:
            paarid.append({"prompt": prompt, "chosen": f"{A[-1]} {B[-1]}",
                           "rejected": vastus, "arv": arv, "kaane": kaane,
                           "allikas": f"onpolicy-{a.mudel}"})
        if (len(paarid) + oigeid) % 100 == 0 and (len(paarid) + oigeid):
            print(f"  {len(paarid)+oigeid}/{a.n}: {len(paarid)} viga "
                  f"({len(paarid)/(len(paarid)+oigeid)*100:.0f}%)", flush=True)

    with open(a.valjund, "w") as f:
        for t in paarid:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    kokku = len(paarid) + oigeid
    print(f"\nvalmis: {kokku} fraasi, {len(paarid)} DPO paari "
          f"(veamäär {len(paarid)/kokku*100:.1f}%) → {a.valjund}")
    for (arv, kaane), n in Counter((t["arv"], t["kaane"]) for t in paarid).most_common():
        print(f"  {arv} {kaane:<14}{n:>5}")

if __name__ == "__main__":
    main()
