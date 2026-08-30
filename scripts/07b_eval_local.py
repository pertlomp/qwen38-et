#!/usr/bin/env python3
"""Jooksutab lukustatud evali otse Unslothi/transformersi kaudu.

Miks eraldi 07_eval.py-st: baasjoon mõõdeti Ollamas (Q4_K_M), treenitud adapter
elab bnb NF4 peal. Eri kvantimine → ebaaus võrdlus. Seetõttu mõõdame ENNE ja
PÄRAST sama torustikuga: sama laadija, sama kvantimine, samad inferentsiseaded.

Kasutus:
  python 07b_eval_local.py --run baseline-bnb                    # baas ilma adapterita
  python 07b_eval_local.py --run ring1-bnb --adapter .../ring1/final
"""
import argparse, json, os, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--base", default="/mnt/varu/qwen38-et-data/models/Qwen3.8-27B")
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--eval", default="/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/"
                                      "qwen38-et/eval/et_locked_v1.jsonl")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-new", type=int, default=400)
    ap.add_argument("--thinking", action="store_true",
                    help="jäta mõtlemisplokk avatuks (vaikimisi väljas, nagu Ollama evalis)")
    a = ap.parse_args()

    EVAL_DIR = "/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/eval"
    vd = f"{EVAL_DIR}/runs/{a.run}"
    os.makedirs(vd, exist_ok=True)

    import torch
    from unsloth import FastLanguageModel

    laadi = a.adapter if a.adapter else a.base
    print(f"=== laadin: {laadi}", flush=True)
    model, tok = FastLanguageModel.from_pretrained(
        model_name=laadi, max_seq_length=4096, dtype=None, load_in_4bit=True)
    FastLanguageModel.for_inference(model)

    SYSTEM = ("Sa oled abivalmis assistent. Vasta eesti keeles, "
              "kui kasutaja kirjutab eesti keeles.")
    kirjed = [json.loads(r) for r in open(a.eval, encoding="utf-8") if r.strip()]
    if a.limit: kirjed = kirjed[:a.limit]

    torch.manual_seed(20260822)
    tulemused, t0 = [], time.time()
    for i, k in enumerate(kirjed, 1):
        msgs = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": k["prompt"]}]
        tekst = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True,
                                        enable_thinking=a.thinking)
        # NB: Qwen3.8 "tokenizer" on multimodaalne protsessor — positsiooniline
        # argument läheks pildiparserisse. Tekst tuleb anda nimeliselt.
        sisend = tok(text=tekst, return_tensors="pt").to("cuda")
        t1 = time.time()
        with torch.no_grad():
            valjund = model.generate(**sisend, max_new_tokens=a.max_new,
                                     temperature=0.3, top_p=0.9, top_k=40,
                                     do_sample=True, pad_token_id=tok.eos_token_id)
        vastus = tok.decode(valjund[0][sisend["input_ids"].shape[1]:],
                            skip_special_tokens=True)
        tulemused.append({**k, "vastus": vastus, "latents_s": round(time.time()-t1, 2)})
        if i % 20 == 0 or i == len(kirjed):
            print(f"  {i}/{len(kirjed)} ({(time.time()-t0)/60:.1f} min)", flush=True)

    with open(f"{vd}/vastused.jsonl", "w", encoding="utf-8") as f:
        for t in tulemused:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    with open(f"{vd}/konfiguratsioon.json", "w", encoding="utf-8") as f:
        json.dump({"run": a.run, "baas": a.base, "adapter": a.adapter,
                   "torustik": "unsloth bnb-4bit", "seed": 20260822,
                   "seaded": {"temperature": 0.3, "top_p": 0.9, "top_k": 40,
                              "max_new_tokens": a.max_new},
                   "system": SYSTEM, "ulesandeid": len(kirjed)}, f,
                  ensure_ascii=False, indent=1)
    tyhjad = sum(1 for t in tulemused if not t["vastus"].strip())
    print(f"\nVALMIS → {vd}/vastused.jsonl | {(time.time()-t0)/60:.1f} min | "
          f"tühje {tyhjad}", flush=True)

if __name__ == "__main__":
    main()
