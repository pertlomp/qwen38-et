#!/usr/bin/env python3
"""Andmeallikate inventuur: mitu tokenit igas allikas on (Qweni tokeniseerijaga).

Valimipõhine: loeb igast allikast N dokumenti, mõõdab tokenit/bait suhte ja
ekstrapoleerib lahtipakitud kogumahule. EI loe 44 GB faile tervikuna mällu.

Väljund: reports/andmete-inventuur.md + reports/inventuur.json
"""
import bz2, glob, gzip, io, json, os, re, subprocess, sys, zipfile
from tokenizers import Tokenizer

RAW = "/mnt/varu/qwen38-et-data/raw"
OUT_DIR = "/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/reports"
TOK = Tokenizer.from_file("/mnt/varu/qwen38-et-data/tokenizer/tokenizer.json")
VALIM_DOK = 2000        # dokumenti valimisse allika kohta
VALIM_MAX_MB = 40       # ära loe rohkem kui nii palju baite valimiks

def tok_arv(tekstid):
    """Tokenite arv kokku (batch, kiirem kui ükshaaval)."""
    return sum(len(e.ids) for e in TOK.encode_batch(tekstid))

def ekstrapoleeri(valim_tekstid, valim_baidid, koguhulk_baite):
    """Valimi põhjal kogu allika tokenihinnang."""
    if not valim_tekstid or valim_baidid == 0:
        return 0, 0.0
    t = tok_arv(valim_tekstid)
    tok_per_bait = t / valim_baidid
    return int(tok_per_bait * koguhulk_baite), tok_per_bait

tulemused = []

def lisa(nimi, tokenid, dokid, markus, kindlus):
    tulemused.append({"allikas": nimi, "tokenid": tokenid, "dokumendid": dokid,
                      "markus": markus, "kindlus": kindlus})
    print(f"{nimi:38} {tokenid/1e6:12.1f}M tok  {markus}", flush=True)

# ---------- 1. HPLT v2 (zstd jsonl, 44 GB lahti) ----------
def hplt():
    p = f"{RAW}/hplt-v2/est_Latn-1.jsonl.zst"
    if not os.path.exists(p): return
    lahti_baite = 44_094_708_324   # zstd -t mõõdetud
    tekstid, baidid = [], 0
    proc = subprocess.Popen(["zstd", "-dc", p], stdout=subprocess.PIPE)
    for rida in io.TextIOWrapper(proc.stdout, encoding="utf-8", errors="replace"):
        try: d = json.loads(rida)
        except: continue
        t = d.get("text", "")
        if not t: continue
        tekstid.append(t); baidid += len(rida.encode())
        if len(tekstid) >= VALIM_DOK or baidid > VALIM_MAX_MB * 1e6: break
    proc.kill()
    kesk_dok_baite = baidid / max(len(tekstid), 1)
    tok, _ = ekstrapoleeri(tekstid, baidid, lahti_baite)
    lisa("HPLT v2 (est_Latn)", tok, int(lahti_baite / kesk_dok_baite),
         "veebitekst, kvaliteedimetaandmetega", "valim 2000 dok")

# ---------- 2. FineWeb-2 (parquet) ----------
def fineweb():
    import pyarrow.parquet as pq
    fs = sorted(glob.glob(f"{RAW}/fineweb2/*.parquet"))
    if not fs: return
    read_kokku, baidid_kokku = 0, 0
    for f in fs:
        pf = pq.ParquetFile(f)
        read_kokku += pf.metadata.num_rows
        baidid_kokku += os.path.getsize(f)
    pf = pq.ParquetFile(fs[0])
    partii = next(pf.iter_batches(batch_size=VALIM_DOK, columns=["text"]))
    tekstid = [t for t in partii.column("text").to_pylist() if t]
    v_baidid = sum(len(t.encode()) for t in tekstid)
    tok_valim = tok_arv(tekstid)
    tok_per_dok = tok_valim / max(len(tekstid), 1)
    lisa("FineWeb-2 (ekk_Latn)", int(tok_per_dok * read_kokku), read_kokku,
         f"veebitekst, {len(fs)} parquet-faili", "valim 2000 dok")

