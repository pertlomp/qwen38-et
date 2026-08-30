#!/usr/bin/env python3
"""Keskne andmeregister: mis allikas, kust, mis litsents, kus kasutatud.

Perti nõue 2026-08-23: "kogu data mida saame salvestame, kategoriseerime,
tekitame selge arusaama mis on kust". Ilma selleta ei saa hiljem vastata
küsimusele, kas mingi materjal tohib avalikku paketti minna.

Register on KÄSITSI HOOLDATAV (allikad ja litsentsid tulevad allpool tabelist)
+ AUTOMAATNE mõõtmine (mahud kettalt, kirjete arv failidest). Nii ei valeta
number ja kontekst ei kao.

Väljund: reports/ANDMEREGISTER.md + reports/andmeregister.json
"""
import glob, json, os, subprocess

RAW = "/mnt/varu/qwen38-et-data/raw"
PROC = "/mnt/varu/qwen38-et-data/processed"
OUT = "/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/reports"

# --- KÄSITSI HOOLDATAV OSA: päritolu, litsents, kasutuspiirang ---
ALLIKAD = [
 {"nimi": "HPLT v2 (est_Latn)", "kaust": "hplt-v2", "kategooria": "veebitekst",
  "url": "https://data.hplt-project.org/two/cleaned/est_Latn/1.jsonl.zst",
  "litsents": "CC0 / vaba (HPLT väljalase)", "saadud": "2026-08-22",
  "kasutus": "CPT-reserv (faas 4)", "avaldatav": "jah, allikaviitega"},
 {"nimi": "FineWeb-2 (ekk_Latn)", "kaust": "fineweb2", "kategooria": "veebitekst",
  "url": "https://huggingface.co/datasets/HuggingFaceFW/fineweb-2",
  "litsents": "ODC-By 1.0", "saadud": "2026-08-22",
  "kasutus": "CPT-reserv (faas 4)", "avaldatav": "jah, allikaviitega"},
 {"nimi": "Riigi Teataja XML", "kaust": "riigiteataja", "kategooria": "õigustekst",
  "url": "https://www.riigiteataja.ee/avaandmed/ERT/",
  "litsents": "avalik omand (AutÕS §5, õigusaktid ei ole kaitstud)",
  "saadud": "2026-08-22", "kasutus": "CPT-reserv; SFT-paarid plaanis",
  "avaldatav": "JAH, piiranguteta"},
 {"nimi": "Riigikogu stenogrammid", "kaust": "riigikogu-steno", "kategooria": "toimetatud kõne",
  "url": "https://api.riigikogu.ee/api/steno/verbatims",
  "litsents": "avalik omand (ametlikud dokumendid)", "saadud": "2026-08-22",
  "kasutus": "käänamiskorpus; CPT-reserv", "avaldatav": "JAH, piiranguteta"},
 {"nimi": "OPUS OpenSubtitles v2018 (et)", "kaust": "opus-opensubtitles", "kategooria": "subtiitrid",
  "url": "https://opus.nlpl.eu/OpenSubtitles", "litsents": "ebaselge (tuletatud teosed)",
  "saadud": "2026-08-22", "kasutus": "EI KASUTATUD ring 1-3",
  "avaldatav": "EI — jääb koduseks"},
 {"nimi": "Eesti Vikipeedia", "kaust": "wikipedia", "kategooria": "entsüklopeedia",
  "url": "https://dumps.wikimedia.org/etwiki/", "litsents": "CC-BY-SA 4.0 (share-alike)",
  "saadud": "2026-08-22", "kasutus": "CPT-reserv", "avaldatav": "jah, CC-BY-SA all"},
 {"nimi": "TalTech inflection_et", "kaust": "taltech/inflection_et", "kategooria": "käänamine",
  "url": "https://huggingface.co/datasets/TalTechNLP/inflection_et",
  "litsents": "MÄÄRAMATA (HF-kaardil puudub)", "saadud": "2026-08-22",
  "kasutus": "ring 1 SFT (1022), eval (60)", "avaldatav": "KÜSI ENNE"},
 {"nimi": "TalTech grammar_et + grammar2_et", "kaust": "taltech/grammar_et", "kategooria": "grammatikaparandus",
  "url": "https://huggingface.co/datasets/TalTechNLP/grammar_et",
  "litsents": "kontrollimata", "saadud": "2026-08-22",
  "kasutus": "ring 1-2 SFT (9302), eval (50)", "avaldatav": "KÜSI ENNE"},
 {"nimi": "TalTech word_meanings_et", "kaust": "taltech/word_meanings_et", "kategooria": "sõnaseletused",
  "url": "https://huggingface.co/datasets/TalTechNLP/word_meanings_et",
  "litsents": "kontrollimata", "saadud": "2026-08-22", "kasutus": "ring 1-3 SFT",
  "avaldatav": "KÜSI ENNE"},
 {"nimi": "TalTech err-video-news-transcribed", "kaust": "taltech/err-video-news-transcribed",
  "kategooria": "kõne + toimetatud tekst",
  "url": "https://huggingface.co/datasets/TalTechNLP/err-video-news-transcribed",
  "litsents": "CC-BY-SA 4.0 (SHARE-ALIKE, nakkav)", "saadud": "2026-08-22",
  "kasutus": "ring 1-2 SFT (kõne→tekst paarid); käänamiskorpus",
  "avaldatav": "ainult CC-BY-SA all"},
 {"nimi": "TalTech qa_broadcast_conv_et", "kaust": "taltech/qa_broadcast_conv_et",
  "kategooria": "saatevestlused", "url": "https://huggingface.co/datasets/TalTechNLP/qa_broadcast_conv_et",
  "litsents": "kontrollimata", "saadud": "2026-08-22", "kasutus": "ring 1-3 SFT",
  "avaldatav": "KÜSI ENNE"},
 {"nimi": "TartuNLP alpaca-est", "kaust": "alpaca-est", "kategooria": "instruktsioonid",
  "url": "https://github.com/TartuNLP/alpaca-est",
  "litsents": "GPT-3.5 genereeritud → OpenAI ToS hall ala", "saadud": "2026-08-22",
  "kasutus": "ring 1-3 SFT (märgitud 'hall-gpt35')",
  "avaldatav": "ainult teadusklausliga (Alpaca-est pretsedent)"},
 {"nimi": "TartuNLP gec-llm", "kaust": "gec-llm", "kategooria": "grammatikaparandus",
  "url": "https://github.com/TartuNLP/gec-llm", "litsents": "kontrollimata",
  "saadud": "2026-08-22", "kasutus": "DPO-reserv", "avaldatav": "KÜSI ENNE"},
 {"nimi": "Riigikogu heli + joondatud stenogrammid", "kaust": "heli/riigikogu-audio-stenograms-2018-2025",
  "kategooria": "KÕNE (heli+tekst)",
  "url": "https://huggingface.co/datasets/TalTechNLP/riigikogu-audio-stenograms-2018-2025",
  "litsents": "CC-BY-SA-3.0 (share-alike)", "saadud": "2026-08-24",
  "kasutus": "RESERV: Whisperi kohandamine / kõnemudel; EI kasutata tekstitreeningus",
  "avaldatav": "ainult CC-BY-SA all"},
 {"nimi": "VoxPopuli (eesti osa)", "kaust": "heli/voxpopuli-et", "kategooria": "KÕNE (heli+tekst)",
  "url": "https://huggingface.co/datasets/facebook/voxpopuli",
  "litsents": "CC0-1.0 / other (kontrolli alamosa)", "saadud": "2026-08-24",
  "kasutus": "RESERV: kõnemudel (Euroopa Parlamendi eesti kõne)",
  "avaldatav": "CC0 osa jah"},
 {"nimi": "TalTech EASC + EFAC", "kaust": "heli", "kategooria": "KÕNE (heli+tekst)",
  "url": "https://huggingface.co/datasets/TalTechNLP/EASC",
  "litsents": "MÄÄRAMATA ('other')", "saadud": "2026-08-24",
  "kasutus": "RESERV: kõnemudel", "avaldatav": "KÜSI ENNE"},
 {"nimi": "CodeAlpaca-20k", "kaust": "replay", "kategooria": "replay (kood, inglise)",
  "url": "https://huggingface.co/datasets/HuggingFaceH4/CodeAlpaca_20K",
  "litsents": "GPT genereeritud → hall", "saadud": "2026-08-23",
  "kasutus": "ring 1-3 replay", "avaldatav": "ei ole vajalik"},
]

