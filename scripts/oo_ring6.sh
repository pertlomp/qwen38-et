#!/bin/bash
# Ring 6 (viis moodulit) → eval → gguf → fraasisond
cd /mnt/varu/qwen38-et-data || exit 1
S=/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/scripts
A=/mnt/varu/qwen38-et-data/adapters

echo "ring6 algab $(date +%H:%M)"
.train-venv/bin/python "$S/06_train_sft.py" --run ring6 \
  --data /mnt/varu/qwen38-et-data/processed/sft_v1_ring6.jsonl \
  --resume-adapter "$A/dpo3/final" --lr 2e-5 --save-steps 100 > "$A/ring6.log" 2>&1
grep -q "=== VALMIS" "$A/ring6.log" || { echo "RING6 EBAÕNNESTUS"; exit 1; }
echo "ring6 treenitud $(date +%H:%M)"

sleep 15
.train-venv/bin/python "$S/07b_eval_local.py" --run ring6-bnb --adapter "$A/ring6/final" > "$A/eval-ring6-bnb.log" 2>&1
if grep -q "VALMIS →" "$A/eval-ring6-bnb.log"; then
  python3 "$S/08_score.py" --run ring6-bnb > "$A/ring6-bnb-skoor.txt" 2>&1
  echo "ring6 HINNATUD: $(grep ÜLDSKOOR "$A/ring6-bnb-skoor.txt" | head -1)"
else
  echo "ring6 EVAL EBAÕNNESTUS"; exit 1
fi

# gguf + Ollama v5 + fraasisond
.train-venv/bin/python llama.cpp/convert_lora_to_gguf.py "$A/ring6/final" \
  --base models/Qwen3.8-27B --outfile "$A/qwen38-et-v5-ring6-lora.gguf" --outtype f16 >> "$A/ring6.log" 2>&1
cat > /tmp/Modelfile-v5 <<'MF'
FROM qwen3.8:27b
ADAPTER /mnt/varu/qwen38-et-data/adapters/qwen38-et-v5-ring6-lora.gguf
SYSTEM Sa oled abivalmis assistent. Vasta loomulikus ja korrektses eesti keeles.
PARAMETER temperature 0.4
PARAMETER top_p 0.9
PARAMETER top_k 20
MF
ollama create qwen3.8-et:27b-v5 -f /tmp/Modelfile-v5 >> "$A/ring6.log" 2>&1
python3 "$S/15_fraasisond.py" --n 0 --mudel qwen3.8-et:27b-v5 \
  --valjund /mnt/varu/qwen38-et-data/processed/fraasisond-ring6.jsonl > "$A/fraasisond-ring6.log" 2>&1
echo "fraasisond: $(grep TABAVUS "$A/fraasisond-ring6.log")"
echo "RING6 AHEL VALMIS — GPU VABA."
