# CPT-piloot: toorteksti eeltreening eesti keele jaoks (avalik metoodika)

> ⚠️ **Parandused 2026-09-01.** CPT tokenite arv on 110,2M (mudelini jõudnud),
> mitte 131M; kordus oli 3,1% sõnadest, mitte ~10%. Väidet, et kordus säilitas
> koodioskuse, ei saa teha, sest kontrolljooksu ilma korduseta ei tehtud.
> Vt [PARANDUSED.md](../PARANDUSED.md).


**Alustatud:** 2026-08-28 · **Riistvara:** 1× RTX 5090 (32 GB), võimsuspiir 450 W
**Eesmärk:** mõõta, kas 150M tokeni kvaliteetproosa eeltreening (CPT) annab
loomulikkuse ja keeletaju, mida sihitud SFT ei anna. Nõukoda 2 retsept
(`NOUKODA-2-SYNTEES.md`), Soli parameetrid.

> See dokument on kirjutatud jagamiseks: iga samm, parameeter ja tulemus on
> kirjas nii, et sama saab korrata mis tahes mudeli ja keelega.

## Küsimus, millele piloot vastab

Meie 13 SFT-ringi viisid Qwen3.8-27B eesti oskused 61,7 → 85,3 protsendini,
aga vaba registri kvaliteet (ilukirjanduslik stiil, sõnavara sügavus) jäi
SFT-le kättesaamatuks: mudel kirjutab "koerapupp" (pro kutsikas), "sai
kutsung" (pro kutse). Hüpotees: need vead istuvad KEELES ENDAS, mitte
vastamiskäitumises — ja keelt saab juurde valada ainult toortekstiga.

## Disain: kontrollitud võrdlus (Soli nõue)

```
haru A (olemas): baas → 13 sihitud SFT-ringi          = 85,3% (ring12)
haru B (see):    baas → CPT 150M tok → SFT-kombo      = ?
```

SFT-kombo = ringide 5-13 sihitud materjali koond (~15k näidet, dedup,
teadaolevad disainivead välja jäetud) — nii saab haru B sama õpetuse ühe
treeninguga ja võrdlus on aus.

## Andmed (viitamiskohustusega!)

Allikas: **Eesti keele koondkorpus, Tartu Ülikooli arvutilingvistika
uurimisrühm, CC-BY-SA** (litsentsi kinnitas Kadri Muischnek, 2026-08-26).

| Osa | Maht | Märkus |
|---|---|---|
| ilukirjandus (1990+) | 4,6M sõna × 2 | 2× ülekaal — mõõdetud auk |
| teadus (doktoritööd, Eesti Arst, Agraarteadus, Arvutitehnika) | 3,3M sõna | |
| populaarteadus (Horisont) | 0,2M sõna | |
| ajakirjandus (Postimees, EPL, Ekspress, Maaleht, Läänelu, Luup) | 45M sõna (piiratud) | toimetatud, aga ei tohi domineerida |
| replay: inglise + kood | 3,1% sõnadest (mõõdetud) | katastroofilise unustamise vastu |

Riigi Teataja jäi teadlikult välja (kantseleikeele riski hoiatus).
Heldout: 2000 lõiku žanrite kaupa, EI treenita — perplexity-mõõduks.
Filtrid: MD5-dedup, `<nooutput>`-saaste, mitte-tähestikuline müra.

## Treeningparameetrid (CPT)

- QLoRA (bnb NF4) baasmudelist Qwen3.8-27B, **mitte** SFT-adapterist
- rank 32 / alpha 64, sihtmoodulid q,k,v,o,gate,up,down
- **packing=True**, ctx 2048 — pakitud järjestused on CPT võti
- LR 8e-6, cosine, warmup 2%, 1 epohh, paged_adamw_8bit, bf16, seeme 20260828
- checkpoint iga 500 sammu

## Mõõdikud (enne/pärast, sama seeme, sama valim)

1. **Heldout-perplexity žanrite kaupa** (baas vs CPT) — Soli kriteerium:
   kui KOKKU ei parane ≥5%, CPT skaleerimine ei tasu
2. **Lukustatud eval 200 ül** (CPT+SFT vs ring12 85,3)
3. **Fraasisond 378 lahtrit** (vs ring12 85,7)
4. Käsitsi registrikontroll (Perti pime võrdlus)

## Skriptid (avalikud)

`42_build_cpt_korpus.py` (korpus+heldout) · `43_train_cpt.py` (pakitud CPT) ·
`44_perplexity.py` (žanri-perplexity) · `45_build_sft_kombo.py` (SFT-koond) ·
`oo_cpt.sh` (täisahel). Kogu ülejäänud metoodika: skriptid 01-41 + STATUS.md.

