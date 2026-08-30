#!/usr/bin/env python3
"""Ehitab mudelisõltumatu eesti käänamiskorpuse (TalTech + tekstist ekstraheeritud).

Miks eraldi failina: see korpus on projekti KÕIGE KANTAVAM vara. Adapter vananeb
koos mudeliga, korpus mitte — Qwen4, Llama või mis iganes tuleb, saab sellest
sama treeningmaterjali. Seetõttu EI ole see chat-formaadis: puhas andmestruktuur,
millest saab genereerida näiteid mis tahes mudeli vestlusmalli jaoks.

Litsentsid on kirje kaupa, sest need erinevad ja üks neist on nakkav:
  - riigikogu-steno  : avalik omand (ametlikud dokumendid, AutÕS §5)
  - err-video-news   : CC-BY-SA 4.0  ← SHARE-ALIKE, nakkab kogu tuletisele
  - taltech-inflection: litsents MÄÄRAMATA (HF-i kaardil puudub)
Praegune ekstrakt ei eristanud Riigikogu ja ERR-i lauseid, seega on need märgitud
konservatiivselt CC-BY-SA 4.0. Eraldamiseks tuleb 03b uuesti joosta allikalipuga.

Väljund:
  processed/et-kaanamiskorpus-v1.jsonl
  processed/et-kaanamiskorpus-v1-manifest.json
"""
import collections, hashlib, json, os

PROC = "/mnt/varu/qwen38-et-data/processed"
RAW = "/mnt/varu/qwen38-et-data/raw"
EVAL = "/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/eval"
VALJUND = f"{PROC}/et-kaanamiskorpus-v1.jsonl"

leke = json.load(open(f"{EVAL}/leke_blokk.json", encoding="utf-8"))
EVAL_FRAASID = {x.strip().lower() for x in leke.get("inflection_et", [])}

kirjed, nahtud = [], set()

def lisa(sisend, vorm, kaane, arv, tyyp, allikas, litsents, sagedus=None, sonaliik=None):
    sisend, vorm = str(sisend).strip(), str(vorm).strip()
    if not sisend or not vorm: return
    v = hashlib.md5(f"{sisend}|{vorm}|{kaane}|{arv}".lower().encode()).hexdigest()
    if v in nahtud: return
    nahtud.add(v)
    kirjed.append({
        "sisend": sisend,           # lemma või fraas algvormis
        "vorm": vorm,               # käänatud vorm
        "kaane": kaane,             # eestikeelne käändenimi
        "arv": arv,                 # "ainsuse" | "mitmuse"
        "tyyp": tyyp,               # "sona" | "fraas"
        "sonaliik": sonaliik,
        "sagedus": sagedus,         # korpusesagedus (None = TalTechi käsitsi tehtud)
        "allikas": allikas,
        "litsents": litsents,
        "eval_blokis": sisend.lower() in EVAL_FRAASID,
    })

# ---- 1. TalTechi käsitsi koostatud fraasid (sh omadussõna ühildumine) ----
tee = f"{RAW}/taltech/inflection_et/word_inflections_hf.jsonl"
n_tt = 0
with open(tee, encoding="utf-8") as f:
    for r in f:
        try: d = json.loads(r)
        except Exception: continue
        fraas, kaane = d.get("noun_phrase"), d.get("case")
        vormid = d.get("inflection") or []
        arv = d.get("plurality", "ainsuse")
        if not (fraas and kaane and vormid): continue
        for v in (vormid if isinstance(vormid, list) else [vormid]):
            lisa(fraas, v, kaane, arv, "fraas", "taltech-inflection",
                 "MÄÄRAMATA (HF-kaardil puudub)")
            n_tt += 1

# ---- 2. Tekstist ekstraheeritud üksiksõnad ----
tee = f"{PROC}/kaanded_tekstist.jsonl"
n_tx = 0
if os.path.exists(tee):
    with open(tee, encoding="utf-8") as f:
        for r in f:
            try: d = json.loads(r)
            except Exception: continue
            # kysimus kujul: Pane sõna 'X' <arv> <kääne> käändesse...
            k = d["messages"][1]["content"]
            try:
                lemma = k.split("'")[1]
            except IndexError:
                continue
            lisa(lemma, d["messages"][2]["content"], d.get("kaane"), d.get("arv"),
                 "sona", "riigikogu-steno + err-video-news",
                 "CC-BY-SA-4.0 (konservatiivne: ERR-i osa on share-alike)",
                 sagedus=d.get("sagedus"))
            n_tx += 1