# ---------- 3. Riigi Teataja (zip XML) ----------
def riigiteataja():
    tok_kokku, dok_kokku = 0, 0
    for z in sorted(glob.glob(f"{RAW}/riigiteataja/*.zip")):
        try: zf = zipfile.ZipFile(z)
        except Exception as e:
            print(f"  RT {os.path.basename(z)}: ei avane ({e})"); continue
        nimed = [n for n in zf.namelist() if n.endswith(".xml")]
        lahti = sum(i.file_size for i in zf.infolist())
        tekstid, baidid = [], 0
        for n in nimed[:300]:
            try: xml = zf.read(n).decode("utf-8", "replace")
            except: continue
            # XML-sildid maha, jääb puhas tekst
            t = re.sub(r"<[^>]+>", " ", xml)
            t = re.sub(r"\s+", " ", t).strip()
            if len(t) < 50: continue
            tekstid.append(t[:20000]); baidid += len(xml.encode())
            if baidid > 20e6: break
        tok, _ = ekstrapoleeri(tekstid, baidid, lahti)
        tok_kokku += tok; dok_kokku += len(nimed)
        zf.close()
    lisa("Riigi Teataja (XML)", tok_kokku, dok_kokku,
         "õigusaktid, avalik omand (AutÕS §5)", "valim 300 akti/arhiiv")

# ---------- 4. OPUS OpenSubtitles ----------
def opus():
    p = f"{RAW}/opus-opensubtitles/opensubtitles-v2018-mono-et.txt.gz"
    if not os.path.exists(p): return
    read, baidid, valim = 0, 0, []
    with gzip.open(p, "rt", encoding="utf-8", errors="replace") as f:
        for i, rida in enumerate(f):
            read += 1
            if i < 50000:
                valim.append(rida.strip()); baidid += len(rida.encode())
    tok_valim = tok_arv([r for r in valim if r])
    lisa("OPUS OpenSubtitles (mono-et)", int(tok_valim / len(valim) * read), read,
         "subtiitrid — CPT-s max 10-15%", "valim 50k rida, ridu loetud täpselt")

# ---------- 5. Vikipeedia ----------
def wiki():
    p = f"{RAW}/wikipedia/etwiki-latest-pages-articles.xml.bz2"
    if not os.path.exists(p): return
    pakitud = os.path.getsize(p)
    tekstid, loetud_pakitud = [], 0
    puhver = []
    with bz2.open(p, "rt", encoding="utf-8", errors="replace") as f:
        for rida in f:
            puhver.append(rida)
            if len(puhver) > 200000: break
    kogu = "".join(puhver)
    for m in re.finditer(r"<text[^>]*>(.*?)</text>", kogu, re.S):
        t = re.sub(r"\{\{[^}]*\}\}|\[\[|\]\]|'''|''", " ", m.group(1))
        t = re.sub(r"\s+", " ", t).strip()
        if len(t) > 200: tekstid.append(t[:20000])
        if len(tekstid) >= 1500: break
    # bz2 tihendus eesti tekstil ~4x → hinnang lahtipakitud mahule
    lahti_hinnang = pakitud * 4
    valim_baidid = sum(len(t.encode()) for t in tekstid)
    kogu_baidid = len(kogu.encode())
    tekst_osa = valim_baidid / max(kogu_baidid, 1)   # kui palju XML-ist on artiklitekst
    tok, _ = ekstrapoleeri(tekstid, valim_baidid, lahti_hinnang * tekst_osa)
    lisa("Eesti Vikipeedia", tok, len(tekstid),
         "entsüklopeedia; bz2-tihendus hinnanguline", "VALIM+HINNANG (ebatäpsem)")

