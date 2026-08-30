#!/usr/bin/env python3
"""Teeb fraasisondi tulemustest treeningmaterjali: on-policy DPO + SFT-parandused.

Nõukoja 2 üksmeelne soovitus: DPO paarid peavad tulema mudeli ENDA vigadest.
Sond annab need otse: rejected = mudeli päris vale vastus, chosen = õige vorm.

Väljund:
  processed/dpo_fraasivead.jsonl  - DPO paarid (ainult lahtrid, kus mudel eksis)
  processed/sft_fraasiparandused.jsonl - SFT näited samadest lahtritest
"""
import argparse, json
from collections import Counter

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sond", default="/mnt/varu/qwen38-et-data/processed/fraasisond.jsonl")
    p.add_argument("--dpo", default="/mnt/varu/qwen38-et-data/processed/dpo_fraasivead.jsonl")
    p.add_argument("--sft", default="/mnt/varu/qwen38-et-data/processed/sft_fraasiparandused.jsonl")
    a = p.parse_args()

    read = [json.loads(r) for r in open(a.sond)]
    vead = [t for t in read if not t["korras"] and t["vastus"]]
    print(f"sond: {len(read)} lahtrit, {len(vead)} viga")

    n_dpo = n_sft = 0
    with open(a.dpo, "w") as fd, open(a.sft, "w") as fs:
        for t in vead:
            # standardvorm: pikim variant on tänapäevane de/te-mitmus
            oige = max(t["oiged"], key=len)
            # DPO: sama prompt, mudeli enda viga vs õige vorm
            fd.write(json.dumps({
                "prompt": t["prompt"], "chosen": oige, "rejected": t["vastus"],
                "allikas": "fraasisond-onpolicy", "kaane": t["kaane"],
                "arv": t["arv"]}, ensure_ascii=False) + "\n")
            n_dpo += 1
            # SFT: sama prompt, õige vastus
            fs.write(json.dumps({"messages": [
                {"role": "user", "content": t["prompt"]},
                {"role": "assistant", "content": oige}],
                "allikas": "fraasisond-parandus",
                "litsents": "taltech-inflection (MÄÄRAMATA)"},
                ensure_ascii=False) + "\n")
            n_sft += 1

    jaotus = Counter((t["arv"], t["kaane"]) for t in vead)
    print(f"DPO paare: {n_dpo} → {a.dpo}\nSFT parandusi: {n_sft} → {a.sft}")
    print("\nvigade jaotus (generaatori kaalude sisend):")
    for (arv, kaane), n in jaotus.most_common():
        print(f"  {arv} {kaane:<14}{n:>5}")

if __name__ == "__main__":
    main()