with open(VALJUND, "w", encoding="utf-8") as f:
    for k in kirjed:
        f.write(json.dumps(k, ensure_ascii=False) + "\n")

kaanete_jaotus = collections.Counter(f"{k['arv']} {k['kaane']}" for k in kirjed)
lits = collections.Counter(k["litsents"] for k in kirjed)
tyybid = collections.Counter(k["tyyp"] for k in kirjed)
h = hashlib.sha256(open(VALJUND, "rb").read()).hexdigest()

manifest = {
    "nimi": "et-kaanamiskorpus-v1",
    "kirjeldus": "Eesti käänamiskorpus: TalTechi käsitsi koostatud fraasid + "
                 "Riigikogu/ERR tekstist EstNLTK-ga ekstraheeritud üksiksõnad. "
                 "Mudelisõltumatu — sobib iga LLM-i treeninguks.",
    "kirjeid": len(kirjed), "sha256": h,
    "koostatud": "2026-08-23",
    # --- Atributsioon: kelle panus on MIS. Algandmed jäävad allikate omaks. ---
    "koostaja": {
        "nimi": "Pert Lomp",
        "aasta": 2026,
        "projekt": "qwen38-et (eestikeelse lokaalse assistendi treening)",
        "panus": [
            "korpuse idee, metoodika ja koosseisu valik",
            "ekstraheerimistorustik (03b_kaanded_tekstist.py): ühemõttelisuse nõue, "
            "sagedusfilter, pärisnimede välistus, käänete tasakaalustus",
            "allikate ühendamine ühtsesse mudelisõltumatusse skeemi",
            "litsentside kirjepõhine märgistus ja eval-lekke blokk",
        ],
        "EI kuulu koostajale": "algandmed ise — need kuuluvad allikatele "
                               "(TalTechNLP, Riigikogu, ERR) oma litsentside all",
    },
    "viitamine": "Kui kasutad seda korpust või sellest tuletatud mudelit, viita: "
                 "Pert Lomp (2026), et-kaanamiskorpus-v1, koostatud TalTechNLP, "
                 "Riigikogu ja ERR avalikest allikatest. Algallikad tuleb eraldi "
                 "krediteerida vastavalt nende litsentsidele.",
    "tooriistade_litsents": "Ekstraheerimis- ja ehitusskriptid (qwen38-et/scripts/) "
                            "on Pert Lompi looming; litsentsi ei ole veel valitud "
                            "(vaikimisi: kõik õigused kaitstud kuni omanik otsustab).",
    "oiguslik_markus": "See ei ole õigusnõuanne. Enne avaldamist vaata litsentsid üle.",
    "allikad": {
        "taskech_fraase": n_tt,
        "tekstist_sonu": n_tx,
    },
    "tyybid": dict(tyybid),
    "litsentsid": dict(lits),
    "kaanete_jaotus": dict(sorted(kaanete_jaotus.items())),
    "eval_blokis": sum(1 for k in kirjed if k["eval_blokis"]),
    "hoiatused": [
        "ERR-i osa on CC-BY-SA 4.0 — share-alike nakkab kogu tuletisele. "
        "Avaliku omandi (Riigikogu) osa eraldamiseks tuleb 03b_kaanded_tekstist.py "
        "uuesti joosta allikalipuga.",
        "TalTechi inflection_et litsents on HF-kaardil määramata — enne avaldamist "
        "küsi TalTechilt või jäta see osa välja.",
        "eval_blokis=true kirjeid EI TOHI treeningusse panna (lukustatud testis).",
    ],
    "kasutus": "Iga kirje: sisend + kääne + arv → vorm. Treeningnäite saab "
               "genereerida mis tahes vestlusmalli jaoks; korpus ise on "
               "mudelist ja mallist sõltumatu.",
}
with open(f"{PROC}/et-kaanamiskorpus-v1-manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)

print(f"KORPUS: {len(kirjed)} kirjet ({n_tt} TalTechi fraasi + {n_tx} tekstist)")
print(f"tüübid: {dict(tyybid)}")
print(f"eval-blokis: {manifest['eval_blokis']}")
print(f"litsentsid: {json.dumps(dict(lits), ensure_ascii=False, indent=1)}")
print(f"SHA-256: {h}")
print(f"→ {VALJUND}")
