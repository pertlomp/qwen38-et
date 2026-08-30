#!/usr/bin/env python3
"""Ehitab SFT-andmestiku PÄRIS inimeste tekstist ja kõnest.

Perti reegel (2026-08-22): kasutame enne kõike inimeste päris kõnet ja teksti.
Sünteetiline/reeglipõhine genereerimine tuleb alles siis, kui näeme vajadust.
Seetõttu on Vabamorfi generaator (03_gen_morfoloogia.py) siin VÄLJAS.

Kõik paarid on tekstis JUBA OLEMAS — me ei genereeri neid, vaid ekstraheerime:
  - ERR videouudis: päris kõne (transcript) ↔ ajakirjaniku kirjutatud artikkel/pealkiri
  - saatevestlused: päris küsimus ↔ päris vastus
  - grammatikakorpus: inimese vigane lause ↔ toimetaja parandus
  - dialoogid: päris vestlus ↔ inimese kirjutatud kokkuvõte

Väljund: data/processed/sft_v1.jsonl (kõik) + sft_v1_10m.jsonl (esimene ring)
"""
import glob, hashlib, json, os, random, re

RAW = "/mnt/varu/qwen38-et-data/raw"
OUT = "/mnt/varu/qwen38-et-data/processed"
EVAL = "/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/eval"
SEEME = 20260822
RING1_TOKENEID = 10_000_000
random.seed(SEEME)

from tokenizers import Tokenizer
TOK = Tokenizer.from_file("/mnt/varu/qwen38-et-data/tokenizer/tokenizer.json")
SYS_ET = "Sa oled abivalmis assistent. Vasta loomulikus ja korrektses eesti keeles."

leke = json.load(open(f"{EVAL}/leke_blokk.json", encoding="utf-8"))
LEKE_INF = set(leke.get("inflection_et", []))
LEKE_GEC = set(leke.get("grammar_et", [])) | set(leke.get("grammar2_et", []))

naited = []
def lisa(kasutaja, vastus, kategooria, allikas, litsents, system=SYS_ET, min_pikkus=15):
    # min_pikkus=1 lühivastuse ülesannetel (käändevorm "raamatu" on 7 tähte —
    # 15-tähemärgiline filter viskas neist veerandi vaikselt välja).
    if not kasutaja or not vastus: return
    kasutaja, vastus = str(kasutaja).strip(), str(vastus).strip()
    if len(vastus) < min_pikkus: return
    naited.append({"messages": [{"role": "system", "content": system},
                                {"role": "user", "content": kasutaja},
                                {"role": "assistant", "content": vastus}],
                   "kategooria": kategooria, "allikas": allikas, "litsents": litsents})

def parquet_read(muster, veerud=None):
    import pyarrow.parquet as pq
    read = []
    for f in glob.glob(muster, recursive=True):
        if ".cache" in f: continue
        try:
            for b in pq.ParquetFile(f).iter_batches(batch_size=2000, columns=veerud):
                read += b.to_pylist()
        except Exception as e:
            print(f"  ! {os.path.basename(f)}: {e}")
    return read

