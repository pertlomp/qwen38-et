#!/bin/bash
# Ring 5 (fraasikäänamine, kirurgiline) → eval → fraasisond uuesti
cd /mnt/varu/qwen38-et-data || exit 1
S=/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/scripts
A=/mnt/varu/qwen38-et-data/adapters

echo "ring5 algab $(date +%H:%M)"
.train-venv/bin/python "$S/06_train_sft.py" --run ring5 \
  --data /mnt/varu/qwen38-et-data/processed/sft_v1_ring5.jsonl \
  --resume-adapter "$A/dpo2/final" --lr 2e-5 --save-steps 100 > "$A/ring5.log" 2>&1
grep -q "=== VALMIS" "$A/ring5.log" || { echo "RING5 EBAÕNNESTUS"; exit 1; }
echo "ring5 treenitud $(date +%H:%M)"

sleep 15
.train-venv/bin/python "$S/07b_eval_local.py" --run ring5-bnb --adapter "$A/ring5/final" > "$A/eval-ring5-bnb.log" 2>&1
if grep -q "VALMIS →" "$A/eval-ring5-bnb.log"; then
  python3 "$S/08_score.py" --run ring5-bnb > "$A/ring5-bnb-skoor.txt" 2>&1
  echo "ring5 HINNATUD: $(grep ÜLDSKOOR "$A/ring5-bnb-skoor.txt" | head -1)"
else
  echo "ring5 EVAL EBAÕNNESTUS"; exit 1
fi
echo "RING5 AHEL VALMIS — GPU VABA."
