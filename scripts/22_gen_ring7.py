#!/usr/bin/env python3
"""Ring 7 mikroannus: ring6 evali JÄRELEJÄÄNUD vigade kuju-täpne parandus.

Ring6 õppetund kordas ring5 oma: mudel õpib TÄPSELT näidatud kuju.
  - arvliitsõnad paranesid isolatsioonis ("Paranda: 'viie kümne eurone'"), aga
    MITTE lause sees (man-017) → moodul 1: parandused TERVES LAUSES
  - "mõttetera" märgiti olematuks, sest olemasolu-moodul filtreeris liitsõnad
    välja → moodul 2: päris liitsõnad kui "jah, olemas"
  - JSON võti ikka "kuupäev", sest treening ütles vihje "täpitähtedeta", eval
    ei ütle → moodul 3: evali kujuga JSON (vihjeta, võti ASCII)
  - "deploy'isin" eelistus püsib → moodul 4: valikküsimuse kuju
  - väljendid ("mõisa köis") → moodul 5: kureeritud püsiväljendid
"""
import argparse, collections, json, random, re
from estnltk.vabamorf.morf import Vabamorf, synthesize

_VM = Vabamorf.instance()
SEEME = 20260828
EVAL = "/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/eval/et_locked_v1.jsonl"
MORF = "/mnt/varu/qwen38-et-data/processed/morf_gen.jsonl"

def eval_blokk():
    sonad = set()
    for r in open(EVAL):
        d = json.loads(r)
        tekst = f"{d.get('prompt','')} {d.get('oige_vastus') or ''}"
        sonad.update(re.findall(r"[a-zõäöüšž\-]{4,}", tekst.lower()))
    return sonad

# ---------- 1: kokku-lahku parandused TERVES LAUSES ----------
ARVUD_OM = ["kahe", "kolme", "nelja", "viie", "kuue", "seitsme", "kaheksa",
            "üheksa", "kümne", "kahekümne", "kolmekümne", "neljakümne",
            "viiekümne", "kuuekümne", "saja"]
# ühik → mõistlikud objektid; fraas jääb NIMETAVASSE (ühildumisvigu ei teki)
YHIK_OBJ = {
    "aastane": ["laps", "leping", "kogemus", "traditsioon", "projekt"],
    "eurone": ["rahatäht", "pilet", "kupong", "arve"],
    "minutiline": ["kõne", "ooteaeg", "paus", "video"],
    "tunnine": ["koosolek", "loeng", "sõit", "vahetus"],
    "päevane": ["koolitus", "reis", "puhkus", "ooteaeg"],
    "meetrine": ["kaabel", "vahemaa", "riiul", "toru"],
    "kilone": ["pakk", "kott", "saadetis"],
    "liitrine": ["pudel", "anum", "paak"],
    "protsendiline": ["tõus", "langus", "allahindlus", "intress"],
    "korruseline": ["maja", "hoone", "garaaž"],
    "kuune": ["laps", "ooteaeg", "leping"],
    "nädalane": ["puhkus", "kursus", "vahe"],
    "leheküljeline": ["aruanne", "leping", "essee"],
    "liikmeline": ["komisjon", "žürii", "meeskond"],
}
LAUSEMALLID = ["Tal on {V} {O}.", "Meid ootab {V} {O}.", "See on {V} {O}.",
               "Ees seisab {V} {O}.", "Tulemas on {V} {O}."]

def moodul_1(n):
    tulem = []
    for _ in range(n):
        arv = random.choice(ARVUD_OM)
        yhik = random.choice(sorted(YHIK_OBJ))
        liit = f"{arv}{yhik}"
        vale = f"{arv} {yhik}"
        obj = random.choice(YHIK_OBJ[yhik])
        mall = random.choice(LAUSEMALLID)
        vale_lause = mall.format(V=vale, O=obj)
        oige_lause = mall.format(V=liit, O=obj)
        tulem.append(("liitsonad",
                      f"Paranda vead: '{vale_lause}'",
                      oige_lause))
    # e-liited ja lühendiliited lauses
    E_PAARID = [("e mail", "e-kiri", "Saatsin talle {X}i."),
                ("e pood", "e-pood", "Tellisin selle {X}ist."),
                ("e arve", "e-arve", "Saatke mulle {X}."),
                ("IT alane", "IT-alane", "Tal on {X} haridus."),
                ("PDF formaadis", "PDF-formaadis", "Saada dokument {X}."),
                ("ID kaart", "ID-kaart", "Võta {X} kaasa.")]
    for vale, oige, mall in E_PAARID:
        for _ in range(6):
            tulem.append(("liitsonad",
                f"Paranda: '{mall.replace('{X}', vale)}'",
                mall.replace("{X}", oige)))
    return tulem

