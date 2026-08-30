#!/usr/bin/env python3
"""QLoRA SFT-treening: Qwen3.8-27B → eesti keel.

Kasutus:
  python 06_train_sft.py --run suitsutest --max-steps 60
  python 06_train_sft.py --run ring1
  python 06_train_sft.py --run ring2 --data .../sft_v1_ring2.jsonl --resume-adapter .../ring1

Konfiguratsioon on nõukoja soovituste järgi (LOPLIK-PLAAN-v1.md):
rank 16 / alpha 32, ctx 2048, micro-batch 1, grad-accum 16, paged_adamw_8bit,
LR 5e-5 (mitte 2e-4 — 27B instruct-mudelil agressiivne), warmup 3%, clip 1.0.
"""
import argparse, json, os, time

os.environ.setdefault("UNSLOTH_RETURN_LOGITS", "0")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--data", default="/mnt/varu/qwen38-et-data/processed/sft_v1_10m.jsonl")
    ap.add_argument("--base", default="/mnt/varu/qwen38-et-data/models/Qwen3.8-27B")
    ap.add_argument("--max-steps", type=int, default=-1)
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--alpha", type=int, default=32)
    ap.add_argument("--ctx", type=int, default=2048)
    ap.add_argument("--grad-accum", type=int, default=16)
    ap.add_argument("--save-steps", type=int, default=200)
    ap.add_argument("--resume-adapter", default=None, help="jätka olemasolevast adapterist")
    a = ap.parse_args()

    VALJUND = f"/mnt/varu/qwen38-et-data/adapters/{a.run}"
    os.makedirs(VALJUND, exist_ok=True)

    import torch
    from unsloth import FastLanguageModel
    from datasets import load_dataset
    from trl import SFTTrainer, SFTConfig

    t0 = time.time()
    print(f"=== laadin baasmudeli 4-bitisena: {a.base}", flush=True)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=a.base,
        max_seq_length=a.ctx,
        dtype=None,                 # auto → bf16 Blackwellil
        load_in_4bit=True,
        full_finetuning=False,
    )
    print(f"    laetud {time.time()-t0:.0f} s | VRAM {torch.cuda.memory_allocated()/1e9:.1f} GB",
          flush=True)

    if a.resume_adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, a.resume_adapter, is_trainable=True)
        print(f"=== jätkan adapterist: {a.resume_adapter}", flush=True)
    else:
        model = FastLanguageModel.get_peft_model(
            model,
            r=a.rank,
            lora_alpha=a.alpha,
            lora_dropout=0.05,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                            "gate_proj", "up_proj", "down_proj"],
            bias="none",
            use_gradient_checkpointing="unsloth",
            random_state=20260822,
            use_rslora=False,
        )
    treenitavaid = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"    treenitavaid parameetreid: {treenitavaid/1e6:.1f}M", flush=True)

    ds = load_dataset("json", data_files=a.data, split="train")
    # Qwen3.8 on vision-language mudel → TRL ei toeta assistant_only_loss lippu.
    # Sama tulemuse (loss AINULT vastuselt) annab prompt/completion vorm, mida
    # TRL maskib ise: prompt-osa tokenid jäetakse kaost välja.
    # Rakendame chat-malli ise ja anname TRL-ile valmis STRINGID: nii on loss-mask
    # üheselt määratud (completion_only_loss) ega sõltu TRL-i sisemisest
    # vestlusvormi tõlgendusest, mis VL-mudeli mallil katkes.
    def poolita(x):
        m = x["messages"]
        eelnev = [s for s in m if s["role"] != "assistant"]
        vastus = next((s["content"] for s in m if s["role"] == "assistant"), "")
        # enable_thinking=False on OLULINE: vaikimisi lõpetab Qwen3.8 mall prompti
        # AVATUD <think> plokiga, mistõttu ring 1 õpetas mudelit andma vastust
        # mõtlemisploki sisse ilma seda sulgemata. False annab korrektse
        # non-thinking prefiksi (<think>\n\n</think>\n\n), mis vastab sellele,
        # kuidas mudelit tegelikult kasutatakse.
        prompt = tokenizer.apply_chat_template(eelnev, tokenize=False,
                                               add_generation_prompt=True,
                                               enable_thinking=False)
        return {"prompt": prompt, "completion": vastus + tokenizer.eos_token}
    ds = ds.map(poolita, remove_columns=ds.column_names, num_proc=8)
    ds = ds.filter(lambda x: len(x["completion"]) > 5 and len(x["prompt"]) > 5)
    print(f"=== andmed: {len(ds)} näidet ({a.data})", flush=True)

    cfg = SFTConfig(
        output_dir=VALJUND,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=a.grad_accum,
        warmup_ratio=0.03,
        num_train_epochs=a.epochs if a.max_steps < 0 else 1,
        max_steps=a.max_steps,
        learning_rate=a.lr,
        logging_steps=10,
        optim="paged_adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=20260822,
        max_grad_norm=1.0,
        max_length=a.ctx,
        packing=False,               # pakkimine rikuks loss-maski
        completion_only_loss=True,   # loss AINULT vastuselt (prompt maskitakse)
        save_steps=a.save_steps,
        save_total_limit=3,
        report_to="none",
        bf16=True,
    )

    trainer = SFTTrainer(model=model, train_dataset=ds, args=cfg,
                         processing_class=tokenizer)

    print(f"=== TREENING ALGAB | run={a.run} | max_steps={a.max_steps} "
          f"| efektiivne batch={a.grad_accum}", flush=True)
    tulemus = trainer.train()

    tipp_vram = torch.cuda.max_memory_reserved() / 1e9
    kestus_min = (time.time() - t0) / 60
    print(f"\n=== VALMIS {kestus_min:.1f} min | tipp-VRAM {tipp_vram:.1f} GB", flush=True)

    model.save_pretrained(f"{VALJUND}/final")
    tokenizer.save_pretrained(f"{VALJUND}/final")

    kokkuvote = {
        "run": a.run, "andmed": a.data, "baas": a.base,
        "naiteid": len(ds), "max_steps": a.max_steps,
        "hyperparameetrid": {"rank": a.rank, "alpha": a.alpha, "lr": a.lr,
                             "ctx": a.ctx, "grad_accum": a.grad_accum,
                             "optim": "paged_adamw_8bit", "seed": 20260822,
                             "assistant_only_loss": True},
        "treenitavaid_parameetreid": treenitavaid,
        "train_loss": float(tulemus.training_loss),
        "samme": int(tulemus.global_step),
        "kestus_min": round(kestus_min, 1),
        "tipp_vram_gb": round(tipp_vram, 1),
        "adapter": f"{VALJUND}/final",
    }
    with open(f"{VALJUND}/kokkuvote.json", "w", encoding="utf-8") as f:
        json.dump(kokkuvote, f, ensure_ascii=False, indent=1)
    print(json.dumps(kokkuvote, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