# ===== 1. PÄRIS KÕNE: ERR videouudised (kõne ↔ ajakirjaniku tekst) =====
def err_video(maht=8000):
    tee = f"{RAW}/taltech/err-video-news-transcribed/train.jsonl"
    if not os.path.exists(tee): return
    read = []
    with open(tee, encoding="utf-8") as f:
        for r in f:
            try: d = json.loads(r)
            except: continue
            read.append(d)
    n = 0
    for d in read:
        tr, head = (d.get("transcript") or "").strip(), (d.get("heading") or "").strip()
        lead, tekst = (d.get("leadin") or "").strip(), (d.get("text") or "").strip()
        if not tr or len(tr) < 200: continue
        tr_l = tr[:6000]
        if head and len(head) > 15:
            lisa(f"Kirjuta sellele uudislõigule pealkiri:\n\n{tr_l}", head,
                 "parisk6ne-pealkiri", "TalTechNLP/err-video-news", "puhas"); n += 1
        if lead and len(lead) > 60:
            lisa(f"Kirjuta sellele uudislõigule lühike juhtlõik:\n\n{tr_l}", lead,
                 "parisk6ne-juhtl6ik", "TalTechNLP/err-video-news", "puhas"); n += 1
        if tekst and len(tekst) > 200 and len(tekst) < 4000:
            # KÕIGE VÄÄRTUSLIKUM: suuline kõne → korrektne kirjalik uudistekst
            lisa(f"Vormista see uudistesaate lõik korrektseks kirjalikuks uudistekstiks:"
                 f"\n\n{tr_l}", tekst,
                 "k6ne-tekstiks", "TalTechNLP/err-video-news", "puhas"); n += 1
        if n >= maht: break
    print(f"ERR videouudised (päris kõne): {n}")

# ===== 2. PÄRIS VESTLUS: saatevestluste küsimused-vastused =====
def qa_saated(maht=12000):
    tee = f"{RAW}/taltech/qa_broadcast_conv_et/data.json"
    if not os.path.exists(tee): return
    d = json.load(open(tee, encoding="utf-8"))
    paarid = d.get("questions_and_answers", []) if isinstance(d, dict) else d
    sobivad = [(x["question"], x["answer"]) for x in paarid
               if x.get("question") and x.get("answer") and 60 < len(x["answer"]) < 4000]
    for q, a in random.sample(sobivad, min(maht, len(sobivad))):
        lisa(q, a, "saatevestlus-qa", "TalTechNLP/qa_broadcast_conv_et", "puhas")
    print(f"saatevestlused (päris QA): {min(maht, len(sobivad))} / basseinis {len(sobivad)}")

# ===== 3. PÄRIS PARANDUSED: inimese viga ↔ toimetaja parandus =====
def grammatika():
    paarid = []
    for tee, nimi in [(f"{RAW}/taltech/grammar_et/grammar_l2_train.jsonl", "grammar_et"),
                      (f"{RAW}/taltech/grammar_et/grammar_l2_test.jsonl", "grammar_et"),
                      (f"{RAW}/taltech/grammar2_et/grammar_l1.jsonl", "grammar2_et")]:
        if not os.path.exists(tee): continue
        with open(tee, encoding="utf-8") as f:
            for r in f:
                try: d = json.loads(r)
                except: continue
                o, c = d.get("original"), d.get("correct")
                if not (o and c) or o == c or o in LEKE_GEC: continue
                if not (20 < len(o) < 800): continue
                paarid.append((o, c, nimi))
    for o, c, nimi in paarid:      # KÕIK — see on kõige sihitum materjal
        lisa(f"Paranda selle teksti keelevead. Vasta ainult parandatud tekstiga:\n\n{o}",
             c, "grammatikaparandus", f"TalTechNLP/{nimi}", "puhas")
    print(f"grammatikaparandused (kõik): {len(paarid)}")

# ===== 4. PÄRIS KÄÄNAMINE (TalTechi käsitsi tehtud, kõik mis on) =====
def kaanamine():
    read = []
    with open(f"{RAW}/taltech/inflection_et/word_inflections_hf.jsonl", encoding="utf-8") as f:
        for r in f:
            try: d = json.loads(r)
            except: continue
            if not (d.get("noun_phrase") and d.get("inflection") and d.get("case")): continue
            if d["noun_phrase"] in LEKE_INF: continue
            read.append(d)
    for d in read:
        vorm = d["inflection"][0] if isinstance(d["inflection"], list) else d["inflection"]
        lisa(f"Pane fraas '{d['noun_phrase']}' {d.get('plurality','ainsuse')} "
             f"{d['case']} käändesse. Vasta ainult vormiga.",
             vorm, "kaanamine", "TalTechNLP/inflection_et", "puhas", min_pikkus=1)
    print(f"käänamine (kõik olemasolevad): {len(read)}")

