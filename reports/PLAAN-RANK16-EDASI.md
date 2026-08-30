# Plaan: rank 16 edasi — kirurgiline meetod

**Koostatud:** 2026-08-25 · **Lähtekoht:** `dpo2` adapter, 76,9%
**Otsus:** rank 32 kett katkestatud (küllastus tõestatud), edasi ainult rank 16.

## Mõõdetud alus: väike ja täpne võidab suure ja üldise

| Ring | Näiteid | Tokeneid | Tõus | Tõus / M tokenit |
|---|---:|---:|---:|---:|
| ring 1 | 28 615 | 10,5M | +5,6 | 0,53 |
| ring 2 | 36 753 | 14,1M | +5,5 | 0,39 |
| **ring 3** | **81 268** | **15,4M** | **+1,1** | **0,07** |
| ring 4 | 53 386 | 7,8M | +2,8 | 0,36 |

**Ring 3 oli suurim ja kõige ebaefektiivsem.** Ta sisaldas 21 250 saatevestlust ja
20 057 sõnaseletust — üldist materjali, mis ei andnud mõõdetavat võitu, aga täitis
adapteri mahutavust ja surus välja seda, mis oli juba õpitud (grammatika langes
−0,9, sõnaleiutamine −14,2).

**Vastupidine tõend: väikesed sihitud annused andsid suurimad võidud.**

| Annus | Suurus | Efekt |
|---|---:|---|
| metateadmise faktid | 720 näidet | morfoloogia-meta 0,8 → 57,7 (**+56,9**) |
| tööriistanäited | 400 näidet | tööriistad 50 → 100 (**+50,0**) |
| JSON-näited | 400 näidet | JSON 50 → 66,7 (+16,7) |
| stiilipaarid (DPO2) | 244 paari | liitsõnad 57,1 → 71,4 (+14,3) |

Järeldus: **LoRA adapteril on piiratud mahutavus ja iga näide konkureerib ruumi
pärast.** Üldine materjal ei ole neutraalne täidis, vaid aktiivne kahju.

## Uus töörütm: kirurgiline tsükkel

Senine rütm oli 6–10 h ring + eval, tulemus järgmisel päeval. Uus:

```
1. Mõõda   → vaata evalist, mis on nõrgim (skoor + n)
2. Sihi    → 300–800 näidet TÄPSELT sinna, ei midagi muud
3. Treeni  → 1–2 h (mitte 6–10)
4. Hinda   → eval, sama lukustatud test
5. Otsusta → liikus? hoia ja mine edasi. ei liikunud? viska ära
```

Iga tsükkel on **2–3 tundi**, mitte päev. Päevas mahub 3–4 katset, mitte üks.

**Ballasti reegel:** iga uus annus sisaldab AINULT sihitud materjali + 15% replay.
Saatevestlused, sõnaseletused ja üldised instruktsioonid EI LÄHE enam kaasa.
Need on juba õpitud ja kordamine maksab mahutavust.

## Sihtmärkide järjekord (praegusest evalist)

| # | Kategooria | Praegu | Suured | Annus | Allikas |
|---:|---|---:|---:|---|---|
| 1 | **käänamine** | 76,7 | 96,7 | 600 näidet | Vabamorf: AINULT vead, mida mudel praegu teeb |
| 2 | **sõnaleiutamine** | 57,1 | 57,1 | 400 | negatiivsed näited: "kas see sõna on olemas" |
| 3 | **JSON** | 66,7 | 66,7 | 300 | keerukamad skeemid, pesastatud |
| 4 | **tehniline** | 50,0 | 50,0 | 300 | lühendite käänamine, terminid |
| 5 | **rektsioon** | 75,0 | 87,5–100 | 400 | rektsioonipaarid, DPO-na |

**Käänamine on esimene ja tähtsaim**, sest vahe suurte mudelitega on 20 punkti.
Aga uus meetod: mitte "rohkem käänamisnäiteid" (ring 3 tõestas, et see ei tööta),
vaid **veaanalüüs** — lase mudelil evali käänamisülesanded läbi, vaata TÄPSELT
millised vormid ta valesti teeb, ja tee näited ainult nendest tüüpidest.

## Paralleelselt: DPO mudeli enda vigadest (suurim avamata potentsiaal)

Senised stiilipaarid on Soli ja agy **kujutlus** halvast eesti keelest. Meil on nüüd
päris mudel, kes teeb päris vigu.

```
1. Lase dpo2-mudelil vastata 300 uuele küsimusele (Perti kasutusjuhud)
2. Tema väljund = rejected
3. Minimaalselt toimetatud versioon = chosen  (Sol/agy/Claude toimetavad)
4. DPO nendega: lr 3e-6, beta 0.3 (DPO2 seaded, mis tõestasid end)
```

See on ainus DPO-allikas, mis õpetab mudeli **enda** vigu. 15 min treeningut.

## Ja see, mida ainult Pert saab teha

**47 rubriigi-ülesannet on endiselt hindamata.** Need mõõdavad loomulikkust ja
stiili — täpselt seda, "mida inimesed märkavad". Automaatskoor neid ei näe.

Pime A/B: sama küsimus, kaks vastust (meie mudel vs suur mudel), Pert valib parema
teadmata kumb kumb. Iga valik on ühtlasi kõrgeima kvaliteediga DPO-paar.

## Mida EI tee

- ei treeni enam suuri üldisi annuseid (ring 3 õppetund)
- ei lisa saatevestlusi/sõnaseletusi (õpitud, kordamine maksab)
- ei mine rank 32 rajale (küllastus tõestatud: 73,7 → 73,7 → 73,3)
- ei kasuta GEC-paare DPO-s (DPO1 õppetund: −6,0 pp)

## Edukriteerium

Iga tsükkel peab andma **vähemalt +0,5 pp üldskoori** või **+10 pp sihitud
kategoorias**. Kui ei anna, visatakse annus ära ja proovitakse teist nurka.
Praegune lähtekoht: **76,9%**. Realistlik siht järgmiseks: 80%+ (GPT on 81,7).
