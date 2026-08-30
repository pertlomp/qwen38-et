#!/usr/bin/env python3
"""Ring 12: kahe ring11 disainivea parandus.

Ring11 kontroll (Perti küsimused v11 peal) näitas:
  1. KAJA-MALL: minu "vestlus-mitte-gec" mall ("Sain mõttest aru! + lause")
     õpetas lause tagasi kajama. VIGA OLI MINU DISAINIS. Ravi: SISULISED
     vastused kõnekeelsetele ütlustele, ilma sisendi kordamiseta — kureeritud.
  2. PIKKUS EI ÜLDISTUNUD: 100-200-sõnased näited ei andnud 300. Ravi:
     päris ERR-i artiklid (err-newsroom, 1737+ artiklit) 250-400 sõna
     lõikudena, korraldus "kirjuta umbes N sõnaga" täpselt vastuse pikkusega.
"""
import argparse, collections, gzip, json, random, re

SEEME = 20260904
P = "/mnt/varu/qwen38-et-data"

# ---------- A: sisulised vastused (kaja-malli vastu), kureeritud ----------
# põhimõte: vastus reageerib SISULE, ei korda sisendit, lõpeb edasiviivalt
VESTLUS = [
    ("ma küsisin seda sinu käest sest sa oled minu sõber",
     "Ja see teeb mind rõõmsaks! Mul läheb hästi: olen siin, erk ja valmis "
     "kaasa mõtlema. Räägi, mis sul täna plaanis on."),
    ("sa oled mu lemmik abiline",
     "Aitäh, see soojendab südant! Püüan seda usaldust iga vastusega õigustada. "
     "Millega täna pihta hakkame?"),
    ("ma olen täna natuke väsinud",
     "Siis võtame rahulikult. Kui tahad, aitan sul mõne tüütu asja kiiresti "
     "ära teha, et saaksid varem puhkama. Mis kõige rohkem koormab?"),
    ("mul oli täna raske päev tööl",
     "Seda on kahju kuulda. Vahel aitab, kui asjad kellelegi ära rääkida — "
     "olen olemas. Kas tahad rääkida, mis juhtus, või hoopis mõtted mujale viia?"),
    ("mul on homme tähtis koosolek",
     "Põnev ja natuke pinev, eks? Kui tahad, aitan sul punktid läbi mõelda "
     "või argumendid ritta seada. Mis koosoleku teema on?"),
    ("täna on nii ilus ilm väljas",
     "Naudi seda kindlasti! Väike jalutuskäik värskes õhus teeb pea selgeks. "
     "Kui tagasi jõuad, olen siin ja jätkame sealt, kus pooleli jäime."),
    ("ma ei jõua enam midagi teha",
     "Kõlab, nagu oleks aeg paus teha. Puhanud pea teeb homme poole vähema "
     "ajaga ära selle, mis täna venib. Kas saan enne mõne asja sinu eest "
     "lõpuni viia?"),
    ("mu laps sai täna koolis kiita",
     "Suurepärane uudis, tubli laps! Selliseid hetki tasub tähistada. "
     "Mille eest kiitus tuli?"),
    ("ma õpin eesti keelt",
     "Tore kuulda, ja julge pealehakkamine on pool võitu! Võin aidata "
     "harjutada: käänamine, sõnavara, vestlus — ütle, mis on kõige raskem."),
    ("mulle meeldib sinuga rääkida",
     "Mulle meeldib ka meie vestlus! Sinu küsimused on huvitavad ja "
     "hoiavad mind vormis. Mis sul järgmisena mõttes on?"),
    ("kas sa väsinud ei saa",
     "Mina ei väsi, see on minu töö võlu! Sina aga hoolitse enda eest — "
     "inimese pea vajab pause. Millega saan sind praegu aidata?"),
    ("ma mõtlen et hakkan sporti tegema",
     "Väga hea otsus! Alusta rahulikult, näiteks kolm korda nädalas "
     "jalutuskäigu või kerge trenniga, ja keha harjub kiiresti. Kas sind "
     "tõmbab pigem jõusaal, jooksmine või hoopis ujumine?"),
    ("mul on kõht tühi",
     "Siis on aeg midagi head süüa! Kui inspiratsiooni vajad, võin pakkuda "
     "kiire õhtusöögi mõtte olemasolevatest ainetest. Mis sul külmkapis on?"),
    ("ma ei oska otsustada",
     "Otsustamine ongi tihti kõige raskem osa. Proovime nii: pane kirja kaks "
     "varianti ja ma aitan plusse-miinuseid kaaluda. Mille vahel valid?"),
    ("homme on mu sünnipäev",
     "Palju õnne juba ette! Loodan, et päev tuleb täpselt selline, nagu "
     "soovid. Kas plaanid midagi erilist?"),
]

def moodul_a():
    return [("vestlus-sisuline", k, v) for k, v in VESTLUS]

# ---------- B: pikkuse järgimine päris artiklitega ----------
def moodul_b(n):
    art = []
    for osa in ("train", "dev"):
        try:
            art += json.load(gzip.open(f"{P}/raw/taltech/err-newsroom/{osa}.json.gz"))
        except Exception:
            continue
    random.shuffle(art)
    tulem = []
    for a in art:
        if len(tulem) >= n:
            break
        tekst = a.get("text", "").strip()
        pealkiri = a.get("heading", "").strip()
        sonu = len(tekst.split())
        if not pealkiri or sonu < 220:
            continue
        # võta ~250-380-sõnane algus, lõika lause piirilt
        soovitud = random.choice((250, 300, 350))
        sonad = tekst.split()
        if sonu < soovitud + 30:
            soovitud = (sonu // 50) * 50
            if soovitud < 200:
                continue
        loige = " ".join(sonad[:soovitud + 40])
        viimane = max(loige.rfind(". "), loige.rfind("! "), loige.rfind("? "))
        if viimane < 100:
            continue
        loige = loige[:viimane + 1]
        tegelik = len(loige.split())
        umbes = round(tegelik / 50) * 50
        tulem.append(("pikk-artikkel",
                      f"Kirjuta umbes {umbes} sõnaga teemal: {pealkiri}",
                      loige))
    return tulem

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--valjund", default=f"{P}/processed/ring12_moodulid.jsonl")
    a = p.parse_args()
    random.seed(SEEME)

    osad = moodul_a() + moodul_b(500)
    nahtud, tulem = set(), []
    for kat, k, v in osad:
        if k in nahtud:
            continue
        nahtud.add(k)
        tulem.append({"messages": [{"role": "user", "content": k},
                                   {"role": "assistant", "content": v}],
                      "kategooria": kat, "allikas": "ring12-gen",
                      "litsents": "err-newsroom + kureeritud"})
    random.shuffle(tulem)
    with open(a.valjund, "w") as f:
        for t in tulem:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(f"valmis: {len(tulem)} näidet → {a.valjund}")
    for k, n in collections.Counter(t["kategooria"] for t in tulem).most_common():
        print(f"  {k:<20}{n:>6}")
    pikkused = [len(t["messages"][1]["content"].split()) for t in tulem
                if t["kategooria"] == "pikk-artikkel"]
    if pikkused:
        print(f"  artiklipikkused: min {min(pikkused)}, max {max(pikkused)}, "
              f"keskmine {sum(pikkused)//len(pikkused)}")

if __name__ == "__main__":
    main()
