# Andmeregister — mis on kust, mis litsentsiga, kus kasutatud

**Uuendatud:** 2026-08-23 · **Toorandmeid kettal:** 89.5 GB

Genereeritud: `scripts/10_andmeregister.py`. Mahud mõõdetakse kettalt,
päritolu ja litsentsid on käsitsi hooldatavad (skripti sees).

## Allikad

| Allikas | Kategooria | Maht | Litsents | Kasutus | Avaldatav |
|---|---|---:|---|---|---|
| Riigi Teataja XML | õigustekst | 45.5 GB | avalik omand (AutÕS §5, õigusaktid ei ole kaitstud) | CPT-reserv; SFT-paarid plaanis | JAH, piiranguteta |
| FineWeb-2 (ekk_Latn) | veebitekst | 19.7 GB | ODC-By 1.0 | CPT-reserv (faas 4) | jah, allikaviitega |
| HPLT v2 (est_Latn) | veebitekst | 13.1 GB | CC0 / vaba (HPLT väljalase) | CPT-reserv (faas 4) | jah, allikaviitega |
| TalTech EASC + EFAC | KÕNE (heli+tekst) | 4.9 GB | MÄÄRAMATA ('other') | RESERV: kõnemudel | KÜSI ENNE |
| Riigikogu heli + joondatud stenogrammid | KÕNE (heli+tekst) | 4.4 GB | CC-BY-SA-3.0 (share-alike) | RESERV: Whisperi kohandamine / kõnemudel; EI kasutata tekstitreeningus | ainult CC-BY-SA all |
| VoxPopuli (eesti osa) | KÕNE (heli+tekst) | 491 MB | CC0-1.0 / other (kontrolli alamosa) | RESERV: kõnemudel (Euroopa Parlamendi eesti kõne) | CC0 osa jah |
| TalTech err-video-news-transcribed | kõne + toimetatud tekst | 424 MB | CC-BY-SA 4.0 (SHARE-ALIKE, nakkav) | ring 1-2 SFT (kõne→tekst paarid); käänamiskorpus | ainult CC-BY-SA all |
| Eesti Vikipeedia | entsüklopeedia | 305 MB | CC-BY-SA 4.0 (share-alike) | CPT-reserv | jah, CC-BY-SA all |
| Riigikogu stenogrammid | toimetatud kõne | 274 MB | avalik omand (ametlikud dokumendid) | käänamiskorpus; CPT-reserv | JAH, piiranguteta |
| OPUS OpenSubtitles v2018 (et) | subtiitrid | 263 MB | ebaselge (tuletatud teosed) | EI KASUTATUD ring 1-3 | EI — jääb koduseks |
| TalTech qa_broadcast_conv_et | saatevestlused | 136 MB | kontrollimata | ring 1-3 SFT | KÜSI ENNE |
| TartuNLP alpaca-est | instruktsioonid | 38 MB | GPT-3.5 genereeritud → OpenAI ToS hall ala | ring 1-3 SFT (märgitud 'hall-gpt35') | ainult teadusklausliga (Alpaca-est pretsedent) |
| TalTech word_meanings_et | sõnaseletused | 10 MB | kontrollimata | ring 1-3 SFT | KÜSI ENNE |
| CodeAlpaca-20k | replay (kood, inglise) | 3 MB | GPT genereeritud → hall | ring 1-3 replay | ei ole vajalik |
| TalTech grammar_et + grammar2_et | grammatikaparandus | 2 MB | kontrollimata | ring 1-2 SFT (9302), eval (50) | KÜSI ENNE |
| TalTech inflection_et | käänamine | 0 MB | MÄÄRAMATA (HF-kaardil puudub) | ring 1 SFT (1022), eval (60) | KÜSI ENNE |
| TartuNLP gec-llm | grammatikaparandus | 0 MB | kontrollimata | DPO-reserv | KÜSI ENNE |

## Tuletised (meie loodud)

| Fail | Sisu | Kirjeid | Allikad | Avaldatav |
|---|---|---:|---|---|
| `et-kaanamiskorpus-v1.jsonl` | mudelisõltumatu käänamiskorpus | 13,436 | TalTech inflection_et + Riigikogu/ERR ekstrakt | osaliselt: Riigikogu-osa vabalt, ERR-osa CC-BY-SA, TalTech küsi |
| `sft_v1.jsonl` | kogu SFT-bassein (chat-formaadis) | 60,249 | vt allikate tabel | segu — filtreeri litsentsi järgi |
| `morfo_meta.jsonl` | EKI reeglistiku faktid (käänded, kõneviisid) | 72 | EKI reeglistik, käsitsi koostatud | JAH, oma looming |
| `kaanded_tekstist.jsonl` | EstNLTK-ga ekstraheeritud vormid | 11,027 | Riigikogu + ERR | CC-BY-SA (kuni allikad eraldatud) |

## Litsentsi-reeglid, mida ei tohi unustada

1. **CC-BY-SA on nakkav.** ERR-i ja Vikipeedia materjalist tuletatu peab jääma
   CC-BY-SA alla. Kui tahad piiranguteta avaldatavat paketti, ehita see AINULT
   avaliku omandi allikatest (Riigikogu, Riigi Teataja) ja omaloomingust.
2. **'Kontrollimata' ei tähenda 'lubatud'.** TalTechi andmestikel puudub HF-kaardil
   litsents. Enne avaldamist tuleb küsida.
3. **Hall kiht on märgistatud.** Kõik GPT-genereeritud materjal kannab SFT-failides
   lippu `litsents: hall-gpt35` — filtreeritav ühe reaga.
4. **Subtiitreid ring 1-3 EI kasutanud.** Need jäid alla laaditud, aga kasutamata.

## Uue allika lisamisel

Lisa kirje `ALLIKAD` nimekirja skriptis (nimi, kaust, URL, litsents, saadud,
kasutus, avaldatav) ja jooksuta skript uuesti. Mahud mõõdetakse ise.
**Litsentsi väli ei tohi jääda tühjaks** — kui ei tea, kirjuta 'kontrollimata'
ja avaldatavusse 'KÜSI ENNE'.
