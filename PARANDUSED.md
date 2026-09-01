# Parandused / Corrections

**2026-09-01.** Materjali ristkontrollimisel kolme sõltumatu mudeliga leiti
projektist kolm viga, mis olid varasemates raportites ja README-s. Need on
parandatud. Vead ise on kirjas siin, sest need on kasulikumad kui parandatud arv.

**2026-09-01.** A cross-model review of this project's write-up surfaced three
errors that had been sitting in the reports and README. They are fixed. The
errors themselves are documented here, because they are more useful than the
corrected numbers.

---

## 1. Umbes viiendik jätku-eeltreeningu korpusest ei jõudnud mudelini

**Oli:** 131M tokenit jätku-eeltreeningut.
**On:** **110,2M tokenit** jõudis mudelini (3364 sammu × 16 kuhjamist × 2048
tokenit). Korpus ise oli ~141M tokenit.

**Põhjus.** `scripts/46_paki_korpus.py` pakib korpuse ~8000 tähemärgi kaupa,
eeldades 4 tähemärki tokeni kohta. Eesti keeles on see suhe **2,75**. Iga
pakitud tükk oli seetõttu ~2912 tokenit pikk, treeningaken aga 2048. **Iga tükk
kärbiti ja ~22% korpusest ei jõudnud mudelini.** Ükski logi ei kurtnud.

**Kuidas seda oleks pidanud märkama.** `sammud × grad_accum × ctx` ei klappinud
sellega, mida arvasime söötvat. Ajaarvestus näitas sama: 131M / 870 tok/s = 41,8 h,
mõõdetud aeg oli 35,3 h. 110,2M / 870 = 35,2 h.

*The packing script assumed 4 chars/token; Estonian is 2.75. Every packed chunk
exceeded the 2048 context window and was silently truncated. Check
`steps × grad_accum × context` against your expected token count.*

## 2. Korduse (replay) osakaal oli kolm korda väiksem kui raporteeritud

**Oli:** ~10% tokenitest.
**On:** **3,1% sõnadest** (`42_build_cpt_korpus.py` logist).
SFT-ringides kasutatud 15–18% on eraldi asi ja kehtib näidete, mitte tokenite kohta.

Ühtlasi: väidet "kordus hoidis üldteadmised alles ja tõstis koodioskust" **ei saa
teha**, sest kontrolljooksu ilma korduseta ei tehtud.

## 3. Skoori nimetaja on 151, mitte 153

200 ülesannet − 47 rubriikhinnangut = 153, aga skooritud on **151**. Kaks
`regressioon-kood` ülesannet on märgitud automaatselt kontrollitavaks, kuid
`scripts/08_score.py:115` jätab need teadlikult vahele, sest töötava koodi
õigsust ei saa stringivõrdlusega hinnata.

86,08% = 129,98 punkti / 151 ülesannet.

---

## Ja üks metodoloogiline parandus, mis on tähtsam kui kõik kolm

**200-ülesandeline `eval/et_locked_v1.jsonl` ei ole test. See on
arenduskomplekt.** Pärast igat 13-st ringist vaadati selle tulemust, valiti
nõrgim kategooria ja koostati selle järgi järgmine treeninguannus. Ülesanded
ise treeningusse ei sattunud (leke on kirje tasandil blokeeritud), aga **komplekt
juhtis treeningu sisu**, ja see teeb temast definitsiooni järgi
valideerimiskomplekti.

Seetõttu tuleb tulemust esitleda nii:

> 86,1% arenduskomplektil (151 ülesannet), iteratiivselt optimeeritud 13 ringi,
> sõltumatu pimetest tegemata.

Kõige kaitstavam number selles projektis on **perpleksus 22,2 → 15,4**, sest
selle vastu ei häälestatud ühtegi ringi. Ka see ei ole täiesti sõltumatu:
korpuse, žanri ja kõrvalepaneku meetodi valisime meie, ja eraldus käis lõigu,
mitte teose või autori tasandil.

*The 200-task "locked test" was consulted after every round and used to choose
the next training batch. That makes it a development set, not a held-out test.
The 61.7 → 86.1 figure is a development metric and is optimistically biased by
an unknown amount. An independent blind evaluation has not been done.*

---

## Litsentsid: mida me tegime ja mida me ei väida

**Avaldamisest väljas ei ole sama mis treeningust väljas.** Määramata litsentsiga
kirjed (2425 tükki) ja masinaga genereeritud materjal on avaldatavast paketist
välja jäetud ja andmestikus eraldi märgistatud, **aga osa neist oli treeningus
sees**.

**See oli teadlik otsus, mitte tähelepanematus.** Treenisime ilma kindla
litsentsikinnituseta ja tõmbasime piiri **avaldamise**, mitte treeningu juurde,
sest levitamine on koht, kus kahju muutub pöördumatuks. Me ei väida, et see on
õige vastus, ja meil ei ole selle kohta õigusnõu. Euroopa tekstikaeve erandid,
andmebaasiõigus ja küsimus, kas mudelikaal on tuletatud teos, on kõik lahtised.

*We trained deliberately without confirmed licences for part of the corpus, and
drew the line at **publication** rather than at training. Records with unclear
rights are flagged in the dataset and excluded from the published package, but
some of them were in the training mix. This is a stated position, not legal
advice, and we are not claiming it is the correct one.*

---

Nende vigade pikem käsitlus koos sellega, kuidas neid vältida, on failis
`reports/Keelemudelite-treenimine-oppematerjal.pdf` (peatükid 2.2, 4.5, 4.8,
6.2 ja 6.7).