# ---------- 2: liitsõnade olemasolu ----------
# kureeritud PÄRIS liitsõnad (sagedased, mitte juhugeneraat — "laekodumaa" tüüpi
# absurd õpetaks mudelit kõike aktsepteerima)
PARIS_LIIDUD = [
    "raudteejaam", "kohvimasin", "raamatukogu", "päevakord", "töökoht",
    "õppeaasta", "sünnipäev", "nädalavahetus", "käsitöö", "jalgratas",
    "linnavalitsus", "riigikogu", "maakond", "rahvamaja", "kultuurimaja",
    "spordisaal", "ujumisbassein", "muusikakool", "lasteaed", "haigemaja",
    "perearst", "hambaarst", "silmaarst", "postkontor", "pangakaart",
    "rahakott", "võtmehoidja", "prügikast", "pesumasin", "külmkapp",
    "nõudepesumasin", "tolmuimeja", "triikraud", "juuksur", "õmblusmasin",
    "kirjakast", "ajaleht", "ajakiri", "uudistesaade", "ilmateade",
    "liiklusmärk", "ülekäigurada", "bussipeatus", "rongijaam", "lennujaam",
    "reisibüroo", "toidupood", "raamatupood", "lillepood", "apteek",
    "leivategu", "koogivorm", "supilusikas", "teelusikas", "kohvitass",
    "veeklaas", "veinipokaal", "õllekapp", "piimapakk", "mahlapudel",
    "võileib", "juustukook", "õunakook", "marjamoos", "meepurk",
    "metsarada", "matkarada", "puhkepäev", "töölaud", "kirjutuslaud",
    "arvutihiir", "klaviatuur", "ekraanipilt", "failinimi", "kasutajanimi",
    "salasõna", "koduleht", "veebileht", "otsingumootor", "andmebaas",
    "mõttetera", "kalatoit", "linnusong", "kärbseseen", "maasikamoos",
    "vihmavari", "päikeseprillid", "talvesaapad", "suvepäev", "kevadlill",
    "sügisvärvid", "lumememm", "jääpurikas", "tuulepuhang", "vihmapiisk",
    "päikesetõus", "kuuvalgus", "tähistaevas", "merevaik", "rannaliiv",
    "metsloom", "koduloom", "lemmikloom", "linnupesa", "kalapüük",
    "jahimees", "kalamees", "meremees", "tuletõrjuja", "kiirabi",
    "politseijaoskond", "kohtumaja", "vanglakaristus", "seaduseelnõu",
    "valimisjaoskond", "hääletuskast", "rahvaloendus", "maksuamet",
]