TULETISED = [
 {"fail": "et-kaanamiskorpus-v1.jsonl", "kirjeldus": "mudelisõltumatu käänamiskorpus",
  "allikad": "TalTech inflection_et + Riigikogu/ERR ekstrakt",
  "avaldatav": "osaliselt: Riigikogu-osa vabalt, ERR-osa CC-BY-SA, TalTech küsi"},
 {"fail": "sft_v1.jsonl", "kirjeldus": "kogu SFT-bassein (chat-formaadis)",
  "allikad": "vt allikate tabel", "avaldatav": "segu — filtreeri litsentsi järgi"},
 {"fail": "morfo_meta.jsonl", "kirjeldus": "EKI reeglistiku faktid (käänded, kõneviisid)",
  "allikad": "EKI reeglistik, käsitsi koostatud", "avaldatav": "JAH, oma looming"},
 {"fail": "kaanded_tekstist.jsonl", "kirjeldus": "EstNLTK-ga ekstraheeritud vormid",
  "allikad": "Riigikogu + ERR", "avaldatav": "CC-BY-SA (kuni allikad eraldatud)"},
]

def kausta_maht(tee):
    if not os.path.exists(tee): return 0
    try:
        return int(subprocess.run(["du", "-sb", tee], capture_output=True,
                                  text=True).stdout.split()[0])
    except Exception:
        return 0

