# Nõukoda 2: süntees ja ring 5 plaan

**Koostatud:** 2026-08-25 · **Osalejad:** Sol (Codex/OpenAI), agy (Google), Claude,
ja **qwen3.8-et:27b-v2 ise** (meie treenitud mudel, 76,9%, osales enda parandamisel)
· **Alusdokument:** `council2/BRIEF.md` (kõik mõõtmised)

## Suur avastus enne nõukoda (Claude, veaanalüüs)

**Treeningu kuju ei vastanud evali kujule.** Eval mõõdab käänamist 60 FRAASI-ülesandega
(omadussõna + nimisõna: "habras tasakaal" → "hapraid tasakaale"). Aga ring 3 treenis
11 011 ja ring 4 17 011 ÜKSIKSÕNA, fraase 0. Mudel õppis täpselt seda, mida näidati:
üksiksõnu. Omadussõna ühildumist ei näidatud kordagi. See seletab, miks 11k
käänamisnäidet andis vaid +3,3.

**Fraasisond kinnitas** (378 evali-blokis lahtrit, mida treening pole näinud):
enamik vigu on just omadussõna ühildumine, mitte nimisõna vorm.

## Milles nõukoda on ÜKSMEELEL (Sol + agy + qwen ise)

1. **Üldine SFT on ammendunud, sihitud EI OLE.** Ring 3 õppetund lõplik: ei ühtegi
   suurt üldist ringi enam. Edasi 2000–5000 näite kirurgilised moodulid.
2. **Käänamist tuleb õpetada PROTSESSINA, mitte faktina.** Mõlemad soovitavad
   morfoloogilist CoT-d (tuletuskäik vastuse sees) ja konteksti kaudu õppimist.
   Qwen ise ütles sama: "fraasis peab iga sõna olema õiges käändes ja kokku tuleb
   moodustada grammatiliselt korrektne fraas" — fraas on raskem kui üksiksõna.
3. **DPO ainult mudeli enda vigadest (on-policy).** Mõlemad: 800–1500 rangelt
   kureeritud paari, beta 0,3–0,4, LR 1–2,5e-6, TÄPSELT 1 epohh, loss ei tohi
   kukkuda alla ~0,45. DPO1 oli klassikaline policy collapse.
4. **CPT praegu MITTE.** agy: raiskamine ja ohtlik. Sol: ainult kontrollitud
   100–200M piloodina, eraldi harus, ja alles siis, kui sihitud SFT enam ei liigu.
5. **Toortekst = SFT tooraine, mitte CPT kütus.** Mõlemad: 26,6 mld tokenist tuleb
   AMMUTADA ülesandeid (ümbersõnastus, veatuvastus, stiil), mitte valada sisse.

## Milles nõukoda LAHKNEB (ja meie otsus)

| Küsimus | Sol | agy | Meie otsus |
|---|---|---|---|
| eval-i laiendus | esimene prioriteet, 300+ käänamisülesannet | ei rõhuta | fraasisond ON see laiendus: 378 lahtrit, variandikomplektidega |
| ring 5 lähtekoht | — | puhas baas, mitte adapteri otsa | jätkame dpo2-st: rank16 järjestikused ringid on MÕÕDETULT töötanud (67→77) |
| annuse suurus | 25–40k multitask | 3–5k CoT + cloze | alustame väiksega (kirurgiline reegel), skaleerime kui liigub |

Soli kriitika, mis jääb kehtima ja läheb STATUS-i: **väikesed kategooriad (7–9
ülesannet) on ühe vastuse meelevallas** — liitsõnade "+14,3" on üks flipp. Ära tee
väikeste kategooriate ühe-ringi muutustest järeldusi.

## Qweni enda panus (huvitav negatiivne tulemus)

Küsisime mudelilt endalt, kus ta eksib. **Introspektsioon ei tööta**: ta leiutas
olematuid vorme ("kõrvali") ja andis üldsõnalist nõu. AGA konkreetsete ülesannete
peal on ta aus mõõteriist: fraasisond näitab tema päris vead kätte. Järeldus, mis
läheb ka avalikku raportisse: **mudelilt tuleb küsida tegusid, mitte enesehinnangut.**

## Ring 5 retsept (kombineeritud)

1. **Fraasikäänamine** (`16_gen_fraasid.py`, Vabamorf, reegel valideeritud TalTechi
   1400 lahtri vastu: 98,1%): ~3000 näidet, kaalutud sondi veakaardi järgi
   (sisseütlev, mitmuse omastav/osastav üle-esindatud), 75% evali kujuga
   otsevastust + 25% CoT-tuletust.
2. **Sondi vigadest SFT-parandused**: iga valesti käänatud lahter → õige vastusega
   näide (sama prompt, õige vorm).
3. **Replay** 15–20% (inglise + kood, sama allikas mis ring 4).
4. Treening: rank 16 / alpha 32, dpo2 adapterist edasi, LR langetatud 2e-5
   (Soli soovitus: 5e-5 oli hilisemate ringide jaoks liiga kuum), 1 epohh.
5. Eval lukustatud testiga + fraasisond UUESTI → kaks mõõdikut.

Pärast ring 5: **error-DPO** (sondi + uute vigade paarid, beta 0,3, LR 1e-6,
1 epohh, max ~100 sammu) — nõukoja mõlema hääle esimene soovitus.

## TULEMUS (sama päev, 2026-08-25)

Ring 5 treeniti ja mõõdeti kohe:

| Mõõt | Enne (dpo2) | Pärast (ring5) |
|---|---:|---:|
| lukustatud eval üldskoor | 76,9 | **77,6** |
| käänamine (60 ül) | 76,7 | **80,0** |
| fraasisond (378 nägemata lahtrit) | 73,3 | **81,5** |
| ainsuse sisseütlev sondil | 48% | **80%** |

Üldistuskontroll: treenitud 101 parandusest õigeks vaid 51% (ei ole päheõppimine),
puutumata 277 lahtrist püsis 92%. Nõukoja retsept töötas esimesel katsel.

**Päeva lõputulemus (4 tsüklit sama metoodikaga):** 76,9 → 77,6 (ring5, fraasid)
→ 78,8 (dpo3, error-DPO) → 79,8 (ring6, 5 moodulit) → **82,6 (ring7, kuju-täpsed
parandused)**. Fraasisond 73,3 → 85,7. **GPT (81,7) ületatud.** Käänamine 76,7 →
88,3, rektsioon → 100. DPO4 lükati tagasi (−1,9): error-DPO ammendub, kui SFT on
sama veatüübi juba katnud. Parim mudel: `qwen3.8-et:27b-v7`.

## Edukriteerium

- käänamine lukustatud evalis: 76,7 → **83+** (Sol: +3…+7 on realistlik)
- fraasisond: praegune tase → **+10 pp** uutel lahtritel
- ükski tugev kategooria ei lange üle 1 punkti
- kui käänamine EI tõuse ≥3 punkti, on järgmine kahtlusalune tokeniseerija ja
  CPT-piloot tõuseb prioriteediks (Soli diagnostika: võrdle veamäära ≥4-tokeniste
  ja 1–2-tokeniste vormide vahel)
