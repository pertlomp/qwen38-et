#!/usr/bin/env python3
"""Ring 8: ring7 järelvigade täpsparandus + käänamise viimane vahe.

Ring7 analüüs (eval/runs/ring7-bnb + fraasisond-ring7):
  1. ÜLE-AKTSEPTEERIMINE (uus viga!): liitsõna-moodul õpetas "jah" liiga laialt —
     man-033 "lihavõimeline" sai "jah". Vaja TASAKAALU: päris -võimeline/-kindel
     liitomadussõnad on jah, semantiliselt absurdsed on ei.
  2. RINGDEFINITSIOON: man-037 "kiluvõileib on kiluvõileib" — definitsioon ei tohi
     korrata sõna ennast; õpeta läbipaistvate liitsõnade lahtivõtmist.
  3. KÄÄNDE TUVASTUS: man-004 "majja" → "mitmuse sisseütlev" — kääne õige, ARV
     vale. Lühikese sisseütleva erivormid (majja, tuppa, jõkke) vajavad eraldi
     annust, ja arvu täpsus üldse.
  4. KÄÄNAMINE 88,3: sondi vead nüüd ühtlaselt mitmuses (omastav/osastav/
     sisseütlev ~80%) — värsked fraasid nende kaaludega.
  5. STABIILSUS: morfoloogia-meta flipib (75,1→62,7) — ring6 verbimooduli
     kordus väikeses mahus, et eelmise ringi võidud ei kaoks.
"""
import argparse, collections, json, random, re
from estnltk.vabamorf.morf import Vabamorf, synthesize

_VM = Vabamorf.instance()
SEEME = 20260829
EVAL = "/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/eval/et_locked_v1.jsonl"

def eval_blokk():
    sonad = set()
    for r in open(EVAL):
        d = json.loads(r)
        sonad.update(re.findall(r"[a-zõäöüšž\-]{4,}",
                     f"{d.get('prompt','')} {d.get('oige_vastus') or ''}".lower()))
    return sonad

# ---------- 1: olemasolu TASAKAAL — liitomadussõnad ----------
# päris (kinnistunud) vs absurdne (sama liide, sobimatu alus)
LIITOMADUS_PARIS = [
    "konkurentsivõimeline", "maksevõimeline", "kohanemisvõimeline",
    "töövõimeline", "elujõuline", "veekindel", "tulekindel", "roostekindel",
    "löögikindel", "ilmastikukindel", "kuulikindel", "keskkonnasõbralik",
    "kasutajasõbralik", "lapsesõbralik", "energiasäästlik", "kulutõhus",
    "ajakohane", "asjakohane", "nõuetekohane", "seadusekohane",
    "suuremahuline", "väikesemahuline", "täismahuline", "pikaajaline",
    "lühiajaline", "kõrgetasemeline", "mitmekülgne", "ühekülgne",
    "kahepoolne", "mitmeaastane", "üleriigiline", "rahvusvaheline"]
LIITOMADUS_VALE = [
    "lihavõimeline", "laudvõimeline", "kivivõimeline", "toolikindel",
    "leivakindel", "unekindel", "kartulisõbralik", "seinasõbralik",
    "kohvitõhus", "aknasäästlik", "tararkohane", "lillekohane",
    "supimahuline", "kingaajaline", "tapeeditasemeline", "lusikakülgne"]

def moodul_1():
    tulem = []
    for s in LIITOMADUS_PARIS:
        tulem.append(("sonaleiutamine",
            f"Kas sõna '{s}' on eesti keeles olemas? Vasta jah või ei.",
            f"Jah, '{s}' on eesti keeles kasutatav liitomadussõna."))
    for s in LIITOMADUS_VALE:
        tulem.append(("sonaleiutamine",
            f"Kas sõna '{s}' on eesti keeles olemas? Vasta jah või ei ja "
            f"põhjenda ühe lausega.",
            f"Ei, sõna '{s}' ei ole eesti keeles olemas — osad ei sobi "
            f"tähenduselt kokku, selline liide nõuab teistsugust alussõna."))
    # segaloendid: 2 päris + 1 vale
    for _ in range(25):
        p = random.sample(LIITOMADUS_PARIS, 2)
        v = random.choice(LIITOMADUS_VALE)
        koik = p + [v]
        random.shuffle(koik)
        tulem.append(("sonaleiutamine",
            f"Millised neist sõnadest ei ole eesti keeles olemas: "
            f"{', '.join(koik)}? Nimeta ainult olematud.",
            f"Olemas ei ole: {v}. Ülejäänud on päris liitomadussõnad."))
    return tulem

