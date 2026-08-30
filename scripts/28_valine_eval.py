#!/usr/bin/env python3
"""Väline valideerimine: TalTechi MMLU_et (masintõlgitud MMLU, valikvastused).

Miks: meie lukustatud eval on ise tehtud — suhteline võrdlus on aus, aga
absoluutnumbrid ei ole standardiga võrreldavad, ja treening on ehitatud evali
veatüüpide järgi. MMLU_et on SÕLTUMATU test, mida me pole kunagi vaadanud:
see mõõdab, kas eesti keele treening rikkus üldist arusaamist (ei tohiks) ja
kas eestikeelsest küsimusest arusaamine paranes.

Deterministlik valim: seeme 20260825, 300 küsimust test-osast, ühtlaselt üle
kategooriate. Sama valim igale mudelile.
"""
import argparse, collections, glob, json, random, re, urllib.request

MMLU = "/mnt/varu/qwen38-et-data/raw/taltech/MMLU_et"
SEEME = 20260825

def kysi(mudel, prompt, n=8):
    d = json.dumps({"model": mudel, "think": False, "stream": False,
                    "messages": [{"role": "user", "content": prompt}],
                    "options": {"temperature": 0.0, "num_predict": n}}).encode()
    req = urllib.request.Request("http://localhost:11434/api/chat", data=d,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["message"]["content"].strip()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mudel", required=True)
    p.add_argument("--n", type=int, default=300)
    p.add_argument("--valjund", default=None)
    a = p.parse_args()
    random.seed(SEEME)

    # deterministlik valim üle kõigi test-failide
    koik = []
    for f in sorted(glob.glob(f"{MMLU}/test_*.jsonl")):
        for rida in open(f):
            try:
                d = json.loads(rida)
            except Exception:
                continue
            if d.get("question") and len(d.get("choices", [])) == 4:
                koik.append(d)
    random.shuffle(koik)
    valim = koik[:a.n]
    print(f"MMLU_et: {len(koik)} küsimust, valim {len(valim)}, mudel {a.mudel}",
          flush=True)

    oiged, tulem = 0, []
    kat = collections.defaultdict(lambda: [0, 0])
    for i, d in enumerate(valim, 1):
        tahed = ["A", "B", "C", "D"]
        valikud = "\n".join(f"{t}) {v}" for t, v in zip(tahed, d["choices"]))
        prompt = (f"{d['question']}\n\n{valikud}\n\n"
                  f"Vasta ainult ühe tähega (A, B, C või D).")
        try:
            v = kysi(a.mudel, prompt)
        except Exception as e:
            print(f"  VIGA {i}: {e}", flush=True)
            continue
        m = re.search(r"[ABCD]", v.upper())
        vastus = m.group(0) if m else "?"
        oige = tahed[d["answer"]]
        korras = vastus == oige
        oiged += korras
        kat[d.get("category", "?")][0] += korras
        kat[d.get("category", "?")][1] += 1
        tulem.append({"kategooria": d.get("category"), "vastus": vastus,
                      "oige": oige, "korras": korras})
        if i % 50 == 0:
            print(f"  {i}/{len(valim)}  täpsus {oiged/i*100:.1f}%", flush=True)

    print(f"\nMMLU_et TÄPSUS ({a.mudel}): {oiged}/{len(tulem)} "
          f"= {oiged/len(tulem)*100:.1f}%")
    if a.valjund:
        with open(a.valjund, "w") as f:
            json.dump({"mudel": a.mudel, "n": len(tulem),
                       "tapsus": oiged / len(tulem),
                       "kategooriad": {k: {"oigeid": v[0], "n": v[1]}
                                       for k, v in kat.items()}}, f,
                      ensure_ascii=False, indent=1)
        print(f"→ {a.valjund}")

if __name__ == "__main__":
    main()
