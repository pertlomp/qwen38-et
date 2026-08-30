# qwen38-et — Estonian post-training for open LLMs / eesti keele järeltreening avatud mudelitele

**EN below · Eesti keeles all**

---

## 🇬🇧 English

A complete, reproducible pipeline for teaching an open LLM (Qwen3.8-27B) proper
Estonian on a single consumer GPU (RTX 5090, 32 GB), with every step measured
and every failure documented.

**Results:** Estonian skills score 61.7% → **85.8%** on a locked 200-task eval
(surpassing GPT and Gemini on the same test); fiction perplexity **−31%** after
131M tokens of continued pretraining on edited Estonian prose; HumanEval 85.4%
retained. Full comparison tables in `reports/`.

**What's in this repo:**
- `scripts/` — 48 numbered Python scripts + orchestration chains: data
  processing, rule-based generators (validated against ground truth via the
  Vabamorf morphological analyser), QLoRA SFT/DPO/CPT training, locked eval,
  a self-probing loop where the model's own errors become the next training
  round, and external benchmarks (MMLU-et, EstQA, HumanEval).
- `reports/` — the full lab journal (STATUS.md), CPT methodology with honest
  lessons (CPT-PILOOT.md), expert-council synthesis, final comparison report.
- `eval/` — the locked 200-task Estonian eval (SHA-256) + variant-aware scorer.
- `datasets/` — licence-clean training data: an Estonian inflection corpus
  (11,011 entries with per-entry source and licence), rule-generated phrase
  inflections, skill modules. Entries with unresolved licences are withheld
  until cleared.
- **Adapters & merged models:** on Hugging Face (link added on publication) —
  three artifacts: the pure CPT language layer (research object in its own
  right), the 13-round skills path, and the final champion (CPT + surgical
  rounds).

**The 11 most expensive lessons** (short version — full text in the README of
the release package):
1. Training example *shape* must match usage shape (word-level drills don't
   teach phrase-level agreement).
2. Estonian parallel forms break naive scoring (−29pp measurement error).
3. Small targeted doses beat large general ones (720 examples > 81,268).
4. The model's own errors are the best training data; the iterative loop is
   itself part of the learning (same data as one batch: −9pp).
5. DPO only on-policy, only on fresh error types.
6. CPT and SFT do different jobs: CPT gives the language, SFT the skills.
7. TRL `packing=True` can silently fail with multimodal processors.
8. Real throughput (27B QLoRA, 1×5090 @450W): ~870 tok/s. Plan honestly.
9. GGUF→Ollama loses RENDERER/PARSER unless set explicitly.
10. A 130-example diagnosis-driven module gave +2.1pp. Read errors first.
11. Verify quantization and think-mode separately on the packaged model.

**Reproducing with another language/model:** see the 7-step recipe at the end
of this file.

*This work is non-commercial. Its purpose: a small language should be as good
in open models as in paid ones, and this work should carry forward into future
models.* Contact: pertlomp@gmail.com

---

## 🇪🇪 Eesti keeles

Täielik ja korratav torustik, millega õpetada avatud keelemudelile
(Qwen3.8-27B) korralik eesti keel ühe tavalise GPU peal (RTX 5090, 32 GB) —
iga samm mõõdetud, iga ebaõnnestumine dokumenteeritud.

**Tulemused:** eesti oskuste skoor 61,7% → **85,8%** lukustatud 200-ülesandelisel
testil (ületab GPT-d ja Geminit samal testil); ilukirjanduse perplexity **−31%**
pärast 131M tokeni jätku-eeltreeningut toimetatud proosal; HumanEval 85,4%
säilinud. Täistabelid kaustas `reports/`.

**Mis repos on:**
- `scripts/` — 48 nummerdatud skripti + ahelad: andmetöötlus, reeglipõhised
  generaatorid (Vabamorfiga ring-kontrollitud), QLoRA SFT/DPO/CPT treening,
  lukustatud eval, isesondiv tsükkel (mudeli enda vead → järgmine ring) ja
  välised testid.
- `reports/` — täielik laboripäevik (STATUS.md), CPT metoodika ausate
  õppetundidega, nõukoja süntees, lõppvõrdlus suurte mudelitega.
- `eval/` — lukustatud 200 ülesandega test (SHA-256) + rööpvorme arvestav skoorija.
- `datasets/` — litsentsipuhtad treeningandmed: käänamiskorpus (11 011 kirjet,
  igal kirjel allikas ja litsents), fraasikäänamised, oskusmoodulid.
  Määramata litsentsiga kirjed on avaldamisest väljas, kuni õigused selguvad.
- **Adapterid ja liidetud mudelid:** Hugging Face'is (link lisatakse
  avaldamisel) — kolm artefakti: puhas CPT-keelekiht, 13 ringi oskuste rada
  ja lõpptšempion.

**11 kõige kallimat õppetundi:** vt ingliskeelne loend üleval ja täistekst
`reports/` all — kuju vastab kasutusele; rööpvormid murravad skoorimise;
väike sihitud võidab suure üldise; mudeli enda vead on parim materjal;
DPO ainult on-policy; CPT annab keele, SFT oskused; packing-lõks; päris
läbilaskevõime; renderer-lõks; 130-näiteline täppismoodul = +2,1pp;
kontrolli pakendatud mudelit eraldi.

**Kordamine teise keele või mudeliga (7 sammu):**
1. Ehita väike lukustatud test oma keele nõrkuste peale (skriptid 05, 08)
2. Mõõda baas, leia suurimad augud (07b)
3. Reeglipõhine generaator + morfoanalüsaator kontrolliks (03, 16, 26)
4. Kirurgilised ringid mudeli enda vigadest (15 → 17 → 06), à 2–3 h
5. On-policy DPO värskete vigade peal (19 → 14)
6. CPT kvaliteetproosaga, kui SFT lagi käes (42–44, 46)
7. Välised testid ausaks kontrolliks (28, 31, 38)

*See töö on tehtud ilma majandusliku huvita. Eesmärk: väike keel olgu avatud
mudelites sama hea kui tasulistes, ja tehtud töö kandugu edasi tulevastesse
mudelitesse.* Kontakt: pertlomp@gmail.com

## Litsents / License

Code & methodology: MIT. Datasets: per-entry licence field (CC-BY-SA parts
require attribution to the Estonian Reference Corpus, University of Tartu;
rule-generated parts are free). Reports: CC-BY 4.0.
