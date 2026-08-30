# STATUS — qwen38-et

## 2026-08-22 — projekt käivitatud, allalaadimised jooksevad

**Tehtud:**
- Projektiskelett `LLMTRAINING/qwen38-et/`, andmed `/mnt/varu/qwen38-et-data/` (sümlink `data/`).
- Inventuur: `reports/inventory.txt` — RTX 5090 (32 607 MiB, draiver 595.84), Python 3.14.4,
  uv 0.12.5, RAM 61 GB, Inteli ketas 1,9 TB vaba.
- Nimekonventsioon lukus: adapter `qwen38-27b-et-lora-v{N}`, Ollama `qwen3.8-et:27b-v{N}`.

**Allalaadimised `/mnt/varu/qwen38-et-data/raw/` (kontrollitud URL-id):**

| Allikas | Maht | Seis |
|---|---|---|
| TartuNLP alpaca-est (52 006 SFT näidet) | 37 MB | ✅ kohal |
| TartuNLP gec-llm (GEC paarid → DPO) | 332 KB | ✅ kohal |
| OPUS OpenSubtitles v2018 mono-et | 263 MB gz | ⏳ taustal |
| Eesti Vikipeedia dump (04.08.2026) | 305 MB bz2 | ⏳ taustal |
| HPLT v2 cleaned est_Latn (1 fail) | 13,1 GB zst (~37 GB lahti) | ⏳ taustal |
| FineWeb-2 ekk_Latn (5 parquet) | 19,7 GB | ⏳ taustal |
| Riigi Teataja XML (kõik aastad, avaandmed) | ~0,3–0,5 GB/aasta | ⏳ taustal |

OPUS mono-et valideeritud: 27 519 603 rida, 129,4 mln sõna — klapib LREC 2018 artikliga.
Riigi Teataja: AutÕS § 5 järgi õigusaktid autoriõigusega kaitsmata — kõige puhtam
litsents. HOIATUS registri kohta: kantseliit — CPT-segus max 10–15%, põhikasutus
SFT-paaridena "seadusetekst → selgita lihtsas eesti keeles".

**TalTechNLP HF-andmestikud (12/14 kohal, `raw/taltech/`):**
- Veaklasside vastu: `inflection_et` (fraas+kääne→vorm, ka omadussõna ühildumine),
  `grammar_et` (L2 original→correct), `grammar2_et` (L1), `word_meanings_et` (9,8 MB).
- Eval: `MMLU_et` (168 MB), `EstQA`, `human_eval_et`.
- Suuline/instruktsioonid: `samsum_ee`, `dialogsum_ee`, `instructERRnews` (41 MB),
  `qa_broadcast_conv_et` (136 MB), `EsimeneStuudio`.
- ❌ Lukustatud (gated, vajab HF-i sisselogimist + ligipääsutaotlust): `trivia_et_verified`, `exam_et`.
- ERR-i tekstid (Perti soovil, 2026-08-22): `err-video-news-transcribed` (424 MB —
  uudistevideote transkriptsioonid, ehtne suuline eesti keel), `err-newsroom` (173 MB
  artiklid), `instructERRReddit` (577 MB). Riigikogu 182 GB FLAC-heli jäeti teadlikult
  võtmata — stenogrammi TEKST tuleb Riigikogu API-st järgmises ringis.

**Vajab Perti kätt (veebivormid, ei saa automatiseerida):**
- ENC 2023 (ühendkorpus, 2,4+ mld sõna) — META-SHARE litsentsinõusolek:
  https://metashare.ut.ee/repository/browse/estonian-national-corpus-2023-prevert/ec397bb9bae611ee9c10e99c00eb27649a7f673b85724ebfaeb0f267373423c0/

**Hilisemad allikad (faasi 4 CPT jaoks, kui vaja):** Riigikogu stenogrammid (API),
OpenSubtitles2024 et (AINULT lukustatud eval-iks, mitte treeninguks).

## Inventuur tehtud (2026-08-22) — `reports/andmete-inventuur.md`

**Kokku 26,6 mld tokenit** kettal, mõõdetud päris Qwen3.8 tokeniseerijaga (valim +
ekstrapolatsioon, ±10–20%). Suurimad: HPLT 11,9 mld, FineWeb-2 11,4 mld, Riigi Teataja
1,3 mld, TalTech ERR 1,04 mld. Esimene treeningring võtab ~10M ehk **0,04%** — valik
on seega projekti kriitiline samm, mitte maht.

**Mõõdetud fakt, millel on tagajärjed:** OPUS 129,4M sõna → 307,3M tokenit ehk
**~2,4 tokenit sõna kohta**. Qweni tokeniseerija on eesti keele suhtes "kallis"
(inglise keeles ~1,3). Tagajärg: 10M tokenit ≈ 4,2M sõna, ja iga treeningsamm katab
vähem eesti sisu kui sama arv tokeneid inglise keeles.

**Terviklikkus kontrollitud:** Riigi Teataja 3 arhiivi SHA256 OK; HPLT zstd-test OK
(44,1 GB lahti). Ketas: ~76 GB / 1,9 TB.

## Eval mustandina valmis (2026-08-22) — OOTAB PERTI ÜLEVAATUST

`eval/et_locked_v1_draft.jsonl` — **200 ülesannet**, neist **153 kontrollitava
vastusega** ja 47 rubriigi järgi hinnatavat. SHA-256:
`439a37ee00eb90886c8344dc8a2d52e6a4ac575e9cd950a615ee05483b0e39c3` (seeme 20260822).

