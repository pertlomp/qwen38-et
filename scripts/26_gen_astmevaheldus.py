#!/usr/bin/env python3
"""Astmevahelduslike omadussõnade fraasid — ring 9 põhiannus.

Ring7 evali KÕIK 7 käänamisviga olid omadussõna tüvevaheldus:
  kurb → kurbade (mudel: "kurjade"), puhas → puhtaid (mudel: "puhaseid"),
  rikas → rikkad (mudel: "rikas"), õnnelik → õnnelikusse (mudel: "õndsasse"),
  kange → kangete (mudel jättis käänamata).

Kureeritud raskete omadussõnade loend (astmevaheldus, -as/-s tüved, erandid) +
Vabamorfi süntees + ring-kontroll. Kaal mitmuse omastav/osastav/nimetav peale,
sest just seal tüvi muutub (kurbade, puhtaid, rikkad).
"""
import argparse, collections, json, random
from estnltk.vabamorf.morf import Vabamorf, synthesize

_VM = Vabamorf.instance()
SEEME = 20260831

# rasked omadussõnad: astmevaheldus, tüvemuutus, -as/-s lõpp, lühikesed erandid
RASKED = ["kurb", "puhas", "rikas", "vaene", "armas", "kallis", "kitsas",
    "pikk", "tark", "halb", "soe", "pime", "sile", "kindel", "õnnelik",
    "ohtlik", "edukas", "arukas", "eakas", "maitsev", "vilets", "kaunis",
    "aus", "paks", "sügav", "madal", "kõva", "märg", "kuiv", "julm",
    "kerge", "raske", "kange", "lahke", "väike", "hea", "paha", "uus",
    "vana", "noor", "suur", "hall", "must", "valge", "punane", "roheline",
    "lühike", "õhuke", "jäme", "lai", "kõrge", "sale", "terav", "nüri",
    "hapu", "magus", "mõru", "soolane", "värske", "toores", "küps"]

KOOD = {"nimetav": "n", "omastav": "g", "osastav": "p", "sisseütlev": "ill",
        "seesütlev": "in", "seestütlev": "el", "alaleütlev": "all",
        "alalütlev": "ad", "alaltütlev": "abl", "saav": "tr", "rajav": "ter",
        "olev": "es", "ilmaütlev": "ab", "kaasaütlev": "kom"}
OMASTAVSED = {"rajav", "olev", "ilmaütlev", "kaasaütlev"}
# tüvevaheldus paistab kõige rohkem mitmuses ja osastavas
KAALUD = {("mitmuse", "omastav"): 5, ("mitmuse", "osastav"): 5,
          ("mitmuse", "nimetav"): 4, ("ainsuse", "osastav"): 3,
          ("mitmuse", "sisseütlev"): 3, ("ainsuse", "sisseütlev"): 2,
          ("ainsuse", "omastav"): 2}

def ring_kontroll(vorm, lemma, liik):
    try:
        a = _VM.analyze(words=[vorm], guess=False, propername=False)
        return any(x["lemma"].replace("_", "") == lemma
                   for x in a[0]["analysis"] if x["partofspeech"] == liik)
    except Exception:
        return False

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=800)
    p.add_argument("--seed", type=int, default=SEEME)
    p.add_argument("--valjund",
                   default="/mnt/varu/qwen38-et-data/processed/fraas_astmevaheldus.jsonl")
    a = p.parse_args()
    random.seed(a.seed)

    import re
    blokk = set()
    for r in open("/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/eval/et_locked_v1.jsonl"):
        d = json.loads(r)
        if d.get("kategooria") == "kaanamine":
            # blokeeri evali FRAASID (mitte üksiksõnad — "kurb" üksi on lubatud,
            # sest me ei treeni evali fraasi "kurb sõna", vaid teisi paare)
            m = re.search(r"'([^']+)'", d.get("prompt", ""))
            if m:
                blokk.add(m.group(1).lower())

    nims = sorted({json.loads(r)["lemma"] for r in
                   open("/mnt/varu/qwen38-et-data/processed/morf_gen.jsonl")
                   if json.loads(r)["sonaliik"] == "S"
                   and json.loads(r)["lemma"].isalpha()})
    lahtrid = list(KAALUD)
    kaalud = [KAALUD[l] for l in lahtrid]

    tulem, katsed, nahtud = [], 0, set()
    while len(tulem) < a.n and katsed < a.n * 40:
        katsed += 1
        om, ni = random.choice(RASKED), random.choice(nims)
        if f"{om} {ni}" in blokk:
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
        om_v, ni_v = A[-1], B[-1]
        if not (ring_kontroll(om_v, om, "A") and ring_kontroll(ni_v, ni, "S")):
            continue
        nahtud.add((om, ni, arv, kaane))
        vorm = f"{om_v} {ni_v}"
        if random.random() < 0.3:
            # CoT rõhutab TÜVE muutust — see ongi viga, mida ravime
            kys = (f"Pane fraas '{om} {ni}' {arv} {kaane} käändesse. "
                   f"Näita kõigepealt omadussõna tüvi, siis vasta.")
            vastus = (f"[omadussõna tüvi muutub: {om} → {om_v} | "
                      f"nimisõna: {ni} → {ni_v}] {vorm}")
        else:
            kys = (f"Pane fraas '{om} {ni}' {arv} {kaane} käändesse. "
                   f"Vasta ainult vormiga, ilma selgituseta.")
            vastus = vorm
        tulem.append({"messages": [{"role": "user", "content": kys},
                                   {"role": "assistant", "content": vastus}],
                      "allikas": "vabamorf-astmevaheldus",
                      "litsents": "reeglipõhine süntees",
                      "arv": arv, "kaane": kaane, "omadussona": om})

    with open(a.valjund, "w") as f:
        for t in tulem:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(f"valmis: {len(tulem)} fraasi → {a.valjund}")
    for om, n in collections.Counter(t["omadussona"] for t in tulem).most_common(8):
        print(f"  {om:<12}{n:>4}")

if __name__ == "__main__":
    main()
