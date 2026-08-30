#!/usr/bin/env python3
"""Ring 11: vestluskäitumise ravi — Perti päris testi leiud (2026-08-25 õhtu).

Perti transkriptist kolm diagnoosi:
  1. GEC-LEKK: "Kuidas läheb sõber" → mudel parandas grammatikat (valesti) ja
     kordas järgmise lause lihtsalt tagasi. 2500 GEC-näidet õpetasid: iga sisend
     on parandamist ootav lause.
  2. LÜHIVASTUSE KALLE: "kirjuta 300 sõnaga" → 60 sõna. Drillid õpetasid, et
     hea vastus on lühike.
  3. Vaba registri vead ("sai kutsung", "suurel lavastel").

Ravi kolm moodulit:
  A. Anti-GEC kontrastpaarid: SAMA lause kahes kontekstis — "Paranda: X" →
     parandus; X üksi (vestlus) → sisuline VASTUS. Kõnekeelsed tervitused
     saavad sooja vastuse, mitte keeleõpetust.
  B. Pikkuse järgimine: "kirjuta ~N sõnaga" → päris N-sõnaline vastus
     (alpaca-est pikad vastused + instructERRnews kokkuvõtted, päris andmed).
  C. Vestlusregister: mitmelauselised soojad vastused tavaküsimustele
     (kureeritud, Perti transkripti mustrite järgi).
"""
import argparse, collections, json, random, re

SEEME = 20260903
P = "/mnt/varu/qwen38-et-data"

# ---------- A: anti-GEC kontrast ----------
TERVITUSED = [
    ("Kuidas läheb sõber", "Tänan küsimast, mul läheb hästi! Olen valmis "
     "aitama, millega iganes vaja. Kuidas sinul läheb?"),
    ("Tere, kuidas elad", "Tere! Elan hästi, tänan küsimast. Mille juures "
     "saan sind täna aidata?"),
    ("No kuidas on lood", "Kõik on kombes, tänan! Räägi, mis sul mõttes on."),
    ("Tsau, mis teed", "Tsau! Olen siin ja valmis aitama. Mis sul plaanis on?"),
    ("Kuidas läheb", "Hästi läheb, aitäh! Kuidas sinul? Millega saan abiks olla?"),
    ("Tere hommikust sõber", "Tere hommikust! Loodan, et päev algab hästi. "
     "Millega tegeleme?"),
    ("Mis toimub", "Kõik rahulik siinpool! Ootan sinu küsimusi. Mis sul "
     "südamel on?"),
    ("Kas sa oled olemas", "Jah, olen siin ja kuulan. Räägi, millega saan "
     "aidata."),
    ("Tere tere", "Tere-tere! Tore sind näha. Mis täna teoksil?"),
    ("Noh kuidas siis läheb ka", "Läheb päris hästi, tänan! Sina räägi — "
     "kas on midagi, mille kallal koos nokitseme?"),
]
# kõnekeelsed laused, mis EI vaja parandamist, vaid vastust
VESTLUSLAUSED = [
    ("ma küsisin seda sinu käest sest sa oled minu sõber",
     "Ja mul on hea meel, et küsisid! Sõbra käest küsimine on kõige õigem "
     "tee. Mul läheb hästi — olen valmis sind aitama, millal iganes vaja."),
    ("ma mõtlesin täna sinu peale",
     "See on armas kuulda! Mina olen alati siin, kui sul on vaja mõtteid "
     "vahetada või abi saada. Mis sul mõttes mõlkus?"),
    ("sa oled täna kuidagi vaikne",
     "Vabandust, kui nii tundus! Olen täiesti kohal ja kuulan tähelepanelikult. "
     "Räägi, mis sul plaanis on."),
    ("äkki teeme midagi huvitavat",
     "Hea mõte! Võime näiteks kirjutada loo, arutada mõnd põnevat teemat või "
     "lahendada mõne ülesande. Mis sind täna kõige rohkem huvitab?"),
]

def moodul_a(gec_allikas, n):
    tulem = []
    for k, v in TERVITUSED + VESTLUSLAUSED:
        tulem.append(("vestlus", k, v))
    # kontrastpaarid päris GEC-andmetest: parandus AINULT kui küsitakse
    read = []
    for tee in (f"{P}/raw/taltech/grammar_et/grammar_l2_train.jsonl",
                f"{P}/raw/taltech/grammar2_et/grammar_l1.jsonl"):
        try:
            for rida in open(tee):
                try:
                    d = json.loads(rida)
                except Exception:
                    continue
                o, c = d.get("original"), d.get("correct")
                if o and c and o != c and 30 < len(o) < 200:
                    read.append((o, c))
        except FileNotFoundError:
            continue
    random.shuffle(read)
    for o, c in read[:n]:
        if random.random() < 0.5:
            tulem.append(("gec-kysitud",
                          f"Paranda selle lause keelevead: '{o}'", c))
        else:
            # SAMA tüüpi lause ILMA palveta → sisuline reaktsioon, mitte parandus
            tulem.append(("vestlus-mitte-gec", o,
                          "Sain mõttest aru! " + c.rstrip(".") +
                          " — kas soovid, et aitan selle teemaga edasi?"))
    return tulem

# ---------- B: pikkuse järgimine (päris pikad vastused) ----------
def moodul_b(n):
    tulem = []
    d = json.load(open(f"{P}/raw/alpaca-est/data/alpaca_est.json"))
    pikad = [x for x in d if len(x.get("output", "").split()) >= 120
             and not x.get("input")]
    random.shuffle(pikad)
    for x in pikad[:n]:
        sonu = len(x["output"].split())
        umbes = round(sonu / 50) * 50
        tulem.append(("pikk-vastus",
                      f"{x['instruction'].rstrip('.?!')}. Kirjuta umbes "
                      f"{umbes} sõnaga.", x["output"]))
    return tulem

# ---------- C: instructERRnews kokkuvõtted (päris ajakirjanduskeel) ----------
def moodul_c(n):
    import pandas as pd
    df = pd.read_parquet(
        f"{P}/raw/taltech/instructERRnews/data/train-00000-of-00001.parquet")
    df = df[df["output"].str.split().str.len().between(40, 250)]
    valik = df.sample(n=min(n, len(df)), random_state=SEEME)
    tulem = []
    for _, r in valik.iterrows():
        tulem.append(("uudise-kokkuvote",
                      f"{r['instruction']}\n\n{r['input'][:3000]}",
                      r["output"]))
    return tulem

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--valjund", default=f"{P}/processed/ring11_vestlus.jsonl")
    a = p.parse_args()
    random.seed(SEEME)

    osad = moodul_a(None, 400) + moodul_b(400) + moodul_c(400)
    nahtud, tulem = set(), []
    for kat, k, v in osad:
        if k in nahtud:
            continue
        nahtud.add(k)
        tulem.append({"messages": [{"role": "user", "content": k},
                                   {"role": "assistant", "content": v}],
                      "kategooria": kat, "allikas": "ring11-vestlus",
                      "litsents": "alpaca-est/instructERRnews/gec + kureeritud"})
    random.shuffle(tulem)
    with open(a.valjund, "w") as f:
        for t in tulem:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(f"valmis: {len(tulem)} näidet → {a.valjund}")
    for k, n in collections.Counter(t["kategooria"] for t in tulem).most_common():
        print(f"  {k:<20}{n:>6}")

if __name__ == "__main__":
    main()