## TULEMUSED

**Baasi heldout-perplexity (ilukirjandus, 600 lõiku): 22,2** — mõõdetud
2026-08-28 10:00. Kaks metoodilist märkust ausalt kirja:
- perplexity-valim on heldout'i järjekorra tõttu ilukirjanduse osa (600 lõiku)
  — enne/pärast võrdlus on sama valimiga, seega aus; žanrijaotus jäi saamata
- replay tuli 3,1% (plaanitud 10%) — masinas pole suurt EN-korpust; inglise/
  koodi tase mõõdetakse pärast eraldi üle (MMLU valim + HumanEval)

| Mõõt | baas | CPT | CPT+kombo | **FINAL (CPT+3 ringi+DPO)** | ring12 (13 ringi) |
|---|---:|---:|---:|---:|---:|
| perplexity ilukirjandus | 22,2 | **15,4 (−31%)** | — | (CPT-kiht sees) | — |
| lukustatud eval | 61,7 | — | 76,5 | **81,9** | 85,3 |
| fraasisond (378) | — | — | 51,6 | **77,2** | 85,7 |
| MMLU_et (300) | 68,7 | — | — | **67,3** | 68,7 |
| EstQA F1 (200) | 86,9 | — | — | **73,6** | 76,1 |
| HumanEval | 71,3 (think, n=164) | — | — | **83,3 (no-think, n=60¹)** | 65,9 (no-think, n=164) |
| proosa (käsitsi) | — | LUGU | — | LUGU | valem |

¹ n=60 valim (HumanEvali algus) ei ole otse võrreldav n=164-ga.

**CPT-haru taastumiskõver:** kombo e1 76,5 → e2 79,5 → ring1 80,6 (käänamine
81,7→90) → ring2 80,6 (sond 53,7→68,5) → ring3+DPO **81,9** (sond 77,2).
Iteratiivne retsept töötas ka CPT peal, iga ring +1-1,5pp või sondihüpe.

**CPT-treening:** 3364 sammu, 35,3 h, 450 W, loss stabiilne; läbilaskevõime
mõõdetult ~870 tok/s (27B QLoRA, üks RTX 5090).

**Põhivastus: CPT TÖÖTAS.** Perplexity −31% (lävi oli 5–10%) ja proosavõrdlus
kinnitas kvalitatiivselt: baas+ringid kirjutab valemit ("unistused täituvad,
kui usud endasse"), CPT-haru kirjutab LUGU (külatüdruk, katkine teleskoop
keldrikapist, parandamine, tähistaevas) — narratiiv, lõigud, konkreetsed pildid.

**Teine leid: oskused ei kandu ühe koondannusega.** 14,7k näidete kombo üks
epohh andis 76,5/51,6 — kaugel 13 iteratiivse ringi 85,3/85,7-st. Iteratiivne
veapõhine protsess on osa õppimisest, mitte ainult andmehulk. Taastamine käib
(kombo e2 + vajadusel kirurgilised ringid CPT-vundamendil).

## Õppetunnid teistele treenijatele

1. **TRL packing=True võib multimodaalse protsessoriga vaikselt MITTE
   rakenduda.** Kontrolli: kui sammude arv = näited/grad_accum, siis pakkimist
   EI toimu (meil 78 045 sammu = 6,5 päeva). Paki faili tasandil ise
   (~8000 tähemärki/tükk) — deterministlik ja treener-sõltumatu.
2. **Päris läbilaskevõime 27B QLoRA-l (1× RTX 5090, 450 W): ~870 tok/s.**
   Sellega arvuta: 110,2M tokenit = ~35 h. "Sammu aeg jääb samaks" on illusioon,
   mis tekib lühikeste polsterdamata näidete pealt.
3. **CPT ja SFT teevad ERI tööd:** CPT annab keele (ppl −31%, narratiiv),
   SFT annab oskused — ja oskuste ehitamine on iteratiivne protsess, mida
   üks koondannus ei asenda. Planeeri CPT + mitu sihitud ringi, mitte CPT +
   üks suur SFT.
4. **Perplexity heldout kihita enne mõõtmist** (meil jäi žanrijaotus saamata,
   sest valim tuli järjekorrast). Enne/pärast on sama valimiga siiski aus.
5. Eesti kontekstis: 2× ilukirjanduse ülekaal 110M-tokenises miksis andis
   proosahüppe ilma inglise/koodi nähtava kahjuta (kontroll käimas).
