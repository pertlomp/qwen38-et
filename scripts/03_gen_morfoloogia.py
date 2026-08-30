#!/usr/bin/env python3
"""Genereerib reeglipõhiseid morfoloogianäiteid Vabamorfiga (EstNLTK).

Miks: baasjoone kõige suurem auk on käänamine ja käändesüsteemi tundmine,
aga TalTechi inflection_et annab ainult ~1000 näidet. Vabamorf genereerib
piiramatult — ja kuna need on reeglipõhised, on nad ka litsentsipuhtad
(avaldatava tuuma osa).

Kvaliteedikontroll: iga genereeritud vorm käib RING-KONTROLLI läbi — vorm
analüüsitakse tagasi ja kontrollitakse, kas lemma ja vorm klapivad. Vormid,
mis ei klapi, visatakse ära (Vabamorf eksib haruldaste sõnadega).

Väljund: data/processed/morf_gen.jsonl
"""
import collections, json, os, random, sys
from estnltk import Text
from estnltk.vabamorf.morf import Vabamorf, synthesize

_VM = Vabamorf.instance()

def analyze(sonad):
    """Ühilduskiht: vana `analyze` API asendus Vabamorf-instantsi kaudu."""
    return _VM.analyze(words=sonad, guess=False, propername=False)

OUT = "/mnt/varu/qwen38-et-data/processed"
RAW = "/mnt/varu/qwen38-et-data/raw"
SEEME = 20260822
random.seed(SEEME)

# 14 käänet: (eestikeelne nimi, Vabamorfi kood, küsimus)
KAANDED = [
    ("nimetav", "n", "kes? mis?"), ("omastav", "g", "kelle? mille?"),
    ("osastav", "p", "keda? mida?"), ("sisseütlev", "ill", "kellesse? millesse?"),
    ("seesütlev", "in", "kelles? milles?"), ("seestütlev", "el", "kellest? millest?"),
    ("alaleütlev", "all", "kellele? millele?"), ("alalütlev", "ad", "kellel? millel?"),
    ("alaltütlev", "abl", "kellelt? millelt?"), ("saav", "tr", "kelleks? milleks?"),
    ("rajav", "ter", "kelleni? milleni?"), ("olev", "es", "kellena? millena?"),
    ("ilmaütlev", "ab", "kelleta? milleta?"), ("kaasaütlev", "kom", "kellega? millega?"),
]

def korja_lemmad(mitu_lauset=8000, min_sagedus=4):
    """Korjab sagedased nimi- ja omadussõnade lemmad päris tekstist."""
    laused = []
    for f in sorted(os.listdir(f"{RAW}/riigikogu-steno"))[:40]:
        try:
            d = json.load(open(f"{RAW}/riigikogu-steno/{f}", encoding="utf-8"))
        except Exception:
            continue
        for istung in d if isinstance(d, list) else []:
            for pkt in istung.get("agendaItems") or []:
                for e in pkt.get("events") or []:
                    t = e.get("text")
                    if t and 40 < len(t) < 1200:
                        laused.append(t)
                        if len(laused) >= mitu_lauset:
                            break
                if len(laused) >= mitu_lauset: break
            if len(laused) >= mitu_lauset: break
        if len(laused) >= mitu_lauset: break
    print(f"analüüsin {len(laused)} lauset...", flush=True)

    loend = collections.Counter()
    for i in range(0, len(laused), 200):
        tykk = " ".join(laused[i:i+200])
        try:
            t = Text(tykk); t.tag_layer(["morph_analysis"])
        except Exception:
            continue
        for s in t.morph_analysis:
            pos = s.partofspeech[0]; lem = s.lemma[0]
            if pos in ("S", "A") and lem and lem.isalpha() and 3 <= len(lem) <= 18:
                loend[(lem, pos)] += 1
        if (i // 200) % 10 == 0:
            print(f"  {i}/{len(laused)} lauset, {len(loend)} lemmat", flush=True)
    return [(l, p) for (l, p), c in loend.most_common() if c >= min_sagedus]

def kontrolli(lemma, vorm, kaane_kood, arv):
    """Ring-kontroll: kas genereeritud vorm analüüsub tagasi õigeks?"""
    try:
        a = analyze([vorm])[0]["analysis"]
    except Exception:
        return False
    oodatud = f"{'sg' if arv == 'ainsuse' else 'pl'} {kaane_kood}"
    for v in a:
        if v.get("lemma") == lemma and v.get("form", "").strip() == oodatud:
            return True
    return False

def main():
    lemmad = korja_lemmad()
    print(f"\nsagedasi lemmasid: {len(lemmad)}")
    valim = lemmad[:2500]

    naited, katsed, labi = [], 0, 0
    for lemma, pos in valim:
        for arv, arv_kood in (("ainsuse", "sg"), ("mitmuse", "pl")):
            for nimi, kood, kysimus in KAANDED:
                katsed += 1
                try:
                    vormid = synthesize(lemma, f"{arv_kood} {kood}")
                except Exception:
                    continue
                if not vormid: continue
                vorm = vormid[0]
                if not vorm or vorm == lemma and nimi != "nimetav": continue
                if not kontrolli(lemma, vorm, kood, arv):
                    continue
                labi += 1
                naited.append({"lemma": lemma, "sonaliik": pos, "arv": arv,
                               "kaane": nimi, "kaane_kysimus": kysimus, "vorm": vorm})
        if len(naited) % 2000 < 28 and naited:
            print(f"  {len(naited)} vormi kontrollitud...", flush=True)

    os.makedirs(OUT, exist_ok=True)
    tee = f"{OUT}/morf_gen.jsonl"
    with open(tee, "w", encoding="utf-8") as f:
        for n in naited:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")
    print(f"\nVALMIS: {len(naited)} kontrollitud vormi ({labi}/{katsed} = "
          f"{labi/max(katsed,1)*100:.1f}% läbis ring-kontrolli)")
    print(f"→ {tee}")

if __name__ == "__main__":
    main()
