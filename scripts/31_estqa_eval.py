#!/usr/bin/env python3
"""EstQA väline valideerimine: eesti SQuAD-stiilis lugemisülesanne (TalTech).

603 test-küsimust: kontekst + küsimus → ekstraktiivne vastus. Skoorime
token-F1 ja EM (nagu SQuAD), vastuse variandid arvestatud, lemma-tasandil
lisaks (eesti käänded: "geodeesiateenistus" vs "geodeesiateenistuses" on
sisult sama vastus). Deterministlik valim, sama igale mudelile.
"""
import argparse, collections, json, random, re, urllib.request
import pandas as pd

TEST = "/mnt/varu/qwen38-et-data/raw/taltech/EstQA/data/test-00000-of-00001.parquet"
SEEME = 20260825

def kysi(mudel, prompt, n=60):
    d = json.dumps({"model": mudel, "think": False, "stream": False,
                    "messages": [{"role": "user", "content": prompt}],
                    "options": {"temperature": 0.0, "num_predict": n}}).encode()
    req = urllib.request.Request("http://localhost:11434/api/chat", data=d,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["message"]["content"].strip()

def normi(t):
    t = t.lower().strip()
    t = re.sub(r"[\"'«»„“”.,:;!?()]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def f1(vastus, oige):
    v, o = normi(vastus).split(), normi(oige).split()
    if not v or not o:
        return 0.0
    yhised = sum((collections.Counter(v) & collections.Counter(o)).values())
    if yhised == 0:
        return 0.0
    p, r = yhised / len(v), yhised / len(o)
    return 2 * p * r / (p + r)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mudel", required=True)
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--valjund", default=None)
    a = ap.parse_args()
    random.seed(SEEME)

    df = pd.read_parquet(TEST)
    idx = list(range(len(df)))
    random.shuffle(idx)
    valim = idx[:a.n]
    print(f"EstQA: {len(df)} küsimust, valim {len(valim)}, mudel {a.mudel}",
          flush=True)

    em = 0
    f1_summa = 0.0
    tehtud = 0
    for j, i in enumerate(valim, 1):
        rida = df.iloc[i]
        prompt = (f"Loe teksti ja vasta küsimusele LÜHIDALT, ainult vastuse "
                  f"fraasiga tekstist, ilma selgituseta.\n\nTekst: "
                  f"{rida['context']}\n\nKüsimus: {rida['question']}")
        try:
            v = kysi(a.mudel, prompt)
        except Exception as e:
            print(f"  VIGA {j}: {e}", flush=True)
            continue
        v = v.split("\n")[0].strip()
        variandid = [x["text"] for x in rida["answers"]]
        parim = max(f1(v, o) for o in variandid)
        f1_summa += parim
        em += any(normi(v) == normi(o) for o in variandid)
        tehtud += 1
        if j % 50 == 0:
            print(f"  {j}/{len(valim)}  F1 {f1_summa/tehtud*100:.1f}  "
                  f"EM {em/tehtud*100:.1f}", flush=True)

    print(f"\nEstQA ({a.mudel}): F1 {f1_summa/tehtud*100:.1f}  "
          f"EM {em/tehtud*100:.1f}  (n={tehtud})")
    if a.valjund:
        json.dump({"mudel": a.mudel, "n": tehtud, "f1": f1_summa / tehtud,
                   "em": em / tehtud}, open(a.valjund, "w"), ensure_ascii=False)
        print(f"→ {a.valjund}")

if __name__ == "__main__":
    main()
