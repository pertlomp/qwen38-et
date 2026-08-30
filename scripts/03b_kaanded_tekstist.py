#!/usr/bin/env python3
"""Ekstraheerib PÄRIS käändevormid PÄRIS tekstist (EstNLTK morfoloogiaanalüüs).

Miks: käänamine on baasjoone suurim auk (51,7% → 63,3% pärast ring 1), aga
TalTechi `inflection_et` bassein on ammendatud (1400 kirjet, millest 1022 juba
kasutatud + 60 evalis). Rohkem PÄRIS käänamisandmeid on olemas ainult tekstis
endas: iga stenogrammi- ja uudislause sisaldab käänatud sõnu.

See EI OLE sünteetiline genereerimine — vormid on inimeste kirjutatud, me
ainult tuvastame, mis vorm need on. Vabamorfi süntees (03_gen_morfoloogia.py)
jääb endiselt reservi.

Kvaliteedinõuded:
  - ainult ÜHEMÕTTELINE analüüs (mitmene morfoloogia visatakse ära)
  - lemma peab vormist erinema (nimetav ei õpeta midagi)
  - sagedusfilter: sõna peab korpuses korduma (juhuslikud kirjavead välja)
  - eval-lekke blokk
  - käänete kaupa tasakaalustatud

Väljund: data/processed/kaanded_tekstist.jsonl
"""
import collections, glob, json, os, random, re, sys

RAW = "/mnt/varu/qwen38-et-data/raw"
OUT = "/mnt/varu/qwen38-et-data/processed"
EVAL = "/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/eval"
SEEME = 20260823
random.seed(SEEME)

# Vabamorfi vormikood → (eestikeelne käändenimi, arv)
VORM = {
    "sg g": ("omastav", "ainsuse"), "sg p": ("osastav", "ainsuse"),
    "sg ill": ("sisseütlev", "ainsuse"), "sg in": ("seesütlev", "ainsuse"),
    "sg el": ("seestütlev", "ainsuse"), "sg all": ("alaleütlev", "ainsuse"),
    "sg ad": ("alalütlev", "ainsuse"), "sg abl": ("alaltütlev", "ainsuse"),
    "sg tr": ("saav", "ainsuse"), "sg ter": ("rajav", "ainsuse"),
    "sg es": ("olev", "ainsuse"), "sg ab": ("ilmaütlev", "ainsuse"),
    "sg kom": ("kaasaütlev", "ainsuse"),
    "pl n": ("nimetav", "mitmuse"), "pl g": ("omastav", "mitmuse"),
    "pl p": ("osastav", "mitmuse"), "pl ill": ("sisseütlev", "mitmuse"),
    "pl in": ("seesütlev", "mitmuse"), "pl el": ("seestütlev", "mitmuse"),
    "pl all": ("alaleütlev", "mitmuse"), "pl ad": ("alalütlev", "mitmuse"),
    "pl abl": ("alaltütlev", "mitmuse"), "pl tr": ("saav", "mitmuse"),
    "pl ter": ("rajav", "mitmuse"), "pl es": ("olev", "mitmuse"),
    "pl ab": ("ilmaütlev", "mitmuse"), "pl kom": ("kaasaütlev", "mitmuse"),
}
SIHT_KAANDE_KOHTA = 700          # tasakaal: iga kääne saab kuni nii palju näidet
MIN_SAGEDUS = 3                  # vorm peab korpuses korduma

def loe_laused(maks=60000):
    laused = []
    for f in sorted(glob.glob(f"{RAW}/riigikogu-steno/*.json"))[:120]:
        try: d = json.load(open(f, encoding="utf-8"))
        except Exception: continue
        for istung in d if isinstance(d, list) else []:
            for pkt in istung.get("agendaItems") or []:
                for e in pkt.get("events") or []:
                    t = e.get("text")
                    if t and 40 < len(t) < 900:
                        laused.append(t)
                        if len(laused) >= maks // 2: break
    tee = f"{RAW}/taltech/err-video-news-transcribed/train.jsonl"
    if os.path.exists(tee):
        with open(tee, encoding="utf-8") as f:
            for r in f:
                try: d = json.loads(r)
                except Exception: continue
                for v in (d.get("text"), d.get("leadin")):
                    if v and 40 < len(v) < 900:
                        laused.append(v)
                if len(laused) >= maks: break
    return laused