# ===== 5. PÄRIS SÕNASELETUSED (EKI-põhised, sõnaleiutamise vastu) =====
def sonad(maht=8000):
    read = []
    for tee in glob.glob(f"{RAW}/taltech/word_meanings_et/*.jsonl"):
        if ".cache" in tee: continue
        with open(tee, encoding="utf-8") as f:
            for r in f:
                try: d = json.loads(r)
                except: continue
                w, defi = d.get("words"), d.get("definition")
                if not w or not defi: continue
                sona = w[0] if isinstance(w, list) else w
                sel = defi[0] if isinstance(defi, list) else defi
                if sona and sel and len(str(sel)) > 8:
                    read.append((str(sona), str(sel)))
    for sona, sel in random.sample(read, min(maht, len(read))):
        lisa(f"Mida tähendab eestikeelne sõna '{sona}'? Selgita lühidalt.",
             sel, "sonatahendus", "TalTechNLP/word_meanings_et", "puhas")
    print(f"sõnaseletused: {min(maht, len(read))} / basseinis {len(read)}")

# ===== 6. PÄRIS DIALOOGID JA KOKKUVÕTTED =====
def dialoogid(maht=6000):
    n = 0
    for muster, nimi in [(f"{RAW}/taltech/samsum_ee/data/train-*.parquet", "samsum_ee"),
                         (f"{RAW}/taltech/dialogsum_ee/data/train-*.parquet", "dialogsum_ee")]:
        read = parquet_read(muster)
        valim = random.sample(read, min(maht // 2, len(read)))
        for x in valim:
            dl, sm = x.get("dialogue"), x.get("summary")
            if dl and sm and len(str(dl)) > 60:
                lisa(f"Võta see vestlus lühidalt kokku:\n\n{dl}", sm,
                     "dialoogi-kokkuvote", f"TalTechNLP/{nimi}", "puhas"); n += 1
    for x in parquet_read(f"{RAW}/taltech/EsimeneStuudio/data/train-*.parquet"):
        tr, sm = x.get("transcript"), x.get("summary")
        if tr and sm and len(str(tr)) > 200:
            lisa(f"Võta see saatelõik kokku:\n\n{str(tr)[:6000]}", sm,
                 "saate-kokkuvote", "TalTechNLP/EsimeneStuudio", "puhas"); n += 1
    print(f"dialoogid ja saated: {n}")

# ===== 7. PÄRIS UUDISED (ERR toimetatud) =====
def uudised(maht=6000):
    read = parquet_read(f"{RAW}/taltech/instructERRnews/data/train-*.parquet")
    valim = random.sample(read, min(maht, len(read)))
    for x in valim:
        i, inp, o = x.get("instruction"), x.get("input"), x.get("output")
        if i and inp and o and len(str(o)) > 60:
            lisa(f"{i}\n\n{str(inp)[:6000]}", o, "uudise-kokkuvote",
                 "TalTechNLP/instructERRnews", "puhas")
    print(f"ERR uudised: {len(valim)} / basseinis {len(read)}")

# ===== 8. ÜLDISED INSTRUKTSIOONID (alpaca-est — märgitud hallina) =====
def alpaca(maht=5000):
    d = json.load(open(f"{RAW}/alpaca-est/data/alpaca_est.json", encoding="utf-8"))
    sobivad = []
    for x in d:
        instr, inp, out = x.get("instruction",""), x.get("input",""), x.get("output","")
        if not instr or not out or not (40 < len(out) < 3000): continue
        if sum(c.isascii() for c in out) / max(len(out), 1) > 0.97: continue
        sobivad.append((instr, inp, out))
    for instr, inp, out in random.sample(sobivad, min(maht, len(sobivad))):
        lisa(f"{instr}\n\n{inp}".strip() if inp else instr, out,
             "yldine-instruktsioon", "TartuNLP/alpaca-est", "hall-gpt35")
    print(f"alpaca-est: {min(maht, len(sobivad))} / basseinis {len(sobivad)}")

# ===== 9. REPLAY: inglise + kood (regressioonikaitse) =====
def replay(maht_en=3000, maht_kood=3000):
    read = parquet_read(f"{RAW}/taltech/samsum_ee/data/train-*.parquet")
    n = 0
    for x in random.sample(read, min(maht_en, len(read))):
        if x.get("en_dialogue") and x.get("en_summary"):
            lisa(f"Summarize this conversation briefly:\n\n{x['en_dialogue']}",
                 x["en_summary"], "replay-inglise", "TalTechNLP/samsum_ee (en)", "puhas",
                 system="You are a helpful assistant."); n += 1
    print(f"replay inglise: {n}")
    kood = parquet_read(f"{RAW}/replay/**/*.parquet")
    for f in glob.glob(f"{RAW}/replay/**/*.jsonl", recursive=True):
        if ".cache" in f: continue
        try: kood += [json.loads(r) for r in open(f, encoding="utf-8") if r.strip()]
        except Exception: continue
    sobivad = [(str(x.get("instruction") or x.get("prompt")), str(x.get("input", "")),
                str(x.get("output") or x.get("response") or x.get("completion")))
               for x in kood if isinstance(x, dict)
               and (x.get("instruction") or x.get("prompt"))
               and (x.get("output") or x.get("response") or x.get("completion"))]
    for i, inp, o in random.sample(sobivad, min(maht_kood, len(sobivad))):
        lisa(f"{i}\n\n{inp}".strip() if inp else i, o, "replay-kood",
             "CodeAlpaca-20k", "hall-gpt35",
             system="You are a helpful coding assistant.")
    print(f"replay kood: {min(maht_kood, len(sobivad))}")

for fn in (err_video, qa_saated, grammatika, kaanamine, sonad, dialoogid,
           uudised, alpaca, replay):
    try: fn()
    except Exception as e:
        print(f"VIGA {fn.__name__}: {type(e).__name__}: {str(e)[:200]}")

# ===== Tokeniseeri, sega, kirjuta =====
random.shuffle(naited)
os.makedirs(OUT, exist_ok=True)
for n in naited:
    n["tokeneid"] = len(TOK.encode("\n".join(m["content"] for m in n["messages"])).ids)

def kirjuta(kirjed, nimi):
    tee = f"{OUT}/{nimi}"
    with open(tee, "w", encoding="utf-8") as f:
        for k in kirjed:
            f.write(json.dumps(k, ensure_ascii=False) + "\n")
    return tee, hashlib.sha256(open(tee, "rb").read()).hexdigest()

tee_koik, h_koik = kirjuta(naited, "sft_v1.jsonl")

# Ring 1: TEADLIK valik baasjoone nõrkuste järgi (mitte juhuslik lõige).
# Baasjoon 2026-08-22: morfoloogia-meta 9,3% · sõnaleiutamine 28,6% ·
# liitsõnad 42,9% · käänamine 51,7% · grammatikaparandus 80,6%.
# Nõrgemad veaklassid saavad kogu olemasoleva materjali.
KVOODID = {
    "kaanamine":            10**9,   # kõik — kriitiline auk, materjali napib niigi
    "grammatikaparandus":   10**9,   # kõik — kõige sihitum parandusmaterjal
    "k6ne-tekstiks":        10**9,   # kõik — päris kõne → korrektne tekst
    "saate-kokkuvote":      10**9,   # kõik (neid on vähe)
    "sonatahendus":          6000,   # sõnaleiutamise vastu
    "saatevestlus-qa":       4000,   # päris kõnekeel
    "parisk6ne-pealkiri":    1500,
    "parisk6ne-juhtl6ik":    1500,
    "uudise-kokkuvote":      2000,
    "dialoogi-kokkuvote":    1500,
    "yldine-instruktsioon":  1200,   # hall kiht — hoiame väiksena
    "replay-inglise":        2500,   # regressioonikaitse
    "replay-kood":           2500,
}
# KAHEASTMELINE valik: prioriteetsed kategooriad korjatakse TÄIELIKULT enne,
# kui tokenieelarve saab ülejäänute peale kuluda. (Ühe-etapiline lõige surus
# käänamise 1022-lt 416-le, sest eelarve täitus enne.)
PRIORITEET = ["kaanamine", "grammatikaparandus", "k6ne-tekstiks", "saate-kokkuvote"]
ring1, votetud, jooksev = [], {}, 0

def vota(n):
    global jooksev
    ring1.append(n)
    votetud[n["kategooria"]] = votetud.get(n["kategooria"], 0) + 1
    jooksev += n["tokeneid"]

for n in naited:                                   # 1. etapp: prioriteetsed täies mahus
    if n["kategooria"] in PRIORITEET: vota(n)
print(f"\nprioriteetsed kategooriad: {len(ring1)} näidet, {jooksev/1e6:.2f}M tokenit")

for n in naited:                                   # 2. etapp: replay (regressioonikaitse)
    k = n["kategooria"]
    if not k.startswith("replay"): continue
    if votetud.get(k, 0) >= KVOODID.get(k, 0): continue
    if jooksev + n["tokeneid"] > RING1_TOKENEID * 1.05: break
    vota(n)

for n in naited:                                   # 3. etapp: ülejäänu kvootide piires
    k = n["kategooria"]
    if k in PRIORITEET or k.startswith("replay"): continue
    if votetud.get(k, 0) >= KVOODID.get(k, 0): continue
    if jooksev + n["tokeneid"] > RING1_TOKENEID * 1.05: continue
    vota(n)
tee_r1, h_r1 = kirjuta(ring1, "sft_v1_10m.jsonl")

def kokkuvote(kirjed):
    kat, lits, tok = {}, {}, 0
    for n in kirjed:
        kat[n["kategooria"]] = kat.get(n["kategooria"], 0) + 1
        lits[n["litsents"]] = lits.get(n["litsents"], 0) + 1
        tok += n["tokeneid"]
    return kat, lits, tok

kat_k, lits_k, tok_k = kokkuvote(naited)
kat_1, lits_1, tok_1 = kokkuvote(ring1)
replay_osa = sum(v for k, v in kat_1.items() if k.startswith("replay")) / max(len(ring1), 1)

manifest = {"koik": {"fail": tee_koik, "sha256": h_koik, "naiteid": len(naited),
                     "tokeneid": tok_k, "kategooriad": kat_k, "litsentsid": lits_k},
            "ring1": {"fail": tee_r1, "sha256": h_r1, "naiteid": len(ring1),
                      "tokeneid": tok_1, "kategooriad": kat_1, "litsentsid": lits_1,
                      "replay_osakaal": round(replay_osa, 3)},
            "seeme": SEEME,
            "pohimote": "PÄRIS inimeste tekst ja kõne; sünteetiline genereerimine VÄLJAS",
            "lekkeblokk": {"fraase": len(LEKE_INF), "lauseid": len(LEKE_GEC)}}
with open(f"{OUT}/sft_v1_manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)

print(f"\n=== KOKKU: {len(naited)} näidet, {tok_k/1e6:.2f}M tokenit")
print(f"=== RING 1: {len(ring1)} näidet, {tok_1/1e6:.2f}M tokenit, "
      f"replay {replay_osa*100:.1f}%")
print("\nring 1 kategooriad:")
for k, v in sorted(kat_1.items(), key=lambda x: -x[1]):
    print(f"  {k:26} {v:6}")
print(f"\nlitsentsid (ring 1): {json.dumps(lits_1, ensure_ascii=False)}")
print(f"SHA-256 (ring 1): {h_r1}")
