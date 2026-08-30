# Lõppraport: qwen3.8-et vs suured pilvemudelid — 2026-08-25

**Meie mudel:** Qwen3.8-27B + LoRA (rank 16), 10 treeningringi + 1 error-DPO,
kõik ühe RTX 5090 peal. Lõppversioon: `ollama run qwen3.8-et:27b` (= ring10).

## 1. Meie lukustatud eval (200 ül, 151 automaatskooritud, ISE TEHTUD test)

Kõik mudelid vastasid täpselt samale testile samade reeglitega.

| Kategooria (n) | baas | **meie (ring10)** | GPT | Gemini | Claude |
|---|---:|---:|---:|---:|---:|
| käänamine (60) | 51,7 | **90,0** | 96,7 | 96,7 | 96,7 |
| grammatikaparandus (50) | 80,2 | **86,3** | 71,1 | 76,8 | 85,9 |
| morfoloogia-meta (9) | 11,6 | **86,2** | 87,0 | 87,0 | 87,0 |
| rektsioon (8) | 87,5 | **87,5** | 87,5 | 100 | 100 |
| liitsõnad (7) | 57,1 | **71,4** | 71,4 | 71,4 | 57,1 |
| sõnaleiutamine (7) | 57,1 | **57,1** | 57,1 | 57,1 | 57,1 |
| JSON (6) | 66,7 | **66,7** | 66,7 | 66,7 | 66,7 |
| tööriistad (2) | 50,0 | **100** | 50,0 | 50,0 | 50,0 |
| tehniline (2) | 50,0 | **50,0** | 50,0 | 50,0 | 50,0 |
| **ÜLDSKOOR** | 61,7 | **84,7** | 81,7 | 84,3 | 86,6 |

Lisamõõt, fraasisond (378 nägemata käänamislahtrit): meie 90,2%
(esimene mõõt treenitud mudelil oli 73,3; puhas baas jäi sondimata).

## 2. Välised testid (MITTE meie tehtud — TalTechi avalikud testid)

Samad deterministlikud valimid kõigile (MMLU_et 300 küsimust, EstQA 200).

| Test | baas Qwen | **meie (ring10)** | GPT | Gemini | Claude |
|---|---:|---:|---:|---:|---:|
| MMLU_et (teadmised, valikvastused) | 68,7 | **68,7** | *(1)* | 91,7 | 90,3 |
| EstQA F1 (lugemine, täpne väljavõte) | 86,9 | **76,1** | *(1)* | 95,2 | 92,4 |
| EstQA EM (täpne vaste) | 73,5 | **55,0** | *(1)* | 92,5 | 87,4 |

*(1)* GPT väline mõõt ootab: Codexi kasutuslimiit taastub 31.08.
(GPT rida meie evalis on olemas — see mõõdeti enne limiiti.)

## 3. Mida see tervikuna tähendab (aus lugemine)

**Kus me päriselt võitsime:**
- Käänamine 51,7 → 90,0 ja grammatikaparandus, kus me **edestame GPT-d ja
  Geminit** ka absoluutselt — kohalik eesti treeningandmestik teeb seda, mida
  suured pole näinud.
- Üldskoor meie testil 84,7: üle GPT (81,7) ja Gemini (84,3), Claude'i (86,6)
  vahe 1,9.
- MMLU_et püsis täpselt baasi tasemel — 10 treeningringi EI rikkunud
  üldteadmisi.

**Kus suured on selgelt ees (välised testid):**
- MMLU_et ~91 vs meie 68,7 — see on 27B lokaalse ja frontier-mudeli teadmiste
  vahe, mida keeletreening ei muuda ega peagi muutma.
- EstQA: suured 92–95 F1, meie 76,1 — JA see on baasist (86,9) MADALAM.

**Ausaim leid: EstQA taandareng (−10,8 F1).** Drilli-treening õpetas mudeli
vastuseid "ilusaks tegema" (lisab sõnu ümber täpse tekstilõigu: küsiti
"aprikoosidest", mudel ütles "aprikoosidest valmistatud ekstraktid").
Sisu on õige, täpne väljavõte mitte. Parandusrada on teada: EstQA TRAIN-osa
(ei kattu testiga) annuseks järgmisse ringi.

**Meie testi piirid:** 84,7 on MEIE testil, mille veatüüpide järgi me treenisime
(ülesande-leke blokeeritud, aga kategooria-fookus on päriselt "testiks
õppimine"). Välised testid ongi selle aususe kontroll — ja need näitavad
mõlemat: võidud on päris (MMLU ei langenud), aga kitsad (EstQA maksis lõivu).

## 4. Perti käsitsi test

`reports/KASITSI-TESTIMINE.md` — kuus ala, konkreetsed küsimused, baasi
võrdluskäsk. Esimene teadaolev nüanss: mudel ütleb "kurvade" (rahvapärane),
kirjakeelne on "kurbade".

## 5. Failid

- Mudel: `qwen3.8-et:27b` (Ollama), adapter `adapters/ring10/final`
- Meie eval: `eval/runs/*/skoor.json` · Sond: `processed/fraasisond-*.jsonl`
- Välised: `eval/runs/mmlu-*.json`, `eval/runs/estqa-*.json`,
  `valised/{agy,claude}/skoor.json`
- Kogu metoodika: skriptid 01–32, `reports/STATUS.md`, `reports/NOUKODA-2-SYNTEES.md`
