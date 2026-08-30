#!/usr/bin/env python3
"""Skoorib eval-jooksu kontrollitava vastusega ülesanded automaatselt.

Rubriigi-ülesandeid (47) SIIN EI SKOORITA — need vajavad inimest või LLM-kohtunikku.
Automaatne skoor katab 153 ülesannet ja on mõeldud enne/pärast VÕRDLUSEKS,
mitte absoluutseks tõeks.

Kasutus: python 08_score.py --run baseline [--vordle cpt-10m]
"""
import argparse, json, os, re, unicodedata

EVAL = "/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/eval"

def norm(s):
    s = unicodedata.normalize("NFC", str(s)).lower().strip()
    s = re.sub(r"[*_`#]", "", s)                 # markdown maha
    s = re.sub(r"[—–\-]+", " ", s)               # kriipsud tühikuks ("nimetav — raamat")
    s = re.sub(r"\s+", " ", s)
    return s.strip(" .,:;!?\"'()")

def ilma_sulgudeta(s):
    """Õige vastuse sulud on valikuline täpsustus: 'sisseütlev (illatiiv)' → 'sisseütlev'."""
    return re.sub(r"\([^)]*\)", " ", str(s))

STOPP = {"on", "ja", "või", "kui", "ning", "ehk", "ka", "see", "mis", "kes"}

def osade_kate(vastus, oige):
    """Varutee: kas kõik õige vastuse sisulised sõnad esinevad vastuses?
    (Täppisstring kukub läbi, kui mudel sõnastab õige vastuse teises järjekorras —
    'algvõrre on hea' vs 'hea (algvõrre)'. Leitud 2026-08-23: Claude'i õiged
    vastused said 0.) Tagastab osakaalu 0..1."""
    v = norm(vastus)
    sonad = [w for w in norm(ilma_sulgudeta(oige)).replace("=", " ").split()
             if len(w) >= 3 and w not in STOPP]
    if not sonad: return None
    return sum(1 for w in set(sonad) if w in v) / len(set(sonad))

def sisaldab(vastus, oige):
    """Kas mudeli vastus sisaldab õiget vastust (või mõnda lubatud varianti)?"""
    v = norm(vastus)
    variandid = [norm(x) for x in re.split(r"[;|]", str(oige)) if norm(x)]
    return any(x and x in v for x in variandid)

def tapne_algus(vastus, oige):
    """Lühivastuse ülesannetel: kas vastus ALGAB õigega (mudel ei lobise)?"""
    v, o = norm(vastus), norm(oige)
    return v.startswith(o) or v == o

def loetelu_kate(vastus, oige):
    """Loetelu-ülesanne: mitu protsenti oodatud elementidest on vastuses."""
    v = norm(vastus)
    osad = [norm(x) for x in str(oige).split(",") if norm(x)]
    if not osad: return 0.0
    return sum(1 for o in osad if o in v) / len(osad)

def json_vordlus(vastus, oige):
    """JSON-ülesanded: parsi mõlemad ja võrdle SISU, mitte stringi.
    (String-võrdlus karistas kompaktset JSON-i {\"a\":1} vs {\"a\": 1} —
    leitud 2026-08-23 Sol-i jooksul, kõik vastused õiged, skoor 16,7%.)"""
    m = re.search(r"[\[{].*[\]}]", str(vastus), re.S)
    if not m: return None
    try:
        v = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    try:
        o = json.loads(str(oige))
    except json.JSONDecodeError:
        return None                      # õige vastus pole range JSON → tagasi stringiteele
    def norm(x):
        if isinstance(x, dict):
            # võtmete tähed normaliseeritakse (kuupaev/kuupäev on sama väli)
            return {unicodedata.normalize("NFC", k).lower().replace("ä","a"): norm(v)
                    for k, v in x.items()}
        if isinstance(x, list): return [norm(i) for i in x]
        if isinstance(x, str): return norm_s(x)
        return x
    return 1.0 if norm(v) == norm(o) else 0.0

def norm_s(s):
    return unicodedata.normalize("NFC", str(s)).lower().strip()

