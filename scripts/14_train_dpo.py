#!/usr/bin/env python3
"""DPO-treening: õpetab mudelit EELISTAMA head vastust halvale.

Erinevus SFT-st: SFT õpetab "kirjuta nii", DPO õpetab "eelista seda, mitte teist".
Just see parandab stiili ja loomulikkust, mida SFT ei suuda (kordused, tõlkelisus).

Jätkab olemasolevast SFT-adapterist. LR on oluliselt väiksem kui SFT-l
(nõukoja soovitus 5e-6…2e-5), sest DPO nihutab käitumist, mitte ei õpeta uut.

Kasutus:
  python 14_train_dpo.py --run dpo1 --resume-adapter .../ring4/final
"""
import argparse, json, os, time

os.environ.setdefault("UNSLOTH_RETURN_LOGITS", "0")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--data", default="/mnt/varu/qwen38-et-data/processed/dpo_korpus.jsonl")
    ap.add_argument("--base", default="/mnt/varu/qwen38-et-data/models/Qwen3.8-27B")
    ap.add_argument("--resume-adapter", required=True,
                    help="SFT-adapter, mille pealt DPO jätkab")
    ap.add_argument("--lr", type=float, default=8e-6)
    ap.add_argument("--beta", type=float, default=0.1,
                    help="DPO beta: väiksem = julgem nihe, suurem = konservatiivsem")
    ap.add_argument("--ctx", type=int, default=1536)
    ap.add_argument("--grad-accum", type=int, default=16)
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--max-steps", type=int, default=-1)
    ap.add_argument("--kihid", default="", help="komaga: ainult need kihid (nt 'stiil')")
    a = ap.parse_args()

    VALJUND = f"/mnt/varu/qwen38-et-data/adapters/{a.run}"
    os.makedirs(VALJUND, exist_ok=True)

    import torch
    from unsloth import FastLanguageModel
    from datasets import load_dataset
    from trl import DPOTrainer, DPOConfig
    from peft import PeftModel

    t0 = time.time()
    print(f"=== laadin baasi 4-bitisena + SFT-adapteri: {a.resume_adapter}", flush=True)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=a.base, max_seq_length=a.ctx, dtype=None,
        load_in_4bit=True, full_finetuning=False)
    model = PeftModel.from_pretrained(model, a.resume_adapter, is_trainable=True)
    treenitavaid = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"    treenitavaid: {treenitavaid/1e6:.1f}M | VRAM "
          f"{torch.cuda.memory_allocated()/1e9:.1f} GB", flush=True)

    ds = load_dataset("json", data_files=a.data, split="train")
    if a.kihid:
        lubatud = set(a.kihid.split(","))
        ds = ds.filter(lambda x: x.get("kiht") in lubatud)

    # Chat-mall rakendatakse SIIN (korpus ise on mudelisõltumatu).
    # enable_thinking=False — sama nagu SFT-s, muidu tekib formaadinihe.
    def vorminda(x):
        p = tokenizer.apply_chat_template(
            [{"role": "system", "content":
              "Sa oled abivalmis assistent. Vasta loomulikus ja korrektses eesti keeles."},
             {"role": "user", "content": x["prompt"]}],
            tokenize=False, add_generation_prompt=True, enable_thinking=False)
        return {"prompt": p,
                "chosen": x["chosen"] + tokenizer.eos_token,
                "rejected": x["rejected"] + tokenizer.eos_token}
    ds = ds.map(vorminda, remove_columns=[c for c in ds.column_names
                                          if c not in ("prompt", "chosen", "rejected")])
    print(f"=== andmed: {len(ds)} eelistuspaari", flush=True)

    cfg = DPOConfig(
        output_dir=VALJUND,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=a.grad_accum,
        num_train_epochs=a.epochs if a.max_steps < 0 else 1,
        max_steps=a.max_steps,
        learning_rate=a.lr,
        beta=a.beta,
        warmup_ratio=0.05,
        logging_steps=10,
        optim="paged_adamw_8bit",
        lr_scheduler_type="cosine",
        seed=20260824,
        max_grad_norm=1.0,
        max_length=a.ctx,
        max_prompt_length=a.ctx // 2,
        save_steps=200,
        save_total_limit=2,
        report_to="none",
        bf16=True,
    )
    trainer = DPOTrainer(model=model, args=cfg, train_dataset=ds,
                         processing_class=tokenizer)
    print(f"=== DPO ALGAB | run={a.run} | lr={a.lr} | beta={a.beta}", flush=True)
    tulemus = trainer.train()

    kestus = (time.time() - t0) / 60
    tipp = torch.cuda.max_memory_reserved() / 1e9
    model.save_pretrained(f"{VALJUND}/final")
    tokenizer.save_pretrained(f"{VALJUND}/final")
    kokkuvote = {"run": a.run, "meetod": "DPO", "andmed": a.data,
                 "lahteadapter": a.resume_adapter, "paare": len(ds),
                 "lr": a.lr, "beta": a.beta, "ctx": a.ctx,
                 "train_loss": float(tulemus.training_loss),
                 "samme": int(tulemus.global_step),
                 "kestus_min": round(kestus, 1), "tipp_vram_gb": round(tipp, 1),
                 "adapter": f"{VALJUND}/final"}
    with open(f"{VALJUND}/kokkuvote.json", "w", encoding="utf-8") as f:
        json.dump(kokkuvote, f, ensure_ascii=False, indent=1)
    print(f"\n=== VALMIS {kestus:.1f} min | tipp-VRAM {tipp:.1f} GB", flush=True)
    print(json.dumps(kokkuvote, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
