#!/usr/bin/env python3
"""Ring 10: viimased augud + degeneratsiooni ravi.

Ring9 diagnoos (eval/runs/ring9-bnb):
  1. DEGENERATSIOON avatud ülesannetes: "liiteosaga liiteosaga..." (man-011),
     leiutatud sõnad "tervisandur" (man-015), "parem, parem, parem" (man-008).
     Üheksa drilli-ringi on kahjustanud vaba genereerimist → ravi on avatud
     vastuste materjal tagasi (build-skriptis, mitte siin).
  2. Võrdlusastmed katki: "algvõrre: parem, keskvõrre: parem, ülivõrre: parem".
  3. Saav vs rajav segi: "rajav: kooliks" (peab olema koolini).
  4. Liitsõnaloendid ("viis liitsõna sõnaga X") annavad leiutatud sõnu.
  5. Tööriistad flipis 50-le — ravi build-skriptis (ring4 tööriistanäited).
"""
import argparse, collections, json, random, re
from estnltk.vabamorf.morf import synthesize

SEEME = 20260902

# ---------- 1: võrdlusastmed (kureeritud, sh supletiivsed erandid) ----------
VORDLUS = [("hea", "parem", "parim"), ("halb", "halvem", "halvim"),
    ("suur", "suurem", "suurim"), ("väike", "väiksem", "väikseim"),
    ("pikk", "pikem", "pikim"), ("lühike", "lühem", "lühim"),
    ("vana", "vanem", "vanim"), ("noor", "noorem", "noorim"),
    ("kiire", "kiirem", "kiireim"), ("aeglane", "aeglasem", "aeglaseim"),
    ("kõrge", "kõrgem", "kõrgeim"), ("madal", "madalam", "madalaim"),
    ("tugev", "tugevam", "tugevaim"), ("nõrk", "nõrgem", "nõrgim"),
    ("ilus", "ilusam", "ilusaim"), ("tark", "targem", "targim"),
    ("rikas", "rikkam", "rikkaim"), ("vaene", "vaesem", "vaeseim"),
    ("soe", "soojem", "soojim"), ("külm", "külmem", "külmim"),
    ("kallis", "kallim", "kalleim"), ("odav", "odavam", "odavaim"),
    ("raske", "raskem", "raskeim"), ("kerge", "kergem", "kergeim"),
    ("puhas", "puhtam", "puhtaim"), ("julge", "julgem", "julgeim"),
    ("õnnelik", "õnnelikum", "õnnelikem"), ("oluline", "olulisem", "olulisim")]

def moodul_1():
    tulem = []
    for alg, kesk, yli in VORDLUS:
        tulem.append(("morfoloogia-meta",
            f"Mis on sõna '{alg}' keskvõrre ja ülivõrre? Nimeta ka algvõrre.",
            f"algvõrre {alg}, keskvõrre {kesk}, ülivõrre {yli} (kõige {kesk})"))
        tulem.append(("morfoloogia-meta",
            f"Mis on omadussõna '{kesk}' algvõrre?",
            f"algvõrre on {alg} (keskvõrre {kesk}, ülivõrre {yli})"))
    return tulem

# ---------- 2: saav vs rajav kontrast ----------
SAAV_RAJAV = ["kool", "mets", "linn", "meri", "kodu", "tipp", "lõpp", "jõgi",
              "sild", "piir", "hommik", "õhtu", "kevad", "sügis", "arst",
              "õpetaja", "juht", "meister", "täiskasvanu", "vanaisa"]

def moodul_2():
    tulem = []
    for s in SAAV_RAJAV:
        S = synthesize(s, "sg tr", "S")
        R = synthesize(s, "sg ter", "S")
        if not S or not R:
            continue
        saav, rajav = S[-1], R[-1]
        tulem.append(("morfoloogia-meta",
            f"Mis vahe on saaval ja rajaval käändel? Too mõlemast üks näide "
            f"sõnaga '{s}'.",
            f"Saav kääne näitab, milleks saadakse või muututakse: {saav}. "
            f"Rajav kääne näitab piiri, milleni jõutakse: {rajav}."))
        tulem.append(("morfoloogia-meta",
            f"Pane sõna '{s}' rajavasse käändesse (milleni?).", rajav))
        tulem.append(("morfoloogia-meta",
            f"Pane sõna '{s}' saavasse käändesse (milleks?).", saav))
    return tulem

