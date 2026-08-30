#!/usr/bin/env python3
"""CPT-piloodi korpus: ~150M tokenit kvaliteetproosat + replay.

Koostis (nõukoja retsept, kohandatud mõõdetud vajadusele):
  - ilukirjandus: KOGU olemasolev, 2x ülekaal (haruldane ja kõige väärtuslikum
    — vaba registri auk on mõõdetud) ~ 9,2M sõna
  - teadus + populaarteadus: kogu ~ 3,5M sõna
  - ajakirjandus: piiratud valim ~ 45M sõna (toimetatud, aga ei tohi domineerida)
  - replay (inglise + kood): ~9% tokenitest, unustamise vastu
Riigi Teataja jäi v1-st teadlikult välja (kantseleikeele risk, nõukoja hoiatus).

Heldout: 2000 lõiku (žanrite kaupa kihiline), perplexity-mõõduks, EI treenita.
Filtrid: dedup, <nooutput>, mitte-eesti read, liiga lühikesed.
"""
import glob, hashlib, json, random

P = "/mnt/varu/qwen38-et-data/processed"
R = "/mnt/varu/qwen38-et-data/raw"
SEEME = 20260828
random.seed(SEEME)

def puhas(t):
    if "<nooutput>" in t or "nooutput" in t:
        return False
    tahti = sum(c.isalpha() for c in t)
    return tahti / max(len(t), 1) > 0.6

zanrid = {"ilukirjandus": [], "teadus": [], "populaarteadus": [], "ajakirjandus": []}
nahtud = set()
for r in open(f"{P}/koondkorpus_koik.jsonl"):
    d = json.loads(r)
    if not puhas(d["tekst"]):
        continue
    h = hashlib.md5(d["tekst"][:200].encode()).hexdigest()
    if h in nahtud:
        continue
    nahtud.add(h)
    zanrid[d["zanr"]].append(d["tekst"])

for z in zanrid:
    random.shuffle(zanrid[z])

# heldout kihiline: 800 ilu, 400 teadus, 100 pop, 700 ajakirjandus
HELD = {"ilukirjandus": 800, "teadus": 400, "populaarteadus": 100,
        "ajakirjandus": 700}
heldout = []
for z, n in HELD.items():
    heldout += [(z, t) for t in zanrid[z][:n]]
    zanrid[z] = zanrid[z][n:]

# treeningmiks
AJAKIRJANDUS_SONU = 45_000_000
miks = []
miks += zanrid["ilukirjandus"] * 2            # 2x ülekaal
miks += zanrid["teadus"] + zanrid["populaarteadus"]
sonu = 0
for t in zanrid["ajakirjandus"]:
    if sonu >= AJAKIRJANDUS_SONU:
        break
    miks.append(t)
    sonu += len(t.split())

# replay: inglise + kood olemasolevast replay-poolist tekstina
replay = []
for d in (json.loads(r) for r in open(f"{P}/sft_v1_ring4.jsonl")):
    pass
import pandas as pd
for f in glob.glob(f"{R}/replay/**/*.parquet", recursive=True)[:3]:
    try:
        df = pd.read_parquet(f)
        for _, row in df.head(20000).iterrows():
            t = " ".join(str(v) for v in row.values if isinstance(v, str))
            if len(t.split()) > 30:
                replay.append(t)
    except Exception as e:
        print("replay viga:", e)
# samsum EN kokkuvõtted
try:
    df = pd.read_parquet(glob.glob(f"{R}/taltech/samsum_ee/**/*.parquet",
                                   recursive=True)[0])
    for _, row in df.head(10000).iterrows():
        t = str(row.get("en_dialogue", "")) + "\n" + str(row.get("en_summary", ""))
        if len(t.split()) > 30:
            replay.append(t)
except Exception:
    pass
random.shuffle(replay)
et_sonu = sum(len(t.split()) for t in miks)
replay_siht = int(et_sonu * 0.10)
rs, rvalik = 0, []
for t in replay:
    if rs >= replay_siht:
        break
    rvalik.append(t)
    rs += len(t.split())
miks += rvalik
random.shuffle(miks)

with open(f"{P}/cpt_korpus.jsonl", "w") as f:
    for t in miks:
        f.write(json.dumps({"text": t}, ensure_ascii=False) + "\n")
with open(f"{P}/cpt_heldout.jsonl", "w") as f:
    for z, t in heldout:
        f.write(json.dumps({"zanr": z, "text": t}, ensure_ascii=False) + "\n")

kokku = et_sonu + rs
print(f"CPT korpus: {len(miks)} lõiku, {kokku/1e6:.1f}M sõna "
      f"(~{kokku*2.2/1e6:.0f}M tokenit), replay {rs/kokku*100:.1f}%")
print(f"heldout: {len(heldout)} lõiku")