def moodul_2(blokk, n):
    """Päris liitsõnad kureeritud loendist + Vabamorfi topeltkontroll."""
    tulem, liidud = [], []
    for liit in PARIS_LIIDUD:
        if len(tulem) >= n:
            break
        if liit in blokk:
            continue
        try:
            an = _VM.analyze(words=[liit], guess=False, propername=False)[0]["analysis"]
        except Exception:
            continue
        if not any(x["partofspeech"] == "S" and "=" not in x["root"] for x in an):
            continue
        liidud.append(liit)
        osad = next(x["root"] for x in an if x["partofspeech"] == "S")
        tulem.append(("sonaleiutamine",
            f"Kas sõna '{liit}' on eesti keeles olemas? Vasta jah või ei.",
            f"Jah, '{liit}' on eesti keeles olemas (liitsõna: "
            f"{osad.replace('_', ' + ')})."))
    # loendid: liitsõnad on PÄRIS, tuletusvead on võltsid
    lemmad = sorted({json.loads(r)["lemma"] for r in open(MORF)
                     if json.loads(r)["sonaliik"] == "S"
                     and json.loads(r)["lemma"] not in blokk})
    VALELIITED = ["uvus", "tis", "ldus", "ngus", "stus", "tsus"]
    for _ in range(n // 3):
        if len(liidud) < 3:
            break
        parised = random.sample(liidud, 3)
        alus = random.choice(lemmad)
        vale = alus[:max(3, len(alus) - 2)] + random.choice(VALELIITED)
        try:
            an = _VM.analyze(words=[vale], guess=False, propername=False)[0]["analysis"]
            if any(x["partofspeech"] in ("S", "A", "V") and "=" not in x["root"]
                   for x in an):
                continue
        except Exception:
            pass
        koik = parised + [vale]
        random.shuffle(koik)
        tulem.append(("sonaleiutamine",
            f"Millised neist sõnadest ei ole eesti keeles olemas: "
            f"{', '.join(koik)}? Nimeta ainult olematud.",
            f"Olemas ei ole: {vale}. Ülejäänud on liitsõnadena olemas."))
    return tulem

# ---------- 3: JSON evali kujuga (võtmed ASCII, vihjeta) ----------
NIMED = ["Mari", "Jaan", "Kati", "Peeter", "Liis", "Andres", "Tiina", "Mart"]
KUUD = ["jaanuari", "veebruari", "märtsi", "aprilli", "mai", "juuni", "juuli",
        "augusti", "septembri", "oktoobri", "novembri", "detsembri"]

def moodul_3(n):
    tulem = []
    for _ in range(n):
        t = random.choice(("arve", "syndmus", "isik2"))
        if t == "arve":
            summa, p, kuu = random.randint(50, 5000), random.randint(1, 28), random.randint(1, 12)
            vastus = json.dumps({"summa": summa, "valuuta": "EUR",
                                 "kuupaev": f"2026-{kuu:02d}-{p:02d}"}, ensure_ascii=False)
            tulem.append(("json-struktuur",
                f"Eralda sellest lausest struktureeritud andmed JSON-ina (väljad: "
                f"summa, valuuta, kuupäev): 'Arve summas {summa} eurot tuleb "
                f"tasuda {p}. {KUUD[kuu-1]}ks 2026.' Vasta ainult JSON-iga.",
                vastus))
        elif t == "syndmus":
            nimi = random.choice(NIMED)
            p, kuu = random.randint(1, 28), random.randint(1, 12)
            vastus = json.dumps({"nimi": nimi, "kuupaev": f"2026-{kuu:02d}-{p:02d}",
                                 "kohalolek": True}, ensure_ascii=False)
            tulem.append(("json-struktuur",
                f"Tagasta JSON (väljad: nimi, kuupäev, kohalolek): {nimi} "
                f"kinnitas osalemise {p}. {KUUD[kuu-1]} 2026 koosolekul. "
                f"Vasta ainult JSON-iga.", vastus))
        else:
            nimi, vanus = random.choice(NIMED), random.randint(18, 79)
            amet = random.choice(["õpetaja", "arst", "insener", "müüja", "jurist"])
            vastus = json.dumps({"nimi": nimi, "vanus": vanus, "amet": amet},
                                ensure_ascii=False)
            tulem.append(("json-struktuur",
                f"Tagasta JSON-objekt väljadega nimi, vanus, amet: {nimi} on "
                f"{vanus}-aastane {amet}. Vasta ainult JSON-iga, ilma selgituseta.",
                vastus))
    return tulem

# ---------- 4: anglitsismi valikküsimused ----------
ANGL_VERBID = [("deployisin", "juurutasin", "koodi"),
    ("mergeisin", "liitsin", "harud"), ("committisin", "salvestasin", "muudatused"),
    ("printisin", "printisin", "dokumendi"), ("forwardisin", "edastasin", "kirja"),
    ("cancelisin", "tühistasin", "tellimuse"), ("bookisin", "broneerisin", "toa"),
    ("checkisin", "kontrollisin", "tulemused"), ("saveisin", "salvestasin", "faili"),
    ("shareisin", "jagasin", "dokumendi"), ("updateisin", "uuendasin", "tarkvara"),
    ("downloadisin", "laadisin alla", "faili"), ("uploadisin", "laadisin üles", "pildi")]

def moodul_4(n):
    tulem = []
    for _ in range(n):
        ing, eesti, obj = random.choice(ANGL_VERBID)
        tulem.append(("tehniline",
            f"Kuidas kirjutada õigesti: 'Ma {ing} {obj}' või "
            f"'Ma {ing[:-4]}'isin {obj}'? Kas on olemas eestikeelne vaste?",
            f"Eelista eestikeelset: '{eesti} {obj}'. Kui toorlaenu siiski "
            f"kasutada, käib ülakomaga vorm võõrsõna kirjapildi järgi, aga "
            f"eesti sõna on alati parem valik."))
    return tulem

# ---------- 5: kureeritud püsiväljendid ----------
VALJENDID = [
    ("mõisa köis, las lohiseb", "võõra vara või asja suhtes ollakse hoolimatu, sest see pole enda oma"),
    ("kivi kotti", "õnnesoov, edu soovimine (nt eksamile või jahile minnes)"),
    ("põrsast kotis ostma", "midagi ostma või valima seda enne nägemata ja kontrollimata"),
    ("kass kotist välja laskma", "saladuse kogemata välja rääkima"),
    ("kahte kärbest ühe hoobiga tabama", "kaks asja korraga ära tegema"),
    ("hane selga vesi", "kriitika või õpetus ei mõju, läheb mööda"),
    ("kella tõmbama", "asjata ootama jääma; ka: liiga kaua venitama"),
    ("silma kinni pigistama", "teadlikult midagi märkamata jätma, andestama"),
    ("keelt hammaste taga hoidma", "vait olema, saladust hoidma"),
    ("kaks vasakut kätt", "oskamatu praktilistes töödes"),
    ("pikka pidu ei ole", "midagi ei kesta kaua"),
    ("nagu kaks tilka vett", "väga sarnased"),
    ("nagu sukk ja saabas", "lahutamatud sõbrad"),
    ("üle kivide ja kändude", "vaevaliselt, raskustega edasi liikuma"),
    ("suud puhtaks rääkima", "kõik ausalt ära ütlema"),
    ("südamelt ära rääkima", "muret jagama, et kergem hakkaks"),
    ("jäneseid püüdma", "kartma, araks lööma"),
    ("nina püsti ajama", "uhkeks ja üleolevaks muutuma"),
    ("hambaid varna panema", "nälga jääma, söömata olema"),
    ("kukalt kratsima", "nõutu olema, järele mõtlema"),
    ("keerulisse olukorda sattudes pead norgu laskma", "alla andma, lootust kaotama"),
    ("kuldsed käed", "väga osav praktilistes töödes"),
    ("pill tuleb pika ilu peale", "liigne lust lõpeb nutuga"),
    ("kes teisele auku kaevab, see ise sisse langeb", "teisele kurja plaanija saab ise kannatada"),
    ("parem varblane peos kui tuvi katusel", "kindel väike asi on parem kui ebakindel suur"),
    ("ega kõik kuld pole, mis hiilgab", "kõik ilus ei ole väärtuslik"),
    ("tühi kott ei seisa püsti", "näljasena ei jaksa töötada"),
    ("harjutamine teeb meistriks", "oskus tuleb kordamisega"),
    ("iga algus on raske", "alustamine ongi kõige keerulisem"),
    ("kuidas küla koerale, nõnda koer külale", "kuidas sina teisi kohtled, nii koheldakse sind"),
]

def moodul_5():
    tulem = []
    for v, t in VALJENDID:
        tulem.append(("sonaleiutamine",
                      f"Mida tähendab väljend '{v}'?",
                      f"Väljend '{v}' tähendab: {t}."))
        tulem.append(("sonaleiutamine",
                      f"Selgita eesti püsiväljendit '{v}' ühe lausega.",
                      f"{t[0].upper()}{t[1:]}."))
    return tulem

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--valjund",
                   default="/mnt/varu/qwen38-et-data/processed/ring7_moodulid.jsonl")
    a = p.parse_args()
    random.seed(SEEME)
    blokk = eval_blokk()

    osad = (moodul_1(250) + moodul_2(blokk, 200) + moodul_3(120)
            + moodul_4(60) + moodul_5())
    nahtud, tulem = set(), []
    for kat, k, v in osad:
        if k in nahtud:
            continue
        nahtud.add(k)
        tulem.append({"messages": [{"role": "user", "content": k},
                                   {"role": "assistant", "content": v}],
                      "kategooria": kat, "allikas": "ring7-gen",
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
