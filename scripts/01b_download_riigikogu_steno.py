#!/usr/bin/env python3
"""Riigikogu stenogrammide allalaadija (ainult tekst, mitte heli).

Ametlik avaandmete API: https://api.riigikogu.ee/api/steno/verbatims
Viisakas: nädal korraga, paus iga päringu vahel, jätkatav (olemasolevad nädalad
jäetakse vahele). Väljund: data/raw/riigikogu-steno/steno-YYYY-Wnn.json
"""
import json, os, sys, time, urllib.request, urllib.error
from datetime import date, timedelta

OUT = "/mnt/varu/qwen38-et-data/raw/riigikogu-steno"
START = date(2015, 1, 1)   # XIII Riigikogu algus; varasem kontrollitakse eraldi
END = date(2026, 8, 22)
PAUS = 4.0                 # sekundit päringute vahel (API andis 429 kiirel järjestusel)
UA = "qwen38-et-teadusprojekt (kontakt: pertlomp@gmail.com; viisakas throttle)"

os.makedirs(OUT, exist_ok=True)

def fetch(url, retries=4):
    for k in range(retries):
        try:
            req = urllib.request.Request(url, headers={"accept": "application/json", "User-Agent": UA})
            return json.loads(urllib.request.urlopen(req, timeout=120).read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(30 * (k + 1))   # tagane rahulikult
                continue
            raise
        except Exception:
            if k == retries - 1:
                raise
            time.sleep(10)
    raise RuntimeError("429 ka pärast kordusi")

paev = START
n_ok = n_tyhi = n_viga = 0
while paev <= END:
    lopp = min(paev + timedelta(days=6), END)
    aasta, nadal, _ = paev.isocalendar()
    sihtfail = f"{OUT}/steno-{aasta}-W{nadal:02d}.json"
    if os.path.exists(sihtfail):
        paev = lopp + timedelta(days=1)
        continue
    url = (f"https://api.riigikogu.ee/api/steno/verbatims"
           f"?startDate={paev.isoformat()}&endDate={lopp.isoformat()}&lang=ET")
    try:
        andmed = fetch(url)
        if andmed:
            with open(sihtfail, "w") as f:
                json.dump(andmed, f, ensure_ascii=False)
            n_ok += 1
        else:
            # tühi nädal (istungeid polnud) — märgi tehtuks, et resume ei korduks
            with open(sihtfail, "w") as f:
                f.write("[]")
            n_tyhi += 1
    except Exception as e:
        n_viga += 1
        print(f"VIGA {paev}: {type(e).__name__}: {str(e)[:100]}", flush=True)
    if (n_ok + n_tyhi) % 20 == 0:
        print(f"seis: {paev} | salvestatud {n_ok}, tühje {n_tyhi}, vigu {n_viga}", flush=True)
    time.sleep(PAUS)
    paev = lopp + timedelta(days=1)

kokku = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
print(f"VALMIS: {n_ok} andmenädalat, {n_tyhi} tühja, {n_viga} viga, kokku {kokku/1e6:.0f} MB", flush=True)
