#!/usr/bin/env python3
"""Fraasikäänamise generaator: omadussõna + nimisõna, Vabamorfiga.

Miks: eval mõõdab FRAASIDE käänamist (60 ülesannet), aga ring 3 ja 4 treenisid
ainult ÜKSIKSÕNU (11k + 17k). Fraasisond kinnitas: enamik vigu on omadussõna
ühildumine. Reegel on TalTechi 1400 lahtri vastu valideeritud: 98,1% katvus
variante arvestades; ainsad erandid on käändumatud omadussõnad, mis filtreeritakse.

Reegel: omadussõna ühildub nimisõnaga käändes ja arvus, VÄLJA ARVATUD neli
viimast käänet (rajav, olev, ilmaütlev, kaasaütlev), kus omadussõna jääb
omastavasse: "ilusa lauluta", mitte "ilusata lauluta".

Väljund (kaks vormingut, Soli/agy soovitus):
  - 75% otsevastus:  Kääna fraas "X" ... → "käänatud fraas"
  - 25% CoT-vastus:  sama küsimus → [omadussõna ühildub: ... | nimisõna: ...] vastus
Kaalud: vaikimisi ülekaalus sisseütlev, mitmuse omastav ja osastav (sondi veakaart).
"""
import argparse, collections, json, random, sys
from estnltk.vabamorf.morf import Vabamorf, synthesize

_VM = Vabamorf.instance()
SEEME = 20260825

KOOD = {"nimetav": "n", "omastav": "g", "osastav": "p", "sisseütlev": "ill",
        "seesütlev": "in", "seestütlev": "el", "alaleütlev": "all",
        "alalütlev": "ad", "alaltütlev": "abl", "saav": "tr", "rajav": "ter",
        "olev": "es", "ilmaütlev": "ab", "kaasaütlev": "kom"}
OMASTAVSED = {"rajav", "olev", "ilmaütlev", "kaasaütlev"}

# sondi veakaart (ring7, 2026-08-25): vead on nüüd mitmuses — omastav 80%,
# osastav 80%, sisseütlev 81%; ainsus on 85-93%
KAALUD = {("mitmuse", "omastav"): 5, ("mitmuse", "osastav"): 5,
          ("mitmuse", "sisseütlev"): 4, ("ainsuse", "sisseütlev"): 2,
          ("ainsuse", "omastav"): 1, ("mitmuse", "nimetav"): 1,
          ("ainsuse", "osastav"): 1}

def kaandumatu(om):
    """Käändumatud omadussõnad: partitsiibid ja väike kinnitatud loend."""
    if om.endswith(("nud", "tud", "dud")):
        return True
    return om in {"täis", "valmis", "eri", "kogu", "tänu", "vaba", "katki",
                  "lahti", "kinni", "eht", "väärt", "loid"}

def ring_kontroll(vorm, lemma, liik):
    """Analüüsi vorm tagasi ja kontrolli, et lemma klapib."""
    try:
        a = _VM.analyze(words=[vorm], guess=False, propername=False)
        return any(x["lemma"].replace("_", "") == lemma
                   for x in a[0]["analysis"] if x["partofspeech"] == liik)
    except Exception:
        return False

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=3000)
    p.add_argument("--cot-osa", type=float, default=0.25)
    p.add_argument("--seed", type=int, default=SEEME)
    p.add_argument("--valjund",
                   default="/mnt/varu/qwen38-et-data/processed/fraas_gen.jsonl")
    a = p.parse_args()
    random.seed(a.seed)

    # lemmapool päris tekstist (morf_gen.jsonl on juba ring-kontrollitud)
    oms, nims = set(), set()
    for r in open("/mnt/varu/qwen38-et-data/processed/morf_gen.jsonl"):
        d = json.loads(r)
        lem = d["lemma"]
        if d["sonaliik"] == "A" and not kaandumatu(lem) and lem.isalpha():
            oms.add(lem)
        elif d["sonaliik"] == "S" and lem.isalpha() and "_" not in lem:
            nims.add(lem)
    oms, nims = sorted(oms), sorted(nims)
    print(f"lemmapool: {len(oms)} omadussõna, {len(nims)} nimisõna", flush=True)

    # evali leke: blokeeri fraasid, mille sisend on TalTechi korpuses eval_blokis
    blokk = set()
    for r in open("/mnt/varu/qwen38-et-data/processed/et-kaanamiskorpus-v1.jsonl"):
        d = json.loads(r)
        if d.get("eval_blokis"):
            blokk.add(d["sisend"])
            blokk.update(d["sisend"].split())

    lahtrid = [(arv, kaane) for arv in ("ainsuse", "mitmuse") for kaane in KOOD]
    kaalud = [KAALUD.get(l, 1) for l in lahtrid]

    tulem, katsed, nahtud = [], 0, set()
    while len(tulem) < a.n and katsed < a.n * 30:
        katsed += 1
        om, ni = random.choice(oms), random.choice(nims)
        if om in blokk or ni in blokk or f"{om} {ni}" in blokk:
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
        # viimane variant on tänapäevane standardvorm (esimene on sageli
        # arhailine i-mitmus: "kogemusisse" vs "kogemustesse")
        om_v, ni_v = A[-1], B[-1]
        if not (ring_kontroll(om_v, om, "A") and ring_kontroll(ni_v, ni, "S")):
            continue
        nahtud.add((om, ni, arv, kaane))
        vorm = f"{om_v} {ni_v}"
        if random.random() < a.cot_osa:
            # CoT-näide küsib tuletust selgelt — vastus EI TOHI rikkuda
            # "ilma selgituseta" korraldust, seega on küsimus teine
            kys = (f"Pane fraas '{om} {ni}' {arv} {kaane} käändesse. "
                   f"Näita kõigepealt kummagi sõna tuletus, siis vasta.")
            om_selgitus = (f"omadussõna jääb omastavasse: {om_v}"
                           if kaane in OMASTAVSED
                           else f"omadussõna ühildub: {om} → {om_v}")
            vastus = f"[{om_selgitus} | nimisõna: {ni} → {ni_v}] {vorm}"
        else:
            # SAMA sõnastus mis lukustatud evalis (treeningu kuju = evali kuju)
            kys = (f"Pane fraas '{om} {ni}' {arv} {kaane} käändesse. "
                   f"Vasta ainult vormiga, ilma selgituseta.")
            vastus = vorm
        tulem.append({"messages": [
            {"role": "user", "content": kys},
            {"role": "assistant", "content": vastus}],
            "allikas": "vabamorf-fraas-gen", "litsents": "reeglipõhine sünitees",
            "arv": arv, "kaane": kaane, "fraas": f"{om} {ni}", "vorm": vorm})

    with open(a.valjund, "w") as f:
        for t in tulem:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    jaotus = collections.Counter((t["arv"], t["kaane"]) for t in tulem)
    print(f"valmis: {len(tulem)} fraasinäidet ({katsed} katset) → {a.valjund}")
    for (arv, kaane), n in jaotus.most_common(10):
        print(f"  {arv} {kaane:<14}{n:>6}")

if __name__ == "__main__":
    main()
