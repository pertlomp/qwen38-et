#!/usr/bin/env python3
"""Ehitab ring 4 andmestiku RING4-PLAAN.md järgi.

Eeldab: ring 3 on hinnatud (eval/runs/ring3-bnb/skoor.json olemas) ja
Vabamorfi generaator on jooksnud (processed/morf_gen.jsonl olemas).
"""
import glob, hashlib, json, os, random

PROC = "/mnt/varu/qwen38-et-data/processed"
RAW = "/mnt/varu/qwen38-et-data/raw"
EVAL = "/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/eval"
SEEME = 20260824
SIHT = 15_000_000
random.seed(SEEME)

from tokenizers import Tokenizer
TOK = Tokenizer.from_file("/mnt/varu/qwen38-et-data/tokenizer/tokenizer.json")
SYS = "Sa oled abivalmis assistent. Vasta loomulikus ja korrektses eesti keeles."

KAANDE_JARJEKORD = ["nimetav", "omastav", "osastav", "sisseütlev", "seesütlev",
                    "seestütlev", "alaleütlev", "alalütlev", "alaltütlev", "saav",
                    "rajav", "olev", "ilmaütlev", "kaasaütlev"]
HARVAD = {"rajav", "ilmaütlev", "olev", "sisseütlev"}

evalp = {json.loads(r)["prompt"].lower() for r in open(f"{EVAL}/et_locked_v1.jsonl", encoding="utf-8")}
leke = json.load(open(f"{EVAL}/leke_blokk.json", encoding="utf-8"))
LEKE_FRAASID = {x.lower() for x in leke.get("inflection_et", [])}

n = []
def L(k, v, kat, allikas, lits="puhas", sys=SYS):
    if not k or not v: return
    if str(k).lower() in evalp: return
    n.append({"messages": [{"role": "system", "content": sys},
                           {"role": "user", "content": str(k).strip()},
                           {"role": "assistant", "content": str(v).strip()}],
              "kategooria": kat, "allikas": allikas, "litsents": lits})

# ---- 1a. Käänamise kordus (kõik ring 3 käänamisnäited) ----
r3 = [json.loads(r) for r in open(f"{PROC}/sft_v1_ring3.jsonl", encoding="utf-8")]
korduskat = {"kaanamine", "grammatikaparandus", "morfoloogia-meta"}
kordused = [d for d in r3 if d["kategooria"] in korduskat]
# dedup (ring 3-s olid mõned juba korduses)
nahtud, uniq = set(), []
for d in kordused:
    h = hashlib.md5(json.dumps(d["messages"], ensure_ascii=False).encode()).hexdigest()
    if h in nahtud: continue
    nahtud.add(h); uniq.append(d)
n.extend(uniq)
print(f"kordused (käänamine+grammatika+meta): {len(uniq)}")

# ---- 1b. Vabamorfi süntees: harvad käänded ----
morf = []
if os.path.exists(f"{PROC}/morf_gen.jsonl"):
    morf = [json.loads(r) for r in open(f"{PROC}/morf_gen.jsonl", encoding="utf-8")]
harvad_n = 0
for d in morf:
    if d["kaane"] not in HARVAD: continue
    if d["lemma"].lower() in LEKE_FRAASID: continue
    L(f"Pane sõna '{d['lemma']}' {d['arv']} {d['kaane']} käändesse. Vasta ainult vormiga.",
      d["vorm"], "kaanamine", "vabamorf-syntees (ring-kontrollitud)")
    harvad_n += 1
    if harvad_n >= 6000: break
print(f"+ Vabamorfi harvad käänded: {harvad_n}")

# ---- 1c. Täistabelid (14 käänet korraga) ----
tabelid = {}
for d in morf:
    if d["arv"] != "ainsuse": continue
    tabelid.setdefault(d["lemma"], {})[d["kaane"]] = d["vorm"]
taisi = 0
lemmad = list(tabelid.keys()); random.shuffle(lemmad)
for lemma in lemmad:
    vormid = tabelid[lemma]
    if len([k for k in KAANDE_JARJEKORD if k in vormid]) < 14: continue
    if lemma.lower() in LEKE_FRAASID: continue
    vastus = ", ".join(f"{k} {vormid[k]}" for k in KAANDE_JARJEKORD)
    L(f"Kääna sõna '{lemma}' kõigis 14 käändes ainsuses. "
      f"Vasta loeteluna: käände nimi ja vorm.",
      vastus, "morfoloogia-meta", "vabamorf-syntees (täistabel)")
    taisi += 1
    if taisi >= 1500: break
print(f"+ täistabelid: {taisi}")

# ---- 2. Viis väikest kategooriat: ring 3 skoori järgi ----
try:
    s3 = json.load(open(f"{EVAL}/runs/ring3-bnb/skoor.json"))["kategooriad"]
    s2 = json.load(open(f"{EVAL}/runs/ring2-bnb/skoor.json"))["kategooriad"]
except FileNotFoundError:
    s3 = s2 = {}
