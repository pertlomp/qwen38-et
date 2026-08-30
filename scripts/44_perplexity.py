#!/usr/bin/env python3
"""Heldout-perplexity žanrite kaupa — CPT ainus aus vahemõõt.

Sol: "kui 100M juures ei parane eestikeelse valideerimiskorpuse perplexity
vähemalt 5-10%, pole mõtet skaleerida." Mõõdame baasi ja CPT-adapteri sama
heldout-komplekti peal (2000 lõiku, EI ole treeningus).
"""
import argparse, json, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", default=None, help="tühi = puhas baas")
    ap.add_argument("--base", default="/mnt/varu/qwen38-et-data/models/Qwen3.8-27B")
    ap.add_argument("--heldout",
                    default="/mnt/varu/qwen38-et-data/processed/cpt_heldout.jsonl")
    ap.add_argument("--n", type=int, default=600)
    ap.add_argument("--valjund", required=True)
    a = ap.parse_args()

    import torch
    from unsloth import FastLanguageModel

    model, tok = FastLanguageModel.from_pretrained(
        model_name=a.base, max_seq_length=2048, dtype=None,
        load_in_4bit=True, full_finetuning=False)
    if a.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, a.adapter)
        print(f"adapter: {a.adapter}", flush=True)
    FastLanguageModel.for_inference(model)
    model.eval()

    read = [json.loads(r) for r in open(a.heldout)][:a.n]
    print(f"heldout: {len(read)} lõiku", flush=True)
    kokku = {}
    with torch.no_grad():
        for i, d in enumerate(read, 1):
            enc = tok(text=d["text"], return_tensors="pt",
                      truncation=True, max_length=1024).to("cuda")
            if enc["input_ids"].shape[1] < 10:
                continue
            out = model(**enc, labels=enc["input_ids"])
            z = d["zanr"]
            s = kokku.setdefault(z, [0.0, 0])
            s[0] += out.loss.item() * enc["input_ids"].shape[1]
            s[1] += enc["input_ids"].shape[1]
            if i % 100 == 0:
                print(f"  {i}/{len(read)}", flush=True)

    tulem = {z: math.exp(s[0] / s[1]) for z, s in kokku.items()}
    koigi = math.exp(sum(s[0] for s in kokku.values())
                     / sum(s[1] for s in kokku.values()))
    tulem["KOKKU"] = koigi
    print("PERPLEXITY:", {k: round(v, 3) for k, v in tulem.items()})
    json.dump({"adapter": a.adapter or "baas", "perplexity": tulem},
              open(a.valjund, "w"))

if __name__ == "__main__":
    main()
