# Eesti käänamiskorpus v1 — mudelisõltumatu vara

**Fail:** `/mnt/varu/qwen38-et-data/processed/et-kaanamiskorpus-v1.jsonl`
**Manifest:** sama kaust, `…-manifest.json`
**SHA-256:** `6caee07d7a095b755ff323e5ff18a54522987f3432deec22a1871ba5d19591cb`
**Koostatud:** 2026-08-23 · **Kirjeid:** 13 436

## Miks see fail on projekti kõige väärtuslikum osa

Adapter vananeb koos mudeliga — Qwen4 tulekul on `qwen38-27b-et-lora-v1` kasutu.
**See korpus ei vanane.** Iga tulevane mudel (Qwen4, Llama, Gemma, mis iganes)
saab sellest sama treeningmaterjali. Seetõttu EI ole see chat-formaadis: puhas
andmestruktuur, millest genereeritakse näiteid iga mudeli oma vestlusmalli jaoks.

## Sisu

| Allikas | Kirjeid | Tüüp | Mida annab |
|---|---:|---|---|
| TalTech `inflection_et` | 2 425 | fraas | omadussõna + nimisõna **ühildumine** ("kollane päevalill" → "kollase päevalille") |
| Riigikogu + ERR tekstist | 11 011 | sõna | päris kasutuses olevad vormid, 11 010 unikaalset lemmat |

Iga kirje: `sisend` + `kaane` + `arv` → `vorm`, lisaks `sonaliik`, `sagedus`,
`allikas`, `litsents`, `eval_blokis`.

**638 kirjet on märgitud `eval_blokis: true`** — need esinevad lukustatud testis
ja neid EI TOHI treeningusse panna. Filter on korpuses sees, mitte eraldi failis,
et see ei ununeks.

## Litsentsid — kirje kaupa, sest need erinevad

| Osa | Litsents | Tähendus |
|---|---|---|
| tekstist ekstraheeritud (11 011) | **CC-BY-SA 4.0** (konservatiivne) | share-alike **nakkab** kogu tuletisele |
| TalTech `inflection_et` (2 425) | **MÄÄRAMATA** | HF-kaardil litsentsi ei ole |

Kaks tegemata tööd enne avaldamist:

1. **Riigikogu ja ERR tuleb eraldada.** Praegune ekstrakt segas need kokku, seega
   on kõik märgitud ERR-i (rangema) litsentsiga. Riigikogu stenogrammid on avalik
   omand (AutÕS §5) ja moodustavad tõenäoliselt enamiku — nende eraldamiseks tuleb
   `03b_kaanded_tekstist.py` uuesti joosta allikalipuga. Siis tekib puhas,
   piiranguteta avaldatav tuum.
2. **TalTechi osa litsents tuleb küsida** või avaldamisel välja jätta.

## Katvus ja lüngad

Ekstraheerimine paljastas, millised käänded on päris kõnes haruldased. Lagi 700
tähendab, et materjali oli rohkem kui kvoot lubas; väiksemad arvud on tegelik nappus.

| Kääne | Ainsus | Mitmus | Seis |
|---|---:|---:|---|
| omastav, osastav, saav, seesütlev, seestütlev, alaleütlev, alalütlev, kaasaütlev | 700 | 374–700 | küllalt |
| sisseütlev | 234 | 112 | napp |
| olev | 243 | 20 | napp |
| alaltütlev | 206 | 61 | napp |
| **rajav** | **99** | **21** | puudulik |
| **ilmaütlev** | **38** | **11** | puudulik |

Rajav ("raamatuni") ja ilmaütlev ("raamatuta") on päris kõnes lihtsalt haruldased.
Neid tekstist rohkem ei saa — siin on põhjendatud minna reeglipõhise genereerimise
teed (Vabamorf, `03_gen_morfoloogia.py` on valmis ja ring-kontrolliga), kontrollides
tulemust teise, sõltumatu rajaga.

## Kuidas kasutada uue mudeli treenimisel

```python
# Korpus on mudelist ja mallist sõltumatu — näide genereeritakse laadimisel
for k in korpus:
    if k["eval_blokis"]: continue        # lukustatud testi kirjed välja
    kysimus = f"Pane {'fraas' if k['tyyp']=='fraas' else 'sõna'} " \
              f"'{k['sisend']}' {k['arv']} {k['kaane']} käändesse."
    # → vorm on k["vorm"]; pane oma mudeli chat-malli
```

## Kasvatamine

`03b_kaanded_tekstist.py` luges 60 000 lauset. Kettal on **26,6 mld tokenit**
toorteksti (HPLT, FineWeb-2, Riigi Teataja, kogu stenogrammiarhiiv), millest on
kasutatud tühine osa. Sagedus- ja kvoodipiiri (`SIHT_KAANDE_KOHTA = 700`,
`MIN_SAGEDUS = 3`) tõstes ning rohkem lauseid lugedes saab korpust mitmekordistada
ilma ühegi uue allalaadimiseta.