viis = [json.loads(r) for r in open(f"{PROC}/viis_kategooriat.jsonl", encoding="utf-8")]
grupid = {}
for d in viis: grupid.setdefault(d["kategooria"], []).append(d)
for kat, naited in grupid.items():
    edenes = (s3.get(kat, {}).get("keskmine", 0) - s2.get(kat, {}).get("keskmine", 0)) >= 0.05
    kordi = max(1, round((400 if edenes else 800) / len(naited)))
    for _ in range(kordi): n.extend(dict(d) for d in naited)
    print(f"+ {kat}: {'edenes' if edenes else 'EI edenenud'} → {len(naited)}×{kordi}")

# ---- 3. Värske materjal (kasutamata basseinist) ----
kasutatud = set()
for f in [f"{PROC}/sft_v1_10m.jsonl", f"{PROC}/sft_v1_ring2.jsonl", f"{PROC}/sft_v1_ring3.jsonl"]:
    for r in open(f, encoding="utf-8"):
        d = json.loads(r)
        kasutatud.add(hashlib.md5((d["messages"][1]["content"] + d["messages"][-1]["content"]).encode()).hexdigest())
def varske(k, v, kat, allikas):
    h = hashlib.md5((str(k) + str(v)).encode()).hexdigest()
    if h in kasutatud: return False
    kasutatud.add(h); L(k, v, kat, allikas); return True
d = json.load(open(f"{RAW}/taltech/qa_broadcast_conv_et/data.json", encoding="utf-8"))
sv = 0
for x in d.get("questions_and_answers", []):
    if x.get("question") and x.get("answer") and 60 < len(x["answer"]) < 4000:
        if varske(x["question"], x["answer"], "saatevestlus-qa", "TalTechNLP/qa_broadcast_conv_et"):
            sv += 1
    if sv >= 12000: break
print(f"+ värsked saatevestlused: {sv}")
ss = 0
for tee in glob.glob(f"{RAW}/taltech/word_meanings_et/*.jsonl"):
    if ".cache" in tee: continue
    for r in open(tee, encoding="utf-8"):
        try: x = json.loads(r)
        except: continue
        w, defi = x.get("words"), x.get("definition")
        if not w or not defi: continue
        s = w[0] if isinstance(w, list) else w
        sel = defi[0] if isinstance(defi, list) else defi
        if s and sel and len(str(sel)) > 8:
            if varske(f"Mida tähendab eestikeelne sõna '{s}'? Selgita lühidalt.", str(sel),
                      "sonatahendus", "TalTechNLP/word_meanings_et"):
                ss += 1
        if ss >= 10000: break
    if ss >= 10000: break
print(f"+ värsked sõnaseletused: {ss}")

# ---- 4. Replay ----
import pyarrow.parquet as pq
rep = 0
for f in glob.glob(f"{RAW}/taltech/samsum_ee/data/train-*.parquet"):
    for b in pq.ParquetFile(f).iter_batches(batch_size=2000):
        for x in b.to_pylist():
            if x.get("en_dialogue") and x.get("en_summary") and rep < 3500:
                if varske(f"Summarize this conversation briefly:\n\n{x['en_dialogue']}",
                          x["en_summary"], "replay-inglise", "TalTechNLP/samsum_ee (en)"):
                    n[-1]["messages"][0]["content"] = "You are a helpful assistant."
                    rep += 1
for f in glob.glob(f"{RAW}/replay/**/*.parquet", recursive=True):
    if ".cache" in f: continue
    for b in pq.ParquetFile(f).iter_batches(batch_size=2000):
        for x in b.to_pylist():
            if x.get("prompt") and x.get("completion") and rep < 7000:
                if varske(str(x["prompt"]), str(x["completion"]), "replay-kood", "CodeAlpaca-20k"):
                    n[-1]["messages"][0]["content"] = "You are a helpful coding assistant."
                    n[-1]["litsents"] = "hall-gpt35"
                    rep += 1
print(f"+ replay: {rep}")

# ---- Tokeniseeri, piira, kirjuta ----
for d in n:
    d["tokeneid"] = len(TOK.encode("\n".join(m["content"] for m in d["messages"])).ids)
random.shuffle(n)
valitud, jooksev = [], 0
PRIO = {"kaanamine", "morfoloogia-meta", "grammatikaparandus"}
for d in n:
    if d["kategooria"] in PRIO: valitud.append(d); jooksev += d["tokeneid"]
for d in n:
    if d["kategooria"] in PRIO: continue
    if jooksev + d["tokeneid"] > SIHT: continue
    valitud.append(d); jooksev += d["tokeneid"]
random.shuffle(valitud)
with open(f"{PROC}/sft_v1_ring4.jsonl", "w", encoding="utf-8") as f:
    for d in valitud: f.write(json.dumps(d, ensure_ascii=False) + "\n")
kat = {}
for d in valitud: kat[d["kategooria"]] = kat.get(d["kategooria"], 0) + 1
rept = sum(d["tokeneid"] for d in valitud if d["kategooria"].startswith("replay"))
print(f"\nRING 4: {len(valitud)} näidet, {jooksev/1e6:.2f}M tokenit, replay {rept/jooksev*100:.1f}%")
print(json.dumps({x: kat[x] for x in sorted(kat, key=lambda y: -kat[y])}, ensure_ascii=False))
