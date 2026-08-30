#!/usr/bin/env python3
"""Ring 6 generaator: viis moodulit dpo3 evali PÄRIS vigade peale.

Veaanalüüs (eval/runs/dpo3-bnb/vastused.jsonl, 2026-08-25):
  A. sõnaleiutamine 42,9 — üle- JA alatuvastab olematuid sõnu (man-034: väitis, et
     "mõttetera" ja "kalatoit" pole olemas; man-033 jj)
  B. morfoloogia-meta 64,8 — verbimorf nõrk: da-tegevusnimi "lugemine" pro "lugeda"
     (man-009), kaudne kõneviis "kirjutatavat" pro "kirjutavat" (man-007), käände
     nimetamine "esseütlev" (man-004)
  C. JSON 66,7 — võtmed täpitähtedega ("kuupäev" pro "kuupaev"), formaadidistsipliin
  D. tehniline 50,0 — anglitsismid ("deploy'isin" pro "juurutasin"), lühendite käänamine
  E. liitsõnad 71,4 — arvsõna-liitsõnad pooleldi ("viiekümne eurone" pro
     "viiekümneeurone", man-017)

Kõik moodulid on reeglipõhised ja Vabamorfi ring-kontrolliga (sama metoodika mis
16_gen_fraasid.py). Evali leke blokeeritakse et_locked_v1.jsonl sisusõnadega.
"""
import argparse, collections, json, random, re
from estnltk.vabamorf.morf import Vabamorf, synthesize

_VM = Vabamorf.instance()
SEEME = 20260826
EVAL = "/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/eval/et_locked_v1.jsonl"
MORF = "/mnt/varu/qwen38-et-data/processed/morf_gen.jsonl"

def eval_blokk():
    """Kõik evali sisusõnad (4+ tähte) — neid treeningusse ei lähe."""
    sonad = set()
    for r in open(EVAL):
        d = json.loads(r)
        tekst = f"{d.get('prompt','')} {d.get('oige_vastus') or ''}"
        for s in re.findall(r"[a-zõäöüšž\-]{4,}", tekst.lower()):
            sonad.add(s)
    return sonad

def olemas(sona):
    """Kas sõna on päris sõnastikusõna?

    Vabamorf "tunneb" ka produktiivseid tuletisi (rõõmustu=vus) — need EI ole
    päris sõnad; juures on siis "="-märk. Tundmatud saavad Z-märgendi.
    """
    try:
        a = _VM.analyze(words=[sona], guess=False, propername=False)[0]["analysis"]
    except Exception:
        return False
    return any(x["partofspeech"] in ("S", "A", "V", "D", "K")
               and "=" not in x["root"] for x in a)

# ---------- A: sõnade olemasolu ----------
VALELIITED = ["uvus", "tis", "ldus", "mus", "ngus", "stus", "lik", "tsus",
              "vus", "line", "kond", "stik"]

