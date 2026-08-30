#!/usr/bin/env python3
"""CPT (continued pretraining) QLoRA-ga BAASMUDELIST — nõukoja piloot.

Erineb SFT-st: toortekst, pakitud järjestused (packing), madal LR, 1 läbimine.
Sol: "alustada baasmudelist, mitte adapterist; rank 16 või 32; LR 5e-6..1e-5;
cosine; warmup 1-2%; checkpoint iga 25M tokeni järel."
"""
import argparse, json, os, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="cpt1")
    ap.add_argument("--data", default="/mnt/varu/qwen38-et-data/processed/cpt_korpus.jsonl")
    ap.add_argument("--base", default="/mnt/varu/qwen38-et-data/models/Qwen3.8-27B")
    ap.add_argument("--lr", type=float, default=8e-6)
    ap.add_argument("--rank", type=int, default=32)
    ap.add_argument("--alpha", type=int, default=64)
    ap.add_argument("--ctx", type=int, default=2048)
    ap.add_argument("--grad-accum", type=int, default=16)
    ap.add_argument("--save-steps", type=int, default=500)
    a = ap.parse_args()

    VALJUND = f"/mnt/varu/qwen38-et-data/adapters/{a.run}"
    os.makedirs(VALJUND, exist_ok=True)

    import torch
    from unsloth import FastLanguageModel
    from datasets import load_dataset
    from trl import SFTTrainer, SFTConfig

    t0 = time.time()
    print(f"=== CPT: laadin baasi 4-bitisena: {a.base}", flush=True)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=a.base, max_seq_length=a.ctx, dtype=None,
        load_in_4bit=True, full_finetuning=False)
    print(f"    laetud {time.time()-t0:.0f} s", flush=True)

    model = FastLanguageModel.get_peft_model(
        model, r=a.rank, lora_alpha=a.alpha, lora_dropout=0.0,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        bias="none", use_gradient_checkpointing="unsloth",
        random_state=20260828, use_rslora=False)

    ds = load_dataset("json", data_files=a.data, split="train")
    print(f"=== korpus: {len(ds)} lõiku", flush=True)

    trainer = SFTTrainer(
        model=model, processing_class=tokenizer, train_dataset=ds,
        args=SFTConfig(
            output_dir=VALJUND,
            dataset_text_field="text",
            packing=True,                     # pakitud järjestused — CPT võti
            max_length=a.ctx,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=a.grad_accum,
            num_train_epochs=1.0,
            learning_rate=a.lr,
            lr_scheduler_type="cosine",
            warmup_ratio=0.02,
            optim="paged_adamw_8bit",
            logging_steps=25,
            save_steps=a.save_steps,
            save_total_limit=3,
            bf16=True,
            seed=20260828,
            report_to=[]))
    t1 = time.time()
    trainer.train()
    model.save_pretrained(f"{VALJUND}/final")
    tokenizer.save_pretrained(f"{VALJUND}/final")
    kestus = (time.time() - t1) / 60
    print(f"=== VALMIS {kestus:.1f} min | tipp-VRAM "
          f"{torch.cuda.max_memory_allocated()/1e9:.1f} GB", flush=True)
    json.dump({"run": a.run, "lr": a.lr, "rank": a.rank, "ctx": a.ctx,
               "kestus_min": kestus, "adapter": f"{VALJUND}/final"},
              open(f"{VALJUND}/info.json", "w"))

if __name__ == "__main__":
    main()