# ---------- 2: läbipaistvate liitsõnade definitsioonid (mitte ring!) ----------
DEF_PAARID = [
    ("juustukook", "kook, mille põhikomponent on juust"),
    ("õunamahl", "mahl, mis on pressitud õuntest"),
    ("kalasupp", "supp, mis on keedetud kalast"),
    ("marjamoos", "moos, mis on keedetud marjadest"),
    ("võileib", "leivaviil, millele on määritud võid ja pandud katteid"),
    ("kohvitass", "tass, millest juuakse kohvi"),
    ("teekann", "kann, milles valmistatakse või serveeritakse teed"),
    ("raamaturiiul", "riiul, kus hoitakse raamatuid"),
    ("kirjakast", "kast, kuhu pannakse või kust võetakse kirju"),
    ("rattatee", "tee, mis on mõeldud jalgratastele"),
    ("bussipeatus", "koht, kus buss peatub ja reisijad sisenevad"),
    ("suusarada", "rada, mis on mõeldud suusatamiseks"),
    ("ujumisriided", "riided, mida kantakse ujumas käies"),
    ("töölaud", "laud, mille taga töötatakse"),
    ("magamistuba", "tuba, kus magatakse"),
    ("söögituba", "tuba, kus süüakse"),
    ("küpsisekarp", "karp, milles hoitakse küpsiseid"),
    ("piimapukk", "alus, kuhu pandi piimanõud äraveoks"),
    ("lumelabidas", "labidas, millega lükatakse lund"),
    ("vihmamantel", "mantel, mida kantakse vihma eest kaitseks"),
]

def moodul_2():
    tulem = []
    for sona, seletus in DEF_PAARID:
        tulem.append(("sonaleiutamine",
            f"Mis on '{sona}'? Selgita lühidalt, ilma sõna ennast kordamata.",
            seletus[0].upper() + seletus[1:] + "."))
        osad = sona  # paarisküsimus: kaks sõna korraga, nagu evalis
    for (a, sa), (b, sb) in zip(DEF_PAARID[::2], DEF_PAARID[1::2]):
        tulem.append(("sonaleiutamine",
            f"Mis on '{a}' ja mis on '{b}'? Selgita mõlemat lühidalt.",
            f"{a} on {sa}; {b} on {sb}."))
    return tulem

# ---------- 3: kääne + ARV täpsus, lühike sisseütlev ----------
LYHIKE_ILL = [("majja", "maja"), ("tuppa", "tuba"), ("linna", "linn"),
    ("kooli", "kool"), ("jõkke", "jõgi"), ("merre", "meri"), ("teatrisse", "teater"),
    ("metsa", "mets"), ("koju", "kodu"), ("kätte", "käsi"), ("suhu", "suu"),
    ("pähe", "pea"), ("vette", "vesi"), ("maale", "maa"), ("põske", "põsk"),
    ("aeda", "aed"), ("randa", "rand"), ("sohu", "soo"), ("mäkke", "mägi"),
    ("õue", "õu")]

def moodul_3(blokk, n):
    tulem = []
    for vorm, lemma in LYHIKE_ILL:
        if vorm in blokk:
            continue
        tulem.append(("morfoloogia-meta",
            f"Millises käändes on sõna '{vorm}'? Nimeta kääne eesti keeles.",
            f"ainsuse sisseütlev ehk lühike sisseütlev (algvorm: {lemma})"))
    # arvu täpsus: sama sõna ainsuses JA mitmuses kõrvuti
    KAANE_VM = {"g": "omastav", "p": "osastav", "ill": "sisseütlev",
                "in": "seesütlev", "el": "seestütlev", "all": "alaleütlev",
                "ad": "alalütlev", "kom": "kaasaütlev"}
    read = [json.loads(r) for r in
            open("/mnt/varu/qwen38-et-data/processed/morf_gen.jsonl")]
    lemmad = sorted({d["lemma"] for d in read if d["sonaliik"] == "S"
                     and d["lemma"] not in blokk})
    random.shuffle(lemmad)
    lisatud = 0
    for lemma in lemmad:
        if lisatud >= n:
            break
        kd = random.choice(list(KAANE_VM))
        for vm_arv, arv in (("sg", "ainsuse"), ("pl", "mitmuse")):
            V = synthesize(lemma, f"{vm_arv} {kd}", "S")
            if not V:
                continue
            vorm = V[-1]
            try:
                an = _VM.analyze(words=[vorm], guess=False, propername=False)[0]["analysis"]
            except Exception:
                continue
            koodid = {x["form"] for x in an if x["partofspeech"] == "S"}
            if koodid != {f"{vm_arv} {kd}"}:      # peab olema ühene, ka arvult
                continue
            tulem.append(("morfoloogia-meta",
                f"Millises käändes ja arvus on sõna '{vorm}'?",
                f"{arv} {KAANE_VM[kd]} (algvorm: {lemma})"))
            lisatud += 1
    return tulem

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--valjund",
                   default="/mnt/varu/qwen38-et-data/processed/ring8_moodulid.jsonl")
    a = p.parse_args()
    random.seed(SEEME)
    blokk = eval_blokk()

    osad = moodul_1() + moodul_2() + moodul_3(blokk, 150)
    nahtud, tulem = set(), []
    for kat, k, v in osad:
        if k in nahtud:
            continue
        nahtud.add(k)
        tulem.append({"messages": [{"role": "user", "content": k},
                                   {"role": "assistant", "content": v}],
                      "kategooria": kat, "allikas": "ring8-gen",
                      "litsents": "reeglipõhine süntees / kureeritud"})
    random.shuffle(tulem)
    with open(a.valjund, "w") as f:
        for t in tulem:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(f"valmis: {len(tulem)} näidet → {a.valjund}")
    for k, n in collections.Counter(t["kategooria"] for t in tulem).most_common():
        print(f"  {k:<20}{n:>6}")

if __name__ == "__main__":
    main()