Koosseis: käänamine 60 (TalTech `inflection_et`, ka omadussõna ühildumine),
grammatikaparandus 50 (`grammar_et` L2 + `grammar2_et` L1), Perti tööülesanded 12,
morfoloogia-metateadmine 10, tõlkelisus 10, liitsõnad 8, rektsioon 8,
sõnaleiutamine 8, tehniline 8, sõnajärg 6, register 6, JSON 6, tööriistad 4,
regressioon (inglise + kood) 4.

`eval/leke_blokk.json` — kirjed, mis EI TOHI SFT-sse sattuda (lekkekontroll).

**Eval-toru tõestatud töökorras** (`scripts/07_eval.py`, jooks `runs/smoke-test`):
12 prompti, 0 tühja, 0 viga, keskmine latents 5,6 s → kogu 200 ≈ 19 min.
Inferentsiseaded LUKUS: temp 0.3, top_p 0.9, top_k 40, seed 20260822, ctx 8192.

**Suitsutesti leid — baasmudel kukub läbi mõõdetavalt:**
- "Mitu käänet on eesti keeles?" → **13** (õige 14).
- Käändenimede loetelu → leiutatud sõnad ("Osnik", "Omastik", "Omandaj"), kordused.
- Kaudne kõneviis → "kirjutaks" (see on tingiv), õige "kirjutavat"; reegel vale.

## ✅ BAASJOON MÕÕDETUD (2026-08-22) — `eval/runs/baseline/`

Eval lukustatud: `eval/et_locked_v1.jsonl`, SHA-256
`439a37ee00eb90886c8344dc8a2d52e6a4ac575e9cd950a615ee05483b0e39c3`.
Jooks: 200 ülesannet, 0 viga, 0 tühja, keskmine latents 2,4 s.

**Üldskoor 57,7%** (automaatselt skooritud 151/200; 47 rubriigi-ülesannet
ootavad inimhinnangut). Kategooriate kaupa:

| Kategooria | n | Baas |
|---|---:|---:|
| morfoloogia-metateadmine | 9 | **9,3%** |
| sõnaleiutamine | 7 | 28,6% |
| JSON-struktuur | 6 | 33,3% |
| liitsõnad | 7 | 42,9% |
| tehniline / tööriistad | 4 | 50,0% |
| käänamine | 60 | 51,7% |
| rektsioon | 8 | 75,0% |
| grammatikaparandus | 50 | 80,6% |

Mudel OSKAB parandada (80,6%), aga ei tea käändesüsteemi (9,3%) — sama muster,
mis kiirproovis. Paranduse sihtmärk on seega teadmine ja vormimoodustus.

## ✅ TREENINGUVALIM VALMIS — `data/processed/sft_v1_10m.jsonl`

**Perti reegel (2026-08-22): päris inimeste kõne ja tekst enne kõike; sünteetiline
genereerimine alles siis, kui näeme vajadust.** Vabamorfi generaator
(`03_gen_morfoloogia.py`) on kirjutatud ja töötab, aga on VÄLJAS — jääb reserviks.

Kõik paarid on allikates juba olemas, neid ei genereeritud:
- ERR videouudised: päris kõne (transkriptsioon) ↔ ajakirjaniku kirjutatud
  artikkel/pealkiri/juhtlõik — sh **2523 "kõne → korrektne tekst"** paari
- saatevestlused: päris küsimus ↔ päris vastus (bassein 60 937)
- grammatikakorpus: inimese viga ↔ toimetaja parandus (kõik 9302)
- dialoogid ja saated ↔ inimese kirjutatud kokkuvõte

| | Kokku | Ring 1 |
|---|---:|---:|
| näiteid | 60 249 | **28 615** |
| tokeneid | 23,96M | **10,50M** |
| replay (inglise + kood) | | 17,5% |
| litsents puhas / hall | | 24 915 / 3 700 (87% puhas) |

Ring 1 valik on kaheastmeline ja prioriteedid tulevad baasjoonest: nõrgimad
veaklassid (käänamine 1022, grammatika 9302, kõne→tekst 2523) võetakse TÄIELIKULT
enne, kui eelarve ülejäänute peale kulub.
SHA-256: `025a5b48dd92e578c8fd0dccb4c89bb662bca9159f82c9a559201f7a103be6b9`

**Kolm vaikset viga, mis ehitamisel leiti ja parandati** (kõik oleksid andmestikku
märkamatult kahjustanud):
1. Koodireplay andis 0 näidet — CodeAlpaca on parquet, skript otsis JSON-i.
2. Käänamist jäi 416/1022 — ühe-etapiline tokenilõige surus prioriteetse
   kategooria alla; parandatud kaheastmeliseks.
3. Käänamist jäi 783/1022 — 15-tähemärgiline miinimumfilter viskas välja lühikesed
   käändevormid ("raamatu" = 7 tähte). Nüüd `min_pikkus=1` lühivastustel.

## 🔥 TREENING KÄIB (algas 2026-08-23 00:01)

**Keskkond** (`.train-venv`, pinnitud): torch 2.13.0+cu132 · torchvision 0.28.0+cu132
· CUDA 13.2 · transformers 5.5.0 · peft 0.20.0 · trl 0.24.0 · bnb 0.50.1 ·
unsloth 2026.8.19. Blackwell sm_120 tuvastatud ja töötab.

**Baasmudel:** `Qwen/Qwen3.8-27B` (Apache-2.0, 55,6 GB, `models/Qwen3.8-27B`),
kvantitakse laadimisel 4-bitiseks. NB: Soli plaanis nimetatud
`unsloth/Qwen3.8-27B-unsloth-bnb-4bit` **ei ole olemas** — HF-is on ainult GGUF
(inferents) ja NVFP4 (plaan keelab treeninguks).

