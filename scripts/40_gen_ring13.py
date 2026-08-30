#!/usr/bin/env python3
"""Ring 13: stiiliannus koondkorpusest (UUED ANDMED, Muischnek 2026-08-26).

Mõõdetud sihid, mida see annus ravib:
  1. Vaba registri vead ("sai kutsung", "suurel lavastel") — mudel pole näinud
     toimetatud ilukirjandust. Nüüd on: 4,6M sõna päris eesti proosat.
  2. Pikkuse järgimine (ring12 parandas 300 peale; nüüd mitmekesisem)
  3. Teaduslik register (doktoritööd) — seni katmata.

Kuju: "Jätka teksti samas stiilis, umbes N sõnaga" — algus promptis, päris
jätk vastuses. See õpetab REGISTRIT ja PIKKUST korraga, ilma teemasilte vajamata.
Viitamiskohustus (CC-BY-SA) täidetud andmeregistris ja avaldamisel.
"""
import argparse, collections, json, random, re

SEEME = 20260828
P = "/mnt/varu/qwen38-et-data/processed"

def eval_blokk():
    sonad = set()
    for r in open("/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/eval/et_locked_v1.jsonl"):
        d = json.loads(r)
        sonad.update(re.findall(r"[a-zõäöüšž\-]{5,}",
                     f"{d.get('prompt','')}".lower()))
    return sonad

def lause_piir(tekst, n_lauset=2):
    """Esimesed n lauset promptiks, ülejäänu vastuseks."""
    laused = re.split(r"(?<=[.!?]) +", tekst)
    if len(laused) < n_lauset + 2:
        return None, None
    return " ".join(laused[:n_lauset]), " ".join(laused[n_lauset:])

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--valjund", default=f"{P}/ring13_stiil.jsonl")
    a = p.parse_args()
    random.seed(SEEME)
    blokk = eval_blokk()

    # loe lõigud žanrite kaupa; jätka-ülesandeks sobivad pikad lõigud
    zanrid = collections.defaultdict(list)
    for r in open(f"{P}/koondkorpus_loigud.jsonl"):
        d = json.loads(r)
        if 80 <= d["sonu"] <= 400:
            zanrid[d["zanr"]].append(d)

    KVOODID = {"ilukirjandus": 600, "teadus": 250, "ajakirjandus": 250,
               "populaarteadus": 60}
    STIILID = {"ilukirjandus": "ilukirjanduslikus stiilis",
               "teadus": "teaduslikus stiilis",
               "ajakirjandus": "ajakirjanduslikus stiilis",
               "populaarteadus": "populaarteaduslikus stiilis"}

    tulem, nahtud = [], set()
    for zanr, kvoot in KVOODID.items():
        kandidaadid = zanrid.get(zanr, [])
        random.shuffle(kandidaadid)
        n = 0
        for d in kandidaadid:
            if n >= kvoot:
                break
            # evali leke: kui lõigus on evali haruldasi sisusõnu, jäta vahele
            sonad = set(re.findall(r"[a-zõäöüšž\-]{5,}", d["tekst"].lower()))
            if len(sonad & blokk) > 8:
                continue
            algus, jatk = lause_piir(d["tekst"])
            if not algus or len(jatk.split()) < 50:
                continue
            if algus in nahtud:
                continue
            nahtud.add(algus)
            umbes = round(len(jatk.split()) / 25) * 25
            tulem.append({"messages": [
                {"role": "user", "content":
                 f"Jätka teksti {STIILID[zanr]}, umbes {umbes} sõnaga:\n\n{algus}"},
                {"role": "assistant", "content": jatk}],
                "kategooria": f"stiil-{zanr}", "allikas": d["allikas"],
                "litsents": d["litsents"]})
            n += 1

    random.shuffle(tulem)
    with open(a.valjund, "w") as f:
        for t in tulem:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(f"valmis: {len(tulem)} näidet → {a.valjund}")
    for k, n in collections.Counter(t["kategooria"] for t in tulem).most_common():
        print(f"  {k:<24}{n:>6}")

if __name__ == "__main__":
    main()
