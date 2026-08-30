#!/bin/bash
# CPT-haru kirurgiline ring 1: täissond Q6-l → on-policy parandused → SFT → eval+sond
set -u
cd /mnt/varu/qwen38-et-data || exit 1
S=/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/scripts
A=/mnt/varu/qwen38-et-data/adapters
P=/mnt/varu/qwen38-et-data/processed

echo "=== täissond cpt2-q6 $(date +%H:%M)"
python3 "$S/15_fraasisond.py" --n 0 --mudel qwen3.8-et:27b-cpt2-q6 \
  --valjund "$P/fraasisond-cpt2q6.jsonl" > "$A/fraasisond-cpt2q6.log" 2>&1
echo "SOND: $(grep TABAVUS "$A/fraasisond-cpt2q6.log")"
python3 "$S/17_sond_to_treening.py" --sond "$P/fraasisond-cpt2q6.jsonl" \
  --dpo "$P/dpo_fraasivead_cpt2.jsonl" --sft "$P/sft_fraasiparandused_cpt2.jsonl" | head -2
ollama stop qwen3.8-et:27b-cpt2-q6 2>/dev/null; sleep 8

echo "=== ringi andmestik $(date +%H:%M)"
python3 - <<'PY'
import json, random
random.seed(20260830)
P = "/mnt/varu/qwen38-et-data/processed"
def loe(t): return [json.loads(r) for r in open(t)]
siht = loe(f"{P}/sft_fraasiparandused_cpt2.jsonl")
siht += random.sample(loe(f"{P}/fraas_astmevaheldus.jsonl"), 500)
siht += random.sample(loe(f"{P}/fraas_gen.jsonl"), 800)
siht += loe(f"{P}/fraas_gen_r8.jsonl")
replay = [d for d in loe(f"{P}/sft_v1_ring4.jsonl")
          if d.get("kategooria","").startswith("replay")]
replay = random.sample(replay, round(len(siht)/0.85*0.15))
koik = siht + replay
random.shuffle(koik)
with open(f"{P}/sft_cptring1.jsonl","w") as f:
    for d in koik:
        f.write(json.dumps({"messages": d["messages"]}, ensure_ascii=False)+"\n")
print(f"CPT-RING1: {len(koik)} näidet")
PY

echo "=== treening $(date +%H:%M)"
.train-venv/bin/python "$S/06_train_sft.py" --run cpt1-ring1 \
  --data "$P/sft_cptring1.jsonl" --resume-adapter "$A/cpt1-sft2/final" \
  --lr 2e-5 --save-steps 200 > "$A/cpt1-ring1.log" 2>&1
grep -q "=== VALMIS" "$A/cpt1-ring1.log" || { echo EBAÕNNESTUS; exit 1; }
echo "treenitud $(date +%H:%M)"
sleep 10
.train-venv/bin/python "$S/07b_eval_local.py" --run cpt1-ring1-bnb --adapter "$A/cpt1-ring1/final" > "$A/eval-cpt1-ring1.log" 2>&1
grep -q "VALMIS →" "$A/eval-cpt1-ring1.log" && python3 "$S/08_score.py" --run cpt1-ring1-bnb > "$A/cpt1-ring1-skoor.txt" 2>&1
echo "EVAL: $(grep ÜLDSKOOR "$A/cpt1-ring1-skoor.txt" | head -1)"
echo "CPT-RING1 VALMIS $(date +%H:%M)"