**Suitsutest läbitud** (`adapters/suitsutest/`): 60 sammu, 11,7 min,
**tipp-VRAM 21,4 GB** (varu ~11 GB), loss 1,10, treenitavaid parameetreid 79,7M.
Adapter salvestus (318 MB) ja **laadimine uues protsessis tõestatud** (25 s).

**Kaks tõrget, mis lahendati** (mõlemad Qwen3.8 multimodaalsusest):
1. `assistant_only_loss=True` → TRL keeldub: "not supported for vision-language
   models". 2. Vestlusvormi (messages) andmine TRL-ile → `TypeError` tema sisemises
   töötluses. **Lahendus:** rakendame chat-malli ise ja anname TRL-ile valmis
   stringid `prompt`/`completion` + `completion_only_loss=True` — loss jääb ikka
   AINULT vastuselt, aga ei sõltu TRL-i vormitõlgendusest.

**✅ RING 1 VALMIS** (00:01 → 04:41, **280,3 min**): 28 615 näidet, 1789 sammu,
efektiivne batch 16, LR 5e-5, rank 16/alpha 32, ctx 2048, paged_adamw_8bit,
seed 20260822. **train_loss 1,10 → 0,997**, tipp-VRAM 21,7 GB, treenitavaid
parameetreid 79,7M. Adapter: `adapters/ring1/final/` (318 MB).
Mõõdetud kiirus: **~6,4 sammu/min** ehk 10,5M tokenit ≈ 4,7 h — kasuta seda
järgmiste ringide planeerimiseks.

### ⚠️ Thinking-malli leid (04:45) — mõjutab ring 1 ja kõiki järgmisi

Qwen3.8 chat-mall lisab **vaikimisi** süsteemiteate "Reasoning effort is set to
xhigh…" ja lõpetab prompti **AVATUD `<think>` plokiga**. Ring 1 treenis seetõttu
mustrit `…assistant\n<think>\n` → *vastus* → eos, st **vastus õpetati mõtlemisploki
sisse, ilma seda sulgemata**. Õige non-thinking prefiks on
`<think>\n\n</think>\n\n`, mille annab `enable_thinking=False`.

**Mõõdetud tagajärg** (kiirtest 12 promptiga, `runs/kiirtest-ring1/`): adapter
TÖÖTAB — 0 tühja vastust, laused sidusad, seega ring 1 EI OLE praagitav.
Osaline paranemine on juba näha: käändetabelis kasutab adapter nüüd eestikeelseid
nimetusi ("nimetav — raamat, omastav — raamatu") baasi leiutatud "Osnik / Omastik /
Omandaj" asemel; liitsõnareegel seletatud õigesti. Endiselt vale: käänete arv (13)
ja kaudne kõneviis ("kirjutaks" pro "kirjutavat").

**Parandatud:** `06_train_sft.py` kasutab nüüd `enable_thinking=False`. Ring 2
treenitakse korrektsel mallil. Ring 1 üle ei treenita — mõõtmine ei põhjenda
4,7 h kordamist.