def main():
    from estnltk import Text

    leke = json.load(open(f"{EVAL}/leke_blokk.json", encoding="utf-8"))
    keelatud = {x.lower() for x in leke.get("inflection_et", [])}

    laused = loe_laused()
    print(f"analüüsin {len(laused)} lauset...", flush=True)

    # (lemma, vormikood, sõnaliik) → Counter(vorm)
    korje = collections.defaultdict(collections.Counter)
    for i in range(0, len(laused), 300):
        tykk = "\n".join(laused[i:i+300])
        try:
            t = Text(tykk); t.tag_layer(["morph_analysis"])
        except Exception:
            continue
        for s in t.morph_analysis:
            # ÜHEMÕTTELISUS: mitmene analüüs → ebakindel, viskame ära
            if len(s.annotations) != 1:
                continue
            ann = s.annotations[0]
            lemma, pos, vorm_kood = ann["lemma"], ann["partofspeech"], ann["form"]
            sonavorm = s.text
            if pos not in ("S", "A"): continue
            if vorm_kood not in VORM: continue
            if not lemma or not lemma.isalpha() or not sonavorm.isalpha(): continue
            if not (3 <= len(lemma) <= 20): continue
            if lemma.lower() == sonavorm.lower(): continue      # ei õpeta midagi
            if lemma.lower() in keelatud: continue              # eval-lekke blokk
            if lemma[0].isupper(): continue                     # pärisnimed välja
            korje[(lemma, vorm_kood, pos)][sonavorm.lower()] += 1
        if (i // 300) % 20 == 0:
            print(f"  {i}/{len(laused)} lauset, {len(korje)} lemma-vormi paari", flush=True)

    # Sagedusfilter + käänete kaupa tasakaal
    kandidaadid = collections.defaultdict(list)
    for (lemma, kood, pos), loend in korje.items():
        vorm, n = loend.most_common(1)[0]
        if n < MIN_SAGEDUS: continue
        # kui sama lemma+kood annab mitu eri vormi, on analüüs ebakindel
        if len(loend) > 1 and loend.most_common(2)[1][1] >= n * 0.4: continue
        kandidaadid[kood].append((lemma, vorm, pos, n))

    naited = []
    SYS = "Sa oled abivalmis assistent. Vasta loomulikus ja korrektses eesti keeles."
    for kood, read in kandidaadid.items():
        kaane, arv = VORM[kood]
        read.sort(key=lambda x: -x[3])                  # sagedasemad ees
        for lemma, vorm, pos, n in read[:SIHT_KAANDE_KOHTA]:
            kysimus = (f"Pane sõna '{lemma}' {arv} {kaane} käändesse. "
                       f"Vasta ainult vormiga.")
            naited.append({"messages": [
                {"role": "system", "content": SYS},
                {"role": "user", "content": kysimus},
                {"role": "assistant", "content": vorm}],
                "kategooria": "kaanamine",
                "allikas": "Riigikogu stenogrammid + ERR (EstNLTK analüüs)",
                "litsents": "puhas", "kaane": kaane, "arv": arv, "sagedus": n})

    random.shuffle(naited)
    os.makedirs(OUT, exist_ok=True)
    from tokenizers import Tokenizer
    TOK = Tokenizer.from_file("/mnt/varu/qwen38-et-data/tokenizer/tokenizer.json")
    for n in naited:
        n["tokeneid"] = len(TOK.encode("\n".join(m["content"] for m in n["messages"])).ids)

    tee = f"{OUT}/kaanded_tekstist.jsonl"
    with open(tee, "w", encoding="utf-8") as f:
        for n in naited:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")

    jaotus = collections.Counter(f"{n['arv']} {n['kaane']}" for n in naited)
    print(f"\nVALMIS: {len(naited)} käänamisnäidet, "
          f"{sum(n['tokeneid'] for n in naited)/1000:.0f}k tokenit")
    print(f"unikaalseid lemmasid: {len({n['messages'][1]['content'] for n in naited})}")
    for k, v in sorted(jaotus.items()):
        print(f"  {k:24} {v:4}")
    print(f"→ {tee}")

if __name__ == "__main__":
    main()