def ridu(tee):
    try: return sum(1 for _ in open(tee, encoding="utf-8", errors="replace"))
    except Exception: return None

for a in ALLIKAD:
    a["baite"] = kausta_maht(f"{RAW}/{a['kaust']}")

for t in TULETISED:
    tee = f"{PROC}/{t['fail']}"
    t["baite"] = os.path.getsize(tee) if os.path.exists(tee) else 0
    t["kirjeid"] = ridu(tee) if os.path.exists(tee) else None

os.makedirs(OUT, exist_ok=True)
with open(f"{OUT}/andmeregister.json", "w", encoding="utf-8") as f:
    json.dump({"allikad": ALLIKAD, "tuletised": TULETISED,
               "uuendatud": "2026-08-23"}, f, ensure_ascii=False, indent=1)

kokku = sum(a["baite"] for a in ALLIKAD)
read = ["# Andmeregister — mis on kust, mis litsentsiga, kus kasutatud", "",
        f"**Uuendatud:** 2026-08-23 · **Toorandmeid kettal:** {kokku/1e9:.1f} GB",
        "", "Genereeritud: `scripts/10_andmeregister.py`. Mahud mõõdetakse kettalt,",
        "päritolu ja litsentsid on käsitsi hooldatavad (skripti sees).", "",
        "## Allikad", "",
        "| Allikas | Kategooria | Maht | Litsents | Kasutus | Avaldatav |",
        "|---|---|---:|---|---|---|"]
for a in sorted(ALLIKAD, key=lambda x: -x["baite"]):
    m = f"{a['baite']/1e9:.1f} GB" if a["baite"] > 1e9 else f"{a['baite']/1e6:.0f} MB"
    read.append(f"| {a['nimi']} | {a['kategooria']} | {m} | {a['litsents']} "
                f"| {a['kasutus']} | {a['avaldatav']} |")

read += ["", "## Tuletised (meie loodud)", "",
         "| Fail | Sisu | Kirjeid | Allikad | Avaldatav |", "|---|---|---:|---|---|"]
for t in TULETISED:
    k = f"{t['kirjeid']:,}" if t["kirjeid"] else "—"
    read.append(f"| `{t['fail']}` | {t['kirjeldus']} | {k} | {t['allikad']} "
                f"| {t['avaldatav']} |")

read += ["", "## Litsentsi-reeglid, mida ei tohi unustada", "",
 "1. **CC-BY-SA on nakkav.** ERR-i ja Vikipeedia materjalist tuletatu peab jääma",
 "   CC-BY-SA alla. Kui tahad piiranguteta avaldatavat paketti, ehita see AINULT",
 "   avaliku omandi allikatest (Riigikogu, Riigi Teataja) ja omaloomingust.",
 "2. **'Kontrollimata' ei tähenda 'lubatud'.** TalTechi andmestikel puudub HF-kaardil",
 "   litsents. Enne avaldamist tuleb küsida.",
 "3. **Hall kiht on märgistatud.** Kõik GPT-genereeritud materjal kannab SFT-failides",
 "   lippu `litsents: hall-gpt35` — filtreeritav ühe reaga.",
 "4. **Subtiitreid ring 1-3 EI kasutanud.** Need jäid alla laaditud, aga kasutamata.",
 "", "## Uue allika lisamisel", "",
 "Lisa kirje `ALLIKAD` nimekirja skriptis (nimi, kaust, URL, litsents, saadud,",
 "kasutus, avaldatav) ja jooksuta skript uuesti. Mahud mõõdetakse ise.",
 "**Litsentsi väli ei tohi jääda tühjaks** — kui ei tea, kirjuta 'kontrollimata'",
 "ja avaldatavusse 'KÜSI ENNE'."]

with open(f"{OUT}/ANDMEREGISTER.md", "w", encoding="utf-8") as f:
    f.write("\n".join(read) + "\n")
print(f"allikaid: {len(ALLIKAD)} | toorandmeid {kokku/1e9:.1f} GB")
print(f"tuletisi: {len(TULETISED)}")
print(f"→ {OUT}/ANDMEREGISTER.md")