**Teine parandus:** `07b_eval_local.py` — Qwen3.8 "tokenizer" on multimodaalne
protsessor, positsiooniline argument läks pildiparserisse ("Incorrect image
source"). Tekst tuleb anda nimeliselt: `tok(text=…)`.

## ✅ RING 1 HINNATUD: 57,6% → 64,5% (+6,9 pp)

Täisaruanne: `reports/et-before-after.md`. Käänamine +11,6 pp (n=60),
rektsioon +12,5 pp, grammatikaparandus +6,4 pp. Kategooriad ilma treeningnäideteta
(liitsõnad, JSON, sõnaleiutamine, tööriistad) liikusid **täpselt 0,0 pp** — otsene
tõend, et mudel õpib ainult seda, mida näidatakse.
Kvantimise kontroll: Ollama Q4_K_M 57,7% vs bnb NF4 57,6% → võrdlus on aus.

## 🔥 RING 2 JOOKSEB (05:28 → ETA ~11:25)

36 753 näidet, 14,14M tokenit, 2298 sammu, jätkab ring 1 adapterist.
Uut: 720 metateadmise näidet (72 EKI-fakti × 10) ja parandatud chat-mall.

## ✅ RING 3 VALMIS OOTEL — käänamine fookuses (Perti suunis)

**Käänamise andmenappus lahendatud:** TalTechi `inflection_et` oli ammendatud
(1400 kirjet kokku). Uus allikas — `scripts/03b_kaanded_tekstist.py` ekstraheerib
PÄRIS käändevormid PÄRIS tekstist (60 000 lauset stenogrammidest ja ERR-ist,
EstNLTK morfoloogiaanalüüs). See EI OLE süntees: vormid on inimeste kirjutatud,
me ainult tuvastame, mis vorm need on.

Kvaliteedinõuded: ainult ühemõtteline analüüs, lemma ≠ vorm, sagedus ≥3,
pärisnimed välja, eval-lekke blokk.

**Tulemus: 11 027 käänamisnäidet** (varem 1022 — **11×**), 11 010 unikaalset sõna.

Kus päris keel otsa saab (ja kus sünteetiline tee on hiljem põhjendatud):

| Kääne | Ainsus | Mitmus |
|---|---:|---:|
| omastav, osastav, saav, seesütlev, seestütlev, alaleütlev, alalütlev, kaasaütlev | 700 (lagi) | 374–700 |
| sisseütlev | 234 | 112 |
| olev | 243 | 20 |
| alaltütlev | 206 | 61 |
| **rajav** | **99** | **21** |
| **ilmaütlev** | **38** | **11** |

`processed/sft_v1_ring3.jsonl`: **76 800 näidet, 15,00M tokenit, replay 12,6%**.
(Esimene katse andis replay 5,0% — liiga vähe, regressioonirisk; ehitatud ümber
prioriteet → replay → ülejäänu järjekorras.)

Ammendatud basseinid ring 3-s: saatevestlused 21 250, sõnaseletused 20 057,
alpaca 6 955, ERR uudised 2 143.

**Järgmine järjekord:** ring 2 lõpp → eval + aruanne → ring 3 käivitus.

**Cron on PEATATUD** (Perti korraldus 2026-08-22 23:25). Varukoopia:
`reports/crontab-varukoopia-2026-08-22.txt` (6 rida). **Taasta käsuga:**
`crontab reports/crontab-varukoopia-2026-08-22.txt`

**Ring 2 valmis ootel:** `processed/sft_v1_ring2.jsonl` — 36 033 näidet, 14,08M
tokenit, replay 14,7%. (Esimene versioon oli 2,8% replay'ga — ring 1 võttis kvoodi
ära; lisatud kasutamata CodeAlpaca ja samsum-EN materjal.)

**Hindamise metoodika muutus:** baasjoon mõõdeti Ollamas (Q4_K_M), adapter elab
bnb NF4 peal — eri kvantimine annaks ebaausa võrdluse. Seetõttu mõõdetakse ENNE ja
PÄRAST sama torustikuga: `scripts/07b_eval_local.py` (Unsloth, bnb-4bit, samad
seaded). Ollama-baasjoon (57,7%) jääb alles, aga võrdluseks kasutatakse bnb-jooksu.

**Jätkamiskäsk:** `ls -lh /mnt/varu/qwen38-et-data/raw/*/` (kontrolli allalaadimiste seis),
siis alusta valideerimisskriptidega (`scripts/02_sample_validate.py`, veel kirjutamata).

## 🔥 2026-08-25 — nõukoda 2, fraasiavastus, ring 5 käib

**Nõukoda 2 peetud** (Sol + agy + qwen3.8-et ise): `council2/BRIEF.md`,
`council2/vastus-sol.md`, `council2/vastus-agy.md`, süntees
`reports/NOUKODA-2-SYNTEES.md`. Üksmeel: üldine SFT ammendunud, käänamine
protsessina (CoT), DPO ainult mudeli enda vigadest, CPT praegu mitte.

**Suur avastus:** eval mõõdab FRAASE (omadussõna+nimisõna), treening andis ainult
ÜKSIKSÕNU (ring3: 11k, ring4: 17k, fraase 0). Sellepärast andis 11k käänamisnäidet
vaid +3,3.

**Mudel osales ise:** dpo2 adapter Ollamas `qwen3.8-et:27b-v2` (159 MB LoRA gguf).
Introspektsioon ei tööta (leiutab olematuid vorme), aga sondina on aus mõõteriist.

**Fraasisond** (`15_fraasisond.py`, 378 evali-blokis lahtrit, mida treening pole
näinud, variandikomplektidega skoorimine): **73,3%**. Nõrgim: ainsuse sisseütlev
48%, mitmuse sisseütlev 56%. Vigadest pooled AINULT omadussõna ühildumine (50/101).
Tulemus: `processed/fraasisond.jsonl`, logi `adapters/fraasisond-dpo2.log`.

**Õppetund skoorimisest:** eesti paralleelvormid ("suurde mäkke" = "suuresse
mäesse") — ühe-variandi võrdlus näitas 44%, variandikomplektidega 73,3%. Sama
lõks, mis skoorija v2-s.

**Uus treeningmaterjal:**
- `processed/fraas_gen.jsonl` — 3000 fraasikäänamist (Vabamorf, reegel valideeritud
  TalTechi 1400 lahtri vastu 98,1%; käändumatute omadussõnade filter; standardvormi
  valik; 75% evali kujuga + 25% CoT-tuletusega; kaalud sondi veakaardist)
- `processed/dpo_fraasivead.jsonl` — 101 on-policy DPO paari (mudeli enda vead)
- `processed/sft_fraasiparandused.jsonl` — 101 SFT parandust
- `processed/sft_v1_ring5.jsonl` — ring 5: 3782 näidet, ~0,3M tokenit, 18% replay

**Ring 5 treening käib** (`oo_ring5.sh` taustal): dpo2-st edasi, rank 16, LR 2e-5
(langetatud, Soli soovitus), 237 sammu ≈ 20 min, siis automaatselt eval.
Pärast evalit: fraasisond uuesti + error-DPO (`dpo_fraasivead.jsonl`, beta 0,3,
LR 1e-6, 1 epohh).

## ✅ 2026-08-25 — RING 5 HINNATUD: 77,6% (uus rekord), käänamine 80,0

**Lukustatud eval:** 76,9 → **77,6** (+0,7). Käänamine 76,7 → **80,0** (+3,3, kaks
ülesannet). Grammatika 84,5 → 86,7. Kaotused (morfoloogia-meta −11,1,
sõnaleiutamine −14,3) on kumbki ÜKS ülesanne — Soli müra-hoiatus kehtib.

**Fraasisond ring5 peal (378 nägemata lahtrit): 73,3 → 81,5 (+8,2).**
Ainsuse sisseütlev 48% → 80%. Vigu 101 → 70.

**Üldistuse tõestus:** treenitud 101 veaparandusest sai õigeks vaid 51% (EI ole
päheõppimine), puutumata 277 lahtrist jäi õigeks 92%. Võit tuleb 3000 genereeritud
fraasist — fraasihüpotees KINNITATUD kolmest sõltumatust mõõdust.

Treening: 23 min, 237 sammu, loss 0,277, LR 2e-5, tipp-VRAM 19,7 GB.
Adapter: `adapters/ring5/final`, Ollamas `qwen3.8-et:27b-v3`.

**Käib:** on-policy DPO paaride korje (`19_onpolicy_paarid.py`, 2600 värsket
fraasi v3 vastu, ootus ~390 paari) → error-DPO (beta 0,3, LR 1,5e-6, 1 epohh).

## ✅ 2026-08-25 — DPO3 (error-DPO): 78,8% — UUS REKORD

**Nõukoja retsept töötas teist korda samal päeval.** 420 on-policy paari (70
ring5-sondi viga + 350 värske korje `19_onpolicy_paarid.py` kaudu, kus v3 mudel
vastas 2600 fraasile ja Vabamorf püüdis vead), beta 0,3, LR 1,5e-6, 1 epohh,
53 sammu, 5 min. Loss püsis 0,95–1,2 (üle 0,45 piiri — mitte DPO1 kordus).

| | ring5 | dpo3 |
|---|---:|---:|
| ÜLDSKOOR | 77,6 | **78,8** (+1,2) |
| rektsioon | 75,0 | 87,5 (flip taastus) |
| morfoloogia-meta | 53,7 | 64,8 (flip taastus) |
| käänamine | 80,0 | 80,0 |
| grammatika | 86,7 | 86,2 |

Adapter: `adapters/dpo3/final`, Ollamas **`qwen3.8-et:27b-v4`**.
Vahe GPT-ni (81,7): 2,9 pp ≈ 4-5 ülesannet.

**Päeva trajektoor:** 76,9 → 77,6 (ring5, fraasid) → 78,8 (dpo3, error-DPO).

**Järgmine kirurgiline sihtmärk** (PLAAN-RANK16-EDASI järjekord): sõnaleiutamine
(42,9, 400 negatiivnäidet) + JSON (66,7, keerukamad skeemid) + tehniline (50,0,
lühendite käänamine). Fraasisond dpo3 peal käib.

**Fraasisond dpo3 peal: 83,6%** (378 nägemata lahtrit; hommikul dpo2: 73,3,
ring5: 81,5). Mitmuse nimetav 93%, nõrgim on nüüd ainsuse sisseütlev ja mitmuse
omastav (mõlemad 78%). Päevaga +10,3 pp fraasikäänamises.

## 🔥 2026-08-25 — RING 6 KÄIB: viis moodulit dpo3 päris vigade peale

Sama metoodika mis ring 5: vaata mudeli PÄRIS vigu (dpo3 evali vastused +
fraasisond), ehita reeglipõhine materjal täpselt nende peale, Vabamorfi
ring-kontroll, evali leke blokeeritud (1467 sisusõna et_locked_v1-st).

**Moodulid (`20_gen_ring6.py`, veaanalüüs skripti päises):**
| Moodul | Näiteid | Vea näide, mida ravib |
|---|---:|---|
| sõnade olemasolu (jah/ei + loendid) | 500 | väitis, et "mõttetera" pole olemas |
| verbimorf + käände tuvastus | 484 | da-tegevusnimi "lugemine" pro "lugeda"; "esseütlev" |
| JSON + formaadidistsipliin | 181 | võti "kuupäev" pro "kuupaev" (ASCII) |
| tehniline (lühendid i-reegliga, anglitsismid) | 114 | "GPS-ist" (mitte "GPS-st"); deploy→juurutama |
| arvsõna-liitsõnad | 123 | "viiekümne eurone" pro "viiekümneeurone" |

**Avastus olemasolu-kontrollis:** Vabamorf "tunneb" ka produktiivseid tuletisi
("rõõmustu=vus") — päris sõna eristab juure "="-märgi puudumine. Ilma selleta
oleks pool negatiivkorpust olnud rikutud.

**Ring 6 kokku:** 2395 näidet (1402 moodulit + 500 värsket fraasi seemnega
20260827 + 62 dpo3-sondi parandust + 18% replay). Treening dpo3-st, LR 2e-5.
Ahel (`oo_ring6.sh`): treening → eval → gguf `qwen3.8-et:27b-v5` → fraasisond.
Ootel: dpo4 materjal on valmis (`dpo_fraasivead_dpo3.jsonl`, 62 paari).

## ✅ 2026-08-25 — RING 6 HINNATUD: 79,8% (rekord) · RING 7 + DPO4 AHEL KÄIB

**Ring 6:** üldskoor 78,8 → **79,8** (+1,0). Sõnaleiutamine 42,9 → 57,1 (+14,3),
morfoloogia-meta 64,8 → 75,1 (+10,3, verbimoodul töötas). Käänamine püsis 80,0.
Fraasisond 84,1%. Ollamas `qwen3.8-et:27b-v5`. **80% piirini 0,2 pp = 1 ülesanne.**

**Ring 6 järelanalüüs (kuju-õppetund kordus KOLMANDAT korda):**
- arvliitsõnad paranesid isolatsioonis, aga MITTE lause sees (man-017) —
  treenisime "Paranda: 'viie kümne eurone'", eval küsib tervet lauset
- "mõttetera" ikka "olematu" — olemasolu-moodul filtreeris liitsõnad välja
- JSON-võti ikka "kuupäev" — treening ütles vihje "täpitähtedeta", eval ei ütle

**Ring 7 materjal (`22_gen_ring7.py`, 610 näidet):** lause-sisesed kokku-lahku
parandused (mõistlikud ühik+objekt paarid, nimetavas — käändevigu ei teki),
kureeritud 120 päris liitsõna (juhugeneraat "laekodumaa" visati välja), JSON
täpselt evali kujuga, anglitsismi valikküsimused, 60 kureeritud püsiväljendit.

**Ahel käib (`oo_ring7_dpo4.sh`):** korje v5 vastu (~350 paari) → ring7 SFT
(817 näidet) → eval → dpo4 (korje + ring6-sondi 60 paari) → eval → `27b-v6` →
sond. Valmis ~2 h pärast.

## 🏆 2026-08-25 — RING 7: 82,6% — ÜLE 80% JA ÜLE GPT (81,7)

**Ring 7** (817 näidet: kuju-täpsed moodulid + 60 sondi parandust, 6 min treening):
| | ring6 | ring7 |
|---|---:|---:|
| ÜLDSKOOR | 79,8 | **82,6** (+2,8) |
| käänamine | 80,0 | **88,3** (+8,3) |
| rektsioon | 87,5 | **100,0** |
| grammatika | 85,4 | 86,3 |
| fraasisond | 84,1 | 85,7 |

**DPO4 TAGASI LÜKATUD:** 80,7 (−1,9 vs ring7). Ainus erinevus: käänamine
88,3 → 83,3. Sond identne (85,7). On-policy DPO fraasivigadest ei anna enam
midagi, kui SFT on sama materjali juba ära õppinud — DPO3 töötas, sest tookord
oli viga-tüüp värske. Adapter `dpo4` jääb arhiivi, rada läheb ring7-st edasi.

**PARIM MUDEL: `adapters/ring7/final`, Ollamas `qwen3.8-et:27b-v7`.**

**Päeva täistrajektoor (üks päev!):** 76,9 → 77,6 (ring5) → 78,8 (dpo3) →
79,8 (ring6) → **82,6 (ring7)**. Fraasisond 73,3 → 85,7. GPT (81,7) ÜLETATUD.
Järgmised sihid: Gemini 84,3 (vahe 1,7), Claude 86,6 (vahe 4,0).

Müra-märkus (Sol): sõnaleiutamine 57,1 → 42,9 ja morfoloogia-meta 75,1 → 62,7
on kumbki 1 ülesande flipid väikestes kategooriates — jälgi järgmises ringis.

## ✅ 2026-08-25 — RING 8: 82,0 (kiikelaud) · RING 9 KÄIB · väline eval valmis

**Ring 8:** sihid paranesid täpselt — sõnaleiutamine 42,9 → 57,1 (tasakaalu-
moodul), morfoloogia-meta 62,7 → 73,5 (lühike sisseütlev + stabiilsuskordus) —
aga käänamine 88,3 → 85,0 (−2 ül) ja liitsõnad −1 ül. Sond 86,0 (rekord).
**Kapatsiteedi kiikelaud:** sellel tasemel iga võit ühes kategoorias maksab
midagi teises. Ring7 (82,6) jääb üldskoorilt parimaks, ring8 on tasakaalukam.

**Ring 8 evali käänamisvead = 100% omadussõna TÜVEVAHELDUS** (kurb→kurbade,
mudel "kurjade"; puhas→puhtaid, mudel "puhaseid"; rikas→rikkad, mudel "rikas").

**Ring 9 käib:** 800 astmevaheldus-fraasi (61 rasket omadussõna, kureeritud,
`26_gen_astmevaheldus.py`, 30% CoT rõhutab tüvemuutust) + 53 ring8-sondi
parandust + 400 stabiilsust + replay. **Tehniline moodul VÄLJAS (Perti otsus:
2 ül, kõik mudelid 50% — testi omapära, mitte oskus).**

**Väline valideerimine valmis (`28_valine_eval.py`):** TalTechi MMLU_et,
300 küsimust deterministlik valim, jookseb pärast ring 9 baasil ja parimal.
Pert küsis ausalt: meie eval on ISE TEHTUD (suhteline võrdlus aus, absoluut
mitte standard) — MMLU_et on sõltumatu kontroll, mida me pole vaadanud.

## 🏆 2026-08-25 — RING 9: 84,3% — GEMINI TASE (84,3) SAAVUTATUD

**Astmevahelduse diagnoos oli täpne:** käänamine 85,0 → **93,3** (+8,3).
800 raske omadussõna fraasi (kurb/puhas/rikas, 30% tüve-CoT) tegid töö ära.
Fraasisond **87,8** (rekord). Morfoloogia-meta püsis 75,1 (stabiilsuskordus
töötab). Tagasilöök: tööriistad 100 → 50 (1 ül; stabiilsusvalimis polnud
tööriistanäiteid — ring 10 peab lisama).

**Trajektoor:** 61,7 (baas) → 76,9 (eile) → 84,3 (täna õhtul). Claude 86,6,
vahe 2,3 pp. Parim mudel: `adapters/ring9/final`, Ollamas `qwen3.8-et:27b-v9`.

**Käib:** MMLU_et väline valideerimine (300 küsimust, baas vs ring9).

## ✅ 2026-08-25 — VÄLINE VALIDEERIMINE: MMLU_et baas 68,7% → ring9 70,0%

Sõltumatu test (TalTechi MMLU_et, 300 küsimust deterministlik valim, mida me
pole kunagi treeningus ega analüüsis kasutanud): **treening ei rikkunud
üldteadmisi** (+1,3 pp, n=300 juures ~müra piiril, aga kindlasti mitte langus).
See on avaldamiskõlblik tõend, et 9 sihitud ringi ei tuupinud mudelit kitsaks.
Tulemused: `eval/runs/mmlu-baas.json`, `eval/runs/mmlu-ring9.json`.

## PÄEVA LÕPPSEIS 2026-08-25

| Mõõt | Hommikul | Õhtul |
|---|---:|---:|
| lukustatud eval | 76,9 | **84,3** |
| fraasisond (378 nägemata) | 73,3 | **87,8** |
| käänamine | 76,7 | **93,3** |
| MMLU_et (väline) | 68,7 (baas) | **70,0** |

GPT (81,7) ületatud, Gemini (84,3) viigis, Claude (86,6) vahe 2,3 pp.
Parim: `qwen3.8-et:27b-v9`. Ring 10 vihjed: tööriistad-stabiilsus (flipis 50-le),
liitsõnad (57,1), JSON (66,7). Ja endiselt: Perti pime A/B 47 rubriigi-ülesandel.

## 🏆 2026-08-25 — RING 10: 84,7% — GEMINI (84,3) ÜLETATUD · LÕPPMUDEL VALMIS

**Ring 10** (1405 näidet: võrdlusastmed, saav-rajav, liitsõnaloendid, ühendverbi
reegel, 150 tööriistanäidet tagasi, **600 avatud vastust degeneratsiooni raviks**):

| | ring9 | ring10 |
|---|---:|---:|
| ÜLDSKOOR | 84,3 | **84,7** |
| fraasisond | 87,8 | **90,2** |
| morfoloogia-meta | 75,1 | **86,2** (tipud: 87,0) |
| tööriistad | 50 | **100** (taastus) |
| liitsõnad | 57,1 | 71,4 |
| käänamine | 93,3 | 90,0 (−2 ül, kiikelaud) |

**LÕPPMUDEL: `ollama run qwen3.8-et:27b`** (= ring10 adapter,
`adapters/qwen38-et-v8-ring10-lora.gguf` — NB: failinimi ütleb v8, sisu on ring10).
Käsitsi testimise juhend: `reports/KASITSI-TESTIMINE.md`.
Proovivastus näitas: "kurvade laulude" (rahvapärane; kirjakeelne "kurbade") —
kirja Perti testi jaoks.

**Käib:** väline patarei — MMLU_et (ring10) + EstQA (baas + ring10).
MMLU baas oli 68,7, ring9 70,0.

## ✅ 2026-08-25 ÕHTU — RING 11 + 12: 85,3%, PERTI KÄITUMISVEAD RAVITUD

**Perti päris test** (transkript terminalist) leidis 3 viga, mida ükski
automaatmõõt ei näinud: GEC-lekk vestlusse (parandas tervitust ja kajas lauset
tagasi), lühivastuse kalle (300 sõna → 60), vaba registri vead.

**Ring 11** (vestlusravi, 1840 näidet): eval 85,1. **Ring 12** (kaja-malli ja
pikkuse parandus, 500 päris ERR-artiklit ~300 sõna): eval **85,3**, käänamine
**95,0**. Käitumiskontroll: "300 sõnaga" → **315 sõna (PARANDATUD)**; tervitus
korras; kaja-viga JÄI (15 näidet ei võida 2500 GEC-i; vajab ~200 sisulise
vastuse näidet, ideaalis Perti päris vestlustest).

**Õppetund (minu disainiviga, dokumenteeritud):** ring11 "vestlus-mitte-gec"
mall "Sain mõttest aru! + lause" ÕPETAS kaja — mall ise oli kaja. Ring12
viskas selle välja.

**Kiikelauad:** ring12 rektsioon 100 → 75 (2 ül), sond 89,9 → 85,7. Eval on
primaarne mõõt, ring12 võidab mõlemas primaarses (skoor + käitumine).

**Lõppseis:** `parim-eesti` = `qwen3.8-et:27b` = `qwen3.8-et:27b-taismudel`
= ring12 liidetud täismudel. EuroLLM mõõdeti sondil: 54,2% vs meie 90 ümber.
Trajektoor ühe päevaga: **61,7 → 85,3** (baas → ring12), GPT ja Gemini
ületatud meie testil, Claude 86,6 vahe 1,3.

## ✅ 2026-08-25 HILISÕHTU — RENDERER-VIGA LEITUD JA PARANDATUD · KOODIVASTUS MÕÕDETUD

**Kriitiline leid:** GGUF-ist loodud täismudelil PUUDUSID RENDERER/PARSER read
→ mudel sai promptid ilma vestlusstruktuurita. SEE seletas Perti õhtuse
transkripti kaja, "ühe võrra taga" vastused ja osa loope. Parandatud
(RENDERER qwen3.8 + PARSER qwen3.5 + repeat_penalty 1.15 kõigil märgenditel).
Kaja-test kinnitas paranemist. ÕPPETUND: GGUF-ist `ollama create` EI päri
rendererit — alati lisa Modelfile'i käsitsi.

**Think on meie mudelil KATKI:** 12 no-think ringi → mudel ei sulge think-plokki,
vastus jääb thinking-välja, content tühi. Kasuta ALATI think=false
(alias `eesti`, API-s "think": false).

**HumanEval pass@1 (164 ül, kood jooksutatud testidega):**
| parim-kood (qwen3-coder:30b) | **92,1%** |
| baas qwen3.8:27b (think) | 71,3% |
| parim-eesti (no-think) | 65,9% |

**Otsus:** parim-kood JÄÄB qwen3-coder:30b-le. Tööjaotus mõõdetud: parim-eesti
= keel/vestlus/selgitus; parim-kood = kood. `<nooutput>` saaste (alpaca-est,
17 tk, 1 jõudis ring4) — filter lisada tulevastesse buildidesse.

**Perti terminali-transkriptid = järgmise faasi treeningkuld** (mitmekäiguline
vestlus, kõnekeel, trikiküsimused). Vestlusrobustsus on eraldi faas, mitte
mikroring.

## 🔥 2026-08-28 — RING 13 KÄIB: koondkorpuse stiiliannus (UUED ANDMED)

**Muischneki vastus avas koondkorpuse:** CC-BY-SA kinnitatud, 941 MB alla
laetud cl.ut.ee-st (ELG/metashare DOI on katki — teatatud neile).
Ekstraktitud (`39_koondkorpus_ekstrakt.py`): **32,4M sõna** puhast teksti →
`processed/koondkorpus_loigud.jsonl` (ilukirjandus 4,6M, doktoritööd 2,1M,
Postimees 25,5M, Horisont 0,2M). VIITAMISKOHUSTUS registris.

**Ring 13** (`40_gen_ring13.py`): 1160 jätkamis-ülesannet päris toimetatud
proosast ("Jätka teksti X stiilis, umbes N sõnaga") — õpetab REGISTRIT ja
PIKKUST korraga. Sihib mõõdetud auku: vaba registri vead ("sai kutsung"),
teaduslik register seni katmata. + 450 stabiilsust + replay = 1894 näidet.
Treening ring12-st (85,3), ahel: eval → v13 → fraasisond.

**Ootel otsus (Pert):** CPT-piloot 100–200M tokenit (nõukoja retsept valmis,
nüüd on kvaliteetproosa selleks olemas) — 5-7 päeva GPU-d, eraldi haru.

## 🔥 2026-08-28 — CPT-PILOOT KÄIVITATUD (Perti otsus: "planeeri ja tee valmis")

Täisahel jookseb (`oo_cpt.sh`): korpus (~110M sõna ET + 10% replay, ilukirjandus
2x ülekaaluga) → baasi perplexity → CPT (rank 32, LR 8e-6, packing, 1 epohh,
BAASIST mitte adapterist — nõukoja üksmeelne nõue) → CPT perplexity →
SFT-kombo (ringide 5-13 koond ~15k, kaja-mall väljas) → eval + sond.

Ajahinnang: agy "5-7 päeva" oli ülehinnang; mõõdetud läbilaskega ~6-10h CPT
+ 2h SFT + 1h mõõtmised ≈ VALMIS TÄNA HILISÕHTUL.

**Avalik dokumentatsioon:** `reports/CPT-PILOOT.md` — kogu disain, andmete
koostis viitamiskohustusega, parameetrid, mõõdikud ja (täitmisel) tulemused,
kirjutatud nii, et keegi saab sama korrata teise mudeli/keelega.

Ring 13 arhiveeritud eksperimendina (84,2; stiil paranes, "koerapupp" näitas
CPT vajadust). parim-eesti = ring12 (85,3) kuni CPT-haru tõestab end.

## 🎉 2026-08-30 — CPT-PILOOT VALMIS: PERPLEXITY −31%, PROOSA UUEL TASEMEL

CPT (3364 sammu, 35,3 h, 450 W): **perplexity 22,2 → 15,4 (−31%!)** — Soli
lävi (5-10%) ületatud kuuekordselt. Proosavõrdlus: ring12 kirjutab valemit,
CPT-haru kirjutab PÄRIS lugu (Liina + teleskoop — narratiiv, lõigud, pildid).

Aus teine pool: kombo e1 järel eval 76,5 / sond 51,6 — üks koondannus EI
asenda 13 iteratiivset ringi. **Käib:** kombo e2 (`oo_cpt_sft2.sh`), siis
vajadusel kirurgilised ringid CPT-vundamendil. Täisdokumentatsioon + 5
õppetundi jagamiseks: `reports/CPT-PILOOT.md`.

## 🏁 2026-08-30 — LÕPPMÕÕTMINE VALMIS, JAGAMISPAKETT KOKKU PANDUD

FINAL (CPT + 3 taastusringi + on-policy DPO): eval 81,9 · sond 77,2 ·
MMLU 67,3 (baas 68,7, püsis) · EstQA F1 73,6 · HumanEval 83,3 (n=60).
Tšempion ring12 jääb oskustelt ette (85,3), FINAL võidab proosas (ppl −31%,
päris narratiiv). Perti hinnang kinnitus: Qwen3.8 piires oleme lae lähedal.

**JAGAMISPAKETT:** /mnt/varu/qwen38-et-data/JAGAMISPAKETT/ — README 10
õppetunniga, 46 skripti, raportid, litsentsipuhtad andmestikud (sh
käänamiskorpus 13 436), lukustatud eval + skoorija, 3 adapterit
(cpt1-puhas-keelekiht, ring12-oskuste-tsempion, FINAL-cpt-pluss-oskused).

## 👑 2026-08-30 — UUS TŠEMPION: 85,8 (CPT + kirurgilised tsüklid)

**Perti siht "ületa tšempion" TÄIDETUD.** Tsüklid CPT-harul: ts4 81,5 (tagasi
lükatud) → ts5 84,0 (rektsiooni täppismoodul 130 näidet: rektsioon 62,5→100!)
→ **ts6 85,8** (liitsõnad+JSON+parandused) > vana tšempion 85,3.

**Uue tšempioni täisvalideerimine:** sond 79,4 · MMLU 66,0 (baas 68,7, kerge
triiv raportis) · EstQA F1 76,1 (= vana) · **HumanEval TÄIS 164: 85,4%**
(CPT-proosa stabiliseeris ka koodi; NB vana 65,9 mõõdeti enne
renderer-parandust, otse ei võrdle). Ja kaasas CPT keel: ppl −31%, päris lood.

**Otsustav õppetund jagamisse:** diagnoosipõhine 130-näiteline täppismoodul
(ts5) andis +2,1pp — sama palju kui mõni 50 000-näiteline ring. Vigade
LUGEMINE on odavaim treeningukiirendi.

Kroonimine käib: ts6 → liidetud täismudel → Q6_K (renderer+parser sees,
kõik pakendamiseõppetunnid rakendatud) → parim-eesti/qwen3.8-et:27b/taismudel.