# ---------- 6. Väikesed jsonl/parquet allikad ----------
def vaiksed():
    grupid = {
        "TalTech grammatika (inflection+grammar+meanings)": [
            f"{RAW}/taltech/inflection_et", f"{RAW}/taltech/grammar_et",
            f"{RAW}/taltech/grammar2_et", f"{RAW}/taltech/word_meanings_et"],
        "TalTech ERR (uudised+transkriptsioonid)": [
            f"{RAW}/taltech/err-newsroom", f"{RAW}/taltech/err-video-news-transcribed",
            f"{RAW}/taltech/instructERRReddit"],
        "TalTech vestlus/kokkuvõte": [
            f"{RAW}/taltech/samsum_ee", f"{RAW}/taltech/dialogsum_ee",
            f"{RAW}/taltech/instructERRnews", f"{RAW}/taltech/qa_broadcast_conv_et",
            f"{RAW}/taltech/EsimeneStuudio"],
        "TalTech eval (MMLU_et, EstQA, human_eval)": [
            f"{RAW}/taltech/MMLU_et", f"{RAW}/taltech/EstQA",
            f"{RAW}/taltech/human_eval_et"],
        "Alpaca-est + GEC (SFT/DPO tooraine)": [
            f"{RAW}/alpaca-est", f"{RAW}/gec-llm"],
    }
    for nimi, kaustad in grupid.items():
        tekstid, ridu = [], 0
        for k in kaustad:
            for f in glob.glob(f"{k}/**/*", recursive=True):
                if not os.path.isfile(f): continue
                if f.endswith((".jsonl", ".json")):
                    try:
                        with open(f, encoding="utf-8", errors="replace") as fh:
                            sisu = fh.read()
                    except: continue
                    read = sisu.splitlines()
                    for r in read:
                        r = r.strip()
                        if not r or r in "[]": continue
                        ridu += 1
                        if len(tekstid) < 3000:
                            tekstid.append(re.sub(r"\s+", " ", r)[:8000])
                elif f.endswith(".gz") and f.endswith(".jsonl.gz"):
                    try:
                        with gzip.open(f, "rt", encoding="utf-8", errors="replace") as fh:
                            for r in fh:
                                ridu += 1
                                if len(tekstid) < 3000: tekstid.append(r.strip()[:8000])
                    except: continue
                elif f.endswith(".parquet"):
                    try:
                        import pyarrow.parquet as pq
                        pf = pq.ParquetFile(f); ridu += pf.metadata.num_rows
                        b = next(pf.iter_batches(batch_size=500))
                        for rec in b.to_pylist()[:500]:
                            if len(tekstid) < 3000:
                                tekstid.append(json.dumps(rec, ensure_ascii=False)[:8000])
                    except: continue
        if ridu == 0: continue
        tok_valim = tok_arv(tekstid) if tekstid else 0
        tok = int(tok_valim / max(len(tekstid), 1) * ridu)
        lisa(nimi, tok, ridu, "struktureeritud (SFT/eval tooraine)", "valim ≤3000 kirjet")

# ---------- 7. Riigikogu stenogrammid (jookseb veel) ----------
def steno():
    fs = glob.glob(f"{RAW}/riigikogu-steno/*.json")
    if not fs: return
    tekstid, korjatud = [], 0
    for f in fs[:60]:
        try:
            with open(f, encoding="utf-8") as fh: d = json.load(fh)
        except: continue
        for istung in d if isinstance(d, list) else []:
            for pkt in istung.get("agendaItems") or []:
                for e in pkt.get("events") or []:
                    t = e.get("text")
                    if t and len(t) > 40:
                        tekstid.append(t); korjatud += 1
    if not tekstid: return
    keskm_tok = tok_arv(tekstid[:3000]) / min(len(tekstid), 3000)
    # ekstrapoleeri failide arvu järgi
    kokku_faile = len(fs)
    kone_failis = korjatud / max(min(len(fs), 60), 1)
    lisa("Riigikogu stenogrammid", int(keskm_tok * kone_failis * kokku_faile),
         int(kone_failis * kokku_faile),
         f"toimetatud suuline keel; {kokku_faile} nädalafaili (2015–2026)",
         "valim 60 faili")

for f in (hplt, fineweb, riigiteataja, opus, wiki, vaiksed, steno):
    try: f()
    except Exception as e:
        print(f"VIGA {f.__name__}: {type(e).__name__}: {str(e)[:200]}", flush=True)

os.makedirs(OUT_DIR, exist_ok=True)
with open(f"{OUT_DIR}/inventuur.json", "w") as f:
    json.dump(tulemused, f, ensure_ascii=False, indent=2)

kokku = sum(t["tokenid"] for t in tulemused)
read = ["# Andmete inventuur — mõõdetud Qwen3.8 tokeniseerijaga", "",
        f"Kokku: **{kokku/1e9:.2f} miljardit tokenit** ({len(tulemused)} allikat).",
        "Valimipõhine ekstrapolatsioon — täpsus ±10–20%, mitte täisloendus.", "",
        "| Allikas | Tokenid | Dokumente/ridu | Märkus | Mõõtmisviis |",
        "|---|---:|---:|---|---|"]
for t in sorted(tulemused, key=lambda x: -x["tokenid"]):
    read.append(f"| {t['allikas']} | {t['tokenid']/1e6:,.1f}M | {t['dokumendid']:,} "
                f"| {t['markus']} | {t['kindlus']} |")
read += ["", f"**Kokku {kokku/1e9:.2f} mld tokenit.** Esimesse treeningringi läheb ~10M "
         f"ehk {10e6/kokku*100:.2f}% — ülejäänu on valikubassein."]
with open(f"{OUT_DIR}/andmete-inventuur.md", "w") as f:
    f.write("\n".join(read) + "\n")
print(f"\nKOKKU {kokku/1e9:.2f} mld tokenit → {OUT_DIR}/andmete-inventuur.md")