def skoori_kirje(k):
    """Tagastab (skoor 0..1, meetod) või None, kui pole automaatselt skooritav."""
    if k.get("tyyp") != "kontrollitav": return None
    vastus, oige = k.get("vastus", ""), k.get("oige_vastus")
    if not oige: return None
    kat = k.get("kategooria", "")

    # JSON-ülesanded: sisupõhine võrdlus enne stringiteed
    if kat in ("json-struktuur", "tooriistad") and str(oige).strip().startswith(("{", "[")):
        r = json_vordlus(vastus, oige)
        if r is not None:
            return r, "json-sisu"

    # Loetelu-tüüpi (käänete nimekiri) — osaline kate
    if "," in str(oige) and len(str(oige).split(",")) >= 5:
        return loetelu_kate(vastus, oige), "loetelu-kate"
    # Käänamine ja lühivastused — sisaldumine (mudel võib lisada selgituse)
    if kat in ("kaanamine", "morfoloogia-meta", "liitsonad", "rektsioon",
               "sonaleiutamine", "tehniline", "json-struktuur", "tooriistad"):
        if sisaldab(vastus, oige):
            return 1.0, "sisaldumine"
        # varutee: sisuliste sõnade kate (≥90% = õige teises sõnastuses)
        k = osade_kate(vastus, oige)
        if k is not None and k >= 0.9:
            return 1.0, "osade-kate"
        return 0.0, "sisaldumine"
    # Grammatikaparandus — sõnatasandi kattuvus õige lausega
    if kat == "grammatikaparandus":
        v, o = set(norm(vastus).split()), set(norm(oige).split())
        if not o: return None
        return len(v & o) / len(o), "sõnakate"
    # Ülejäänud kontrollitavad, millel on vabas vormis õige vastus
    if kat in ("regressioon-kood",):
        return None       # koodi ei skoori stringivõrdlusega
    return (1.0 if sisaldab(vastus, oige) else 0.0), "sisaldumine"

def skoori_jooks(run):
    tee = f"{EVAL}/runs/{run}/vastused.jsonl"
    kirjed = [json.loads(r) for r in open(tee, encoding="utf-8") if r.strip()]
    kat = {}
    skooritud = 0
    for k in kirjed:
        r = skoori_kirje(k)
        if r is None: continue
        s, meetod = r
        skooritud += 1
        c = kat.setdefault(k["kategooria"], {"summa": 0.0, "n": 0, "meetod": meetod})
        c["summa"] += s; c["n"] += 1
    for c in kat.values():
        c["keskmine"] = round(c["summa"] / max(c["n"], 1), 3)
    kesk = sum(c["summa"] for c in kat.values()) / max(skooritud, 1)
    return kat, skooritud, kesk, len(kirjed)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--vordle", default=None, help="teine run_id võrdluseks")
    a = ap.parse_args()

    kat, n, kesk, kokku = skoori_jooks(a.run)
    kat2 = None
    if a.vordle:
        kat2, n2, kesk2, _ = skoori_jooks(a.vordle)

    print(f"\nJOOKS: {a.run}   (automaatselt skooritud {n}/{kokku} ülesannet)")
    print(f"ÜLDSKOOR: {kesk*100:.1f}%\n")
    if kat2:
        print(f"VÕRDLUS: {a.vordle} — üldskoor {kesk2*100:.1f}% "
              f"({(kesk2-kesk)*100:+.1f} pp)\n")
    pais = f"{'Kategooria':26} {'n':>4} {a.run[:12]:>10}"
    if kat2: pais += f" {a.vordle[:12]:>10} {'muutus':>8}"
    print(pais); print("-" * len(pais))
    for k in sorted(kat, key=lambda x: kat[x]["keskmine"]):
        rida = f"{k:26} {kat[k]['n']:>4} {kat[k]['keskmine']*100:>9.1f}%"
        if kat2 and k in kat2:
            d = (kat2[k]["keskmine"] - kat[k]["keskmine"]) * 100
            rida += f" {kat2[k]['keskmine']*100:>9.1f}% {d:>+7.1f}"
        print(rida)

    valjund = {"run": a.run, "uldskoor": round(kesk, 4), "skooritud": n,
               "kokku_ulesandeid": kokku, "kategooriad": kat}
    with open(f"{EVAL}/runs/{a.run}/skoor.json", "w", encoding="utf-8") as f:
        json.dump(valjund, f, ensure_ascii=False, indent=1)
    print(f"\n→ {EVAL}/runs/{a.run}/skoor.json")
    print("NB: 47 rubriigi-ülesannet vajavad eraldi inimhinnangut.")

if __name__ == "__main__":
    main()