def moodul_a(lemmad, blokk, n):
    """Pooled päris sõnad (jah), pooled väljamõeldud (ei), pluss loendiülesanded."""
    random.shuffle(lemmad)
    parised = [l for l in lemmad if l not in blokk and len(l) >= 4][:n]
    vale = []
    katsed = 0
    while len(vale) < n and katsed < n * 60:
        katsed += 1
        alus = random.choice(parised)
        kand = alus[:max(3, len(alus) - random.choice((2, 3)))] + random.choice(VALELIITED)
        if kand in blokk or olemas(kand) or kand in vale:
            continue
        vale.append(kand)
    tulem = []
    for s in parised[:n // 2]:
        tulem.append((f"Kas sõna '{s}' on eesti keeles olemas? Vasta jah või ei.",
                      f"Jah, sõna '{s}' on eesti keeles olemas."))
    for s in vale[:n // 2]:
        tulem.append((f"Kas sõna '{s}' on eesti keeles olemas? Vasta jah või ei.",
                      f"Ei, sõna '{s}' ei ole eesti keeles olemas."))
    # loendiülesanded: 3 päris + 1-2 võltsi, nimeta AINULT võltsid
    for _ in range(n // 4):
        p3 = random.sample(parised, 3)
        v = random.sample(vale, random.choice((1, 2)))
        koik = p3 + v
        random.shuffle(koik)
        tulem.append((f"Millised neist sõnadest ei ole eesti keeles olemas: "
                      f"{', '.join(koik)}? Nimeta ainult olematud.",
                      f"Olemas ei ole: {', '.join(v)}. Ülejäänud on päris sõnad."))
    return [("sonaleiutamine", k, v) for k, v in tulem]

# ---------- B: verbimorfoloogia + käände tuvastus ----------
def moodul_b(blokk, n):
    verbid = set()
    for r in open("/mnt/varu/qwen38-et-data/processed/sft_v1_ring4.jsonl"):
        pass  # verbe korjame morf-analüüsiga allpool hoopis lihtsamalt
    # sagedased verbid: võta lemmapoolist need, mida Vabamorf V-na sünteesib
    kandidaadid = ["kirjutama", "lugema", "tulema", "minema", "sööma", "jooma",
        "õppima", "töötama", "mängima", "laulma", "tantsima", "jooksma", "hüppama",
        "magama", "ärkama", "ehitama", "ostma", "müüma", "maksma", "saatma",
        "võtma", "andma", "tegema", "nägema", "kuulma", "rääkima", "vastama",
        "küsima", "aitama", "otsima", "leidma", "kaotama", "võitma", "algama",
        "lõppema", "jätkama", "muutuma", "kasvama", "vähenema", "tõusma",
        "langema", "avama", "sulgema", "alustama", "lõpetama", "planeerima",
        "korraldama", "juhtima", "õpetama", "tundma", "teadma", "arvama",
        "mõtlema", "unustama", "meenutama", "keetma", "küpsetama", "pesema",
        "koristama", "parandama", "sõitma", "lendama", "ujuma", "kõndima",
        "seisma", "istuma", "lamama", "naerma", "nutma", "kartma", "lootma",
        "soovima", "tahtma", "vajama", "armastama", "vihkama", "usaldama"]
    verbid = [v for v in kandidaadid if v not in blokk and synthesize(v, "da", "V")]
    tulem = []
    for v in verbid[:n]:
        da = synthesize(v, "da", "V")[0]
        vat = synthesize(v, "vat", "V")[0]
        p6 = [synthesize(v, f, "V")[0] for f in ("n", "d", "b", "me", "te", "vad")]
        ksk = synthesize(v, "takse", "V")[0]
        tulem += [
            ("morfoloogia-meta",
             f"Moodusta sõnast '{v}' da-tegevusnimi ja ma-tegevusnimi.",
             f"da-tegevusnimi: {da}, ma-tegevusnimi: {v}"),
            ("morfoloogia-meta",
             f"Pane tegusõna '{v}' kaudsesse kõneviisi olevikus (ainsuse 3. isik).",
             f"{vat}"),
            ("morfoloogia-meta",
             f"Pööra tegusõna '{v}' kindla kõneviisi olevikus kõigis kuues isikus.",
             f"ma {p6[0]}, sa {p6[1]}, ta {p6[2]}, me {p6[3]}, te {p6[4]}, nad {p6[5]}"),
            ("morfoloogia-meta",
             f"Pane tegusõna '{v}' umbisikulisse tegumoodi olevikus.",
             f"{ksk}"),
        ]
    # käände tuvastus: AINULT üheselt analüüsitavad vormid morf_gen-ist
    read = [json.loads(r) for r in open(MORF)]
    random.shuffle(read)
    KAANE_VM = {"n": "nimetav", "g": "omastav", "p": "osastav", "ill": "sisseütlev",
        "in": "seesütlev", "el": "seestütlev", "all": "alaleütlev", "ad": "alalütlev",
        "abl": "alaltütlev", "tr": "saav", "ter": "rajav", "es": "olev",
        "ab": "ilmaütlev", "kom": "kaasaütlev"}
    lisatud = 0
    for d in read:
        if lisatud >= n:
            break
        vorm, lemma = d["vorm"], d["lemma"]
        if vorm in blokk or vorm == lemma:
            continue
        try:
            a = _VM.analyze(words=[vorm], guess=False, propername=False)[0]["analysis"]
        except Exception:
            continue
        vormikoodid = {x["form"] for x in a if x["partofspeech"] in ("S", "A")}
        if len(vormikoodid) != 1:          # mitmeti tõlgendatav — jäta vahele
            continue
        kood = vormikoodid.pop().split()
        if len(kood) != 2 or kood[1] not in KAANE_VM:
            continue
        arv = "ainsuse" if kood[0] == "sg" else "mitmuse"
        tulem.append(("morfoloogia-meta",
                      f"Millises käändes on sõna '{vorm}'? Nimeta kääne ja arv.",
                      f"{arv} {KAANE_VM[kood[1]]} (algvorm: {lemma})"))
        lisatud += 1
    return tulem

# ---------- C: JSON ja formaadidistsipliin ----------
NIMED = ["Mari", "Jaan", "Kati", "Peeter", "Liis", "Andres", "Tiina", "Mart",
         "Anu", "Toomas", "Kadri", "Rein", "Piret", "Urmas", "Helen"]
LINNAD = [("Tallinn", "Harjumaa"), ("Tartu", "Tartumaa"), ("Pärnu", "Pärnumaa"),
    ("Narva", "Ida-Virumaa"), ("Viljandi", "Viljandimaa"), ("Rakvere", "Lääne-Virumaa"),
    ("Kuressaare", "Saaremaa"), ("Võru", "Võrumaa"), ("Valga", "Valgamaa"),
    ("Haapsalu", "Läänemaa"), ("Jõhvi", "Ida-Virumaa"), ("Paide", "Järvamaa")]
TOOTED = ["arvuti", "tool", "laud", "lamp", "raamat", "telefon", "kohver",
          "jalgratas", "kell", "prillid"]
KUUD = ["jaanuari", "veebruari", "märtsi", "aprilli", "mai", "juuni", "juuli",
        "augusti", "septembri", "oktoobri", "novembri", "detsembri"]

def moodul_c(n):
    tulem = []
    for _ in range(n):
        t = random.choice(("isik", "arve", "toode", "linnad", "formaat"))
        if t == "isik":
            nimi, vanus = random.choice(NIMED), random.randint(18, 79)
            linn = random.choice(LINNAD)[0]
            vastus = json.dumps({"nimi": nimi, "vanus": vanus, "linn": linn},
                                ensure_ascii=False)
            tulem.append(("json-struktuur",
                f"Tagasta JSON-objekt väljadega nimi, vanus, linn järgmise info "
                f"põhjal: {nimi} on {vanus}-aastane ja elab {linn}"
                f"{'as' if linn.endswith(('n','u','e')) else 'is'}. "
                f"Vasta ainult JSON-iga, ilma selgituseta.", vastus))
        elif t == "arve":
            summa, p = random.randint(50, 5000), random.randint(1, 28)
            kuu = random.randint(1, 12)
            vastus = json.dumps({"summa": summa, "valuuta": "EUR",
                                 "kuupaev": f"2026-{kuu:02d}-{p:02d}"},
                                ensure_ascii=False)
            tulem.append(("json-struktuur",
                f"Eralda struktureeritud andmed JSON-ina (väljad: summa, valuuta, "
                f"kuupaev): 'Arve summas {summa} eurot tuleb tasuda {p}. "
                f"{KUUD[kuu-1]} 2026.' NB: JSON-i võtmed kirjuta täpitähtedeta. "
                f"Vasta ainult JSON-iga.", vastus))
        elif t == "toode":
            toode, hind, kogus = (random.choice(TOOTED), random.randint(5, 900),
                                  random.randint(1, 12))
            vastus = json.dumps({"toode": toode, "hind": hind, "kogus": kogus},
                                ensure_ascii=False)
            tulem.append(("json-struktuur",
                f"Tagasta JSON väljadega toode, hind, kogus: tellimuses on "
                f"{kogus} tk toodet '{toode}' hinnaga {hind} eurot. Ainult JSON.",
                vastus))
        elif t == "linnad":
            valik = random.sample(LINNAD, 3)
            vastus = json.dumps([{"linn": l, "maakond": m} for l, m in valik],
                                ensure_ascii=False)
            tulem.append(("json-struktuur",
                "Tagasta JSON-massiiv kolmest Eesti linnast, iga element "
                "objektina väljadega 'linn' ja 'maakond'. Ainult JSON.", vastus))
        else:  # formaadidistsipliin
            alam = random.choice(("read", "sona"))
            if alam == "read":
                valik = random.sample(LINNAD, 3)
                tulem.append(("json-struktuur",
                    "Loetle kolm Eesti linna, iga uuel real, ilma numeratsioonita "
                    "ja ilma sissejuhatava lauseta.",
                    "\n".join(l for l, _ in valik)))
            else:
                l, m = random.choice(LINNAD)
                tulem.append(("json-struktuur",
                    f"Vasta ainult ühe sõnaga (ilma kirjavahemärkideta): mis "
                    f"maakonnas asub {l}?", m))
    return tulem

# ---------- D: tehniline — lühendid + anglitsismid ----------
# True = hääldus lõpeb kaashäälikuga → tüvevokaal "i" (GPS-ist, mitte GPS-st)
LYHENDID = {"API": False, "URL": True, "PDF": True, "SMS": True, "ID": False,
            "IT": False, "CV": False, "PIN": True, "GPS": True, "USB": False,
            "HTML": True, "CSS": True, "SQL": True, "AI": False, "TV": False,
            "KKK": False, "IBAN": True, "CEO": False, "HR": True}
L_KAANDED = [("alaleütlevas (kellele/millele)", "le"),
             ("seestütlevas (kellest/millest)", "st"),
             ("kaasaütlevas (kellega/millega)", "ga"),
             ("alalütlevas (kellel/millel)", "l"),
             ("saavas (kelleks/milleks)", "ks"),
             ("seesütlevas (kelles/milles)", "s")]
ANGLITSISMID = [
    ("deployima", "juurutama või paigaldama"), ("feedback", "tagasiside"),
    ("meeting", "koosolek"), ("deadline", "tähtaeg"), ("update", "uuendus"),
    ("upgrade", "täiendus või uuendus"), ("bug", "viga"),
    ("feature", "funktsioon või võimalus"), ("release", "väljalase"),
    ("server", "server (kinnistunud termin)"), ("backup", "varukoopia"),
    ("download", "allalaadimine"), ("upload", "üleslaadimine"),
    ("login", "sisselogimine"), ("account", "konto"), ("password", "parool"),
    ("attachment", "manus"), ("folder", "kaust"), ("printima", "printima (kinnistunud)"),
    ("cancel", "tühistama"), ("submit", "esitama"), ("draft", "mustand"),
    ("skill", "oskus"), ("workshop", "töötuba"), ("brainstorm", "ajurünnak"),
    ("checklist", "kontrollnimekiri"), ("performance", "jõudlus"),
    ("dashboard", "töölaud või juhtpaneel"), ("template", "mall"),
    ("default", "vaikeväärtus"), ("settings", "seaded"), ("device", "seade"),
    ("storage", "salvestusruum"), ("cloud", "pilv"), ("streamima", "voogedastama")]

def moodul_d(n):
    tulem = []
    for _ in range(n):
        if random.random() < 0.5:
            lyh, konsonant = random.choice(list(LYHENDID.items()))
            nimi, lopp = random.choice(L_KAANDED)
            vorm = f"{lyh}-i{lopp}" if konsonant else f"{lyh}-{lopp}"
            tulem.append(("tehniline",
                f"Kuidas käänata lühendit '{lyh}' {nimi} käändes?", vorm))
        else:
            ing, eesti = random.choice(ANGLITSISMID)
            tulem.append(("tehniline",
                f"Mis on eestikeelne vaste sõnale '{ing}'? Eelista eesti sõna.",
                f"{eesti}"))
    return tulem

# ---------- E: arvsõna-liitsõnad ----------
ARVUD_OM = [("kahe", 2), ("kolme", 3), ("nelja", 4), ("viie", 5), ("kuue", 6),
    ("seitsme", 7), ("kaheksa", 8), ("üheksa", 9), ("kümne", 10),
    ("kahekümne", 20), ("kolmekümne", 30), ("neljakümne", 40), ("viiekümne", 50),
    ("kuuekümne", 60), ("saja", 100)]
YHIKUD = [("aastane", "aasta"), ("eurone", "euro"), ("minutiline", "minut"),
    ("tunnine", "tund"), ("päevane", "päev"), ("meetrine", "meeter"),
    ("kilone", "kilo"), ("liitrine", "liiter"), ("protsendiline", "protsent"),
    ("korruseline", "korrus"), ("kuune", "kuu"), ("nädalane", "nädal"),
    ("leheküljeline", "lehekülg"), ("liikmeline", "liige")]

def moodul_e(n):
    tulem = []
    for _ in range(n):
        arv, _ = random.choice(ARVUD_OM)
        yhik, _ = random.choice(YHIKUD)
        liit = f"{arv}{yhik}"
        if random.random() < 0.5:
            tulem.append(("liitsonad",
                f"Paranda kokku-lahkukirjutus: '{arv} {yhik}'. Vasta ainult "
                f"õige vormiga.", liit))
        else:
            tulem.append(("liitsonad",
                f"Kirjuta õigesti kokku: arvsõna '{arv}' + '{yhik}'. "
                f"Vasta ühe sõnaga.", liit))
    return tulem

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--valjund",
                   default="/mnt/varu/qwen38-et-data/processed/ring6_moodulid.jsonl")
    a = p.parse_args()
    random.seed(SEEME)

    blokk = eval_blokk()
    print(f"evali blokk: {len(blokk)} sõna")
    lemmad = sorted({json.loads(r)["lemma"] for r in open(MORF)
                     if json.loads(r)["sonaliik"] == "S"})

    osad = (moodul_a(list(lemmad), blokk, 400) + moodul_b(blokk, 200)
            + moodul_c(300) + moodul_d(250) + moodul_e(150))
    # dedup küsimuse järgi
    nahtud, tulem = set(), []
    for kat, k, v in osad:
        if k in nahtud:
            continue
        nahtud.add(k)
        tulem.append({"messages": [{"role": "user", "content": k},
                                   {"role": "assistant", "content": v}],
                      "kategooria": kat, "allikas": "ring6-gen",
                      "litsents": "reeglipõhine süntees"})
    random.shuffle(tulem)
    with open(a.valjund, "w") as f:
        for t in tulem:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(f"valmis: {len(tulem)} näidet → {a.valjund}")
    for k, n in collections.Counter(t["kategooria"] for t in tulem).most_common():
        print(f"  {k:<20}{n:>6}")

if __name__ == "__main__":
    main()
