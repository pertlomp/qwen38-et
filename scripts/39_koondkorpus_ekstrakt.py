#!/usr/bin/env python3
"""Koondkorpuse TEI-failidest puhta teksti ekstraktimine.

Allikas: TÜ koondkorpus (cl.ut.ee, CC-BY-SA, Muischneki kinnitus 2026-08-26).
VIITAMISKOHUSTUS: iga kasutuse juures viide "Eesti keele koondkorpus,
Tartu Ülikooli arvutilingvistika uurimisrühm".

TEI kuju: <p> lõigud <s> lausetega, tokeniseeritud (tühik enne kirjavahemärki).
Detokeniseerime ja kirjutame lõigud jsonl-ina koos allika ja žanriga.
"""
import argparse, glob, json, os, re, zipfile

R = "/mnt/varu/qwen38-et-data/raw/koondkorpus"

# iga kaust: kõik zipid; žanr kausta järgi
ZANRID = {"eesti_ilukirjandus_1990": "ilukirjandus", "doktoritood": "teadus",
    "horisont": "populaarteadus", "luup": "ajakirjandus",
    "postimees": "ajakirjandus", "epl": "ajakirjandus",
    "ekspress": "ajakirjandus", "maaleht": "ajakirjandus",
    "laane_elu": "ajakirjandus", "kroonika": "ajakirjandus",
    "agraarteadus": "teadus", "arvutitehnika": "teadus", "eestiarst": "teadus"}
ALLIKAD = {}
for kaust, zanr in ZANRID.items():
    for z in sorted(glob.glob(f"{R}/{kaust}/*.zip")):
        # väldi topelt: kui on nii X.zip kui X_tei.zip, võta suurem/uuem TEI
        ALLIKAD[f"{kaust}/{os.path.basename(z)}"] = (z, zanr)

def detokeniseeri(t):
    t = re.sub(r"\s+([,.!?;:%)\]])", r"\1", t)
    t = re.sub(r"([(\[])\s+", r"\1", t)
    t = re.sub(r'\s+(["»])', r"\1", t)
    t = re.sub(r'(["«])\s+', r"\1", t)
    t = re.sub(r"\s+-\s*(\w)", r"-\1", t)   # "puzzle -romaan" → "puzzle-romaan"
    return re.sub(r"\s+", " ", t).strip()

def loigud_teifailist(sisu):
    for p in re.findall(r"<p>(.*?)</p>", sisu, re.S):
        if "<gap" in p or "<bibl" in p:
            continue
        laused = re.findall(r"<s>(.*?)</s>", p, re.S)
        if not laused:
            continue
        tekst = detokeniseeri(" ".join(re.sub(r"<[^>]+>", " ", l) for l in laused))
        if tekst:
            yield tekst

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--valjund",
                   default="/mnt/varu/qwen38-et-data/processed/koondkorpus_loigud.jsonl")
    p.add_argument("--min-sonu", type=int, default=25)
    a = p.parse_args()

    kokku = {}
    with open(a.valjund, "w") as f:
        for nimi, (zpath, zanr) in ALLIKAD.items():
            if not os.path.exists(zpath):
                print(f"puudub: {zpath}")
                continue
            n = sonu = 0
            with zipfile.ZipFile(zpath) as z:
                for fn in z.namelist():
                    if not fn.endswith(".xml") or "header" in fn.lower() \
                       or "/bin/" in fn:
                        continue
                    try:
                        sisu = z.read(fn).decode("utf-8", errors="replace")
                    except Exception:
                        continue
                    for lg in loigud_teifailist(sisu):
                        ns = len(lg.split())
                        if ns < a.min_sonu:
                            continue
                        f.write(json.dumps({
                            "tekst": lg, "sonu": ns, "zanr": zanr,
                            "allikas": f"koondkorpus-{nimi}", "fail": os.path.basename(fn),
                            "litsents": "CC-BY-SA (TÜ koondkorpus, viitamiskohustus)"},
                            ensure_ascii=False) + "\n")
                        n += 1
                        sonu += ns
            kokku[nimi] = (n, sonu)
            print(f"{nimi}: {n} lõiku, {sonu/1e6:.1f}M sõna", flush=True)
    print(f"→ {a.valjund}")

if __name__ == "__main__":
    main()