# ---------- 3: liitsõnaloendid PÄRIS sõnadega ----------
LOENDID = {
    "tervise": ["tervisekontroll", "tervisekeskus", "terviserada",
                "tervisekindlustus", "tervisetõend", "terviseamet"],
    "töö": ["töökoht", "tööpäev", "tööleping", "tööaeg", "tööandja", "töötuba"],
    "päikese": ["päikesetõus", "päikeseloojang", "päikeseprillid",
                "päikesekiir", "päikesevalgus", "päikesepaneel"],
    "raamatu": ["raamatukogu", "raamatupidamine", "raamatupood",
                "raamaturiiul", "raamatuklubi", "raamatukaas"],
    "vee": ["veekogu", "veepudel", "veetase", "veetorustik", "veekeetja",
            "veepark"],
    "metsa": ["metsarada", "metsloom", "metsatukk", "metsamaja",
              "metsatöö", "metsamarjad"],
    "kooli": ["koolimaja", "koolipäev", "koolivaheaeg", "koolitee",
              "koolikott", "koolitoit"],
    "au": ["autasu", "aukiri", "auhind", "aumärk", "auväärt", "aukodanik"],
    "silma": ["silmaarst", "silmapaar", "silmapiir", "silmaring",
              "silmatera", "silmside"],
    "südame": ["südamehaigus", "südamelöök", "südamevalu", "südamesõber",
               "südametunnistus", "südamerütm"],
}

def moodul_3():
    tulem = []
    for algus, loend in LOENDID.items():
        viis = loend[:5]
        tulem.append(("liitsonad",
            f"Kirjuta viis liitsõna, mis algavad sõnaga "
            f"'{algus.rstrip('e') if algus.endswith('se') else algus}'."
            if False else
            f"Kirjuta viis liitsõna, mille esiosa on '{algus}'.",
            ", ".join(viis)))
        tulem.append(("liitsonad",
            f"Nimeta kolm liitsõna, mille esiosa on '{algus}'.",
            ", ".join(loend[:3])))
    return tulem

# ---------- 4: ühendverb vs liitnimisõna (man-011 muster) ----------
YHENDID = [("kokku võtma", "kokkuvõte"), ("välja andma", "väljaanne"),
    ("sisse astuma", "sisseastumine"), ("üles ehitama", "ülesehitus"),
    ("ette valmistama", "ettevalmistus"), ("läbi viima", "läbiviimine"),
    ("alla laadima", "allalaadimine"), ("üle vaatama", "ülevaatus"),
    ("ära ütlema", "äraütlemine"), ("juurde pääsema", "juurdepääs"),
    ("välja pääsema", "väljapääs"), ("sisse pääsema", "sissepääs")]

def moodul_4():
    tulem = []
    for verb, nimi in YHENDID:
        tulem.append(("liitsonad",
            f"Kas kirjutada kokku või lahku: '{verb}' (tegevusena) ja "
            f"'{nimi}' (asjana)? Selgita reeglit ühe lausega.",
            f"Ühendverb '{verb}' kirjutatakse lahku, aga sellest tuletatud "
            f"nimisõna '{nimi}' kokku."))
    return tulem

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--valjund",
                   default="/mnt/varu/qwen38-et-data/processed/ring10_moodulid.jsonl")
    a = p.parse_args()
    random.seed(SEEME)

    blokk = set()
    for r in open("/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/eval/et_locked_v1.jsonl"):
        d = json.loads(r)
        blokk.update(re.findall(r"[a-zõäöüšž\-]{4,}",
                     f"{d.get('prompt','')}".lower()))

    osad = moodul_1() + moodul_2() + moodul_3() + moodul_4()
    nahtud, tulem = set(), []
    for kat, k, v in osad:
        if k in nahtud:
            continue
        nahtud.add(k)
        tulem.append({"messages": [{"role": "user", "content": k},
                                   {"role": "assistant", "content": v}],
                      "kategooria": kat, "allikas": "ring10-gen",
                      "litsents": "kureeritud / reeglipõhine"})
    random.shuffle(tulem)
    with open(a.valjund, "w") as f:
        for t in tulem:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(f"valmis: {len(tulem)} näidet → {a.valjund}")
    for k, n in collections.Counter(t["kategooria"] for t in tulem).most_common():
        print(f"  {k:<20}{n:>6}")

if __name__ == "__main__":
    main()
