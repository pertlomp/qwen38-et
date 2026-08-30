#!/bin/bash
# Ring 8 → eval → gguf v8 → fraasisond
cd /mnt/varu/qwen38-et-data || exit 1
S=/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/scripts
A=/mnt/varu/qwen38-et-data/adapters

ollama stop qwen3.8-et:27b-v7 2>/dev/null; sleep 8
echo "ring8 algab $(date +%H:%M)"
.train-venv/bin/python "$S/06_train_sft.py" --run ring8 \
  --data /mnt/varu/qwen38-et-data/processed/sft_v1_ring8.jsonl \
  --resume-adapter "$A/ring7/final" --lr 2e-5 --save-steps 100 > "$A/ring8.log" 2>&1
grep -q "=== VALMIS" "$A/ring8.log" || { echo "RING8 EBAÕNNESTUS"; exit 1; }
echo "ring8 treenitud $(date +%H:%M)"

sleep 15
.train-venv/bin/python "$S/07b_eval_local.py" --run ring8-bnb --adapter "$A/ring8/final" > "$A/eval-ring8-bnb.log" 2>&1
if grep -q "VALMIS →" "$A/eval-ring8-bnb.log"; then
  python3 "$S/08_score.py" --run ring8-bnb > "$A/ring8-bnb-skoor.txt" 2>&1
  echo "ring8 HINNATUD: $(grep ÜLDSKOOR "$A/ring8-bnb-skoor.txt" | head -1)"
else
  echo "ring8 EVAL EBAÕNNESTUS"; exit 1
fi

.train-venv/bin/python llama.cpp/convert_lora_to_gguf.py "$A/ring8/final" \
  --base models/Qwen3.8-27B --outfile "$A/qwen38-et-v8-ring8-lora.gguf" --outtype f16 >> "$A/ring8.log" 2>&1
cat > /tmp/Modelfile-v8 <<'MF'
FROM qwen3.8:27b
ADAPTER /mnt/varu/qwen38-et-data/adapters/qwen38-et-v8-ring8-lora.gguf
SYSTEM Sa oled abivalmis assistent. Vasta loomulikus ja korrektses eesti keeles.
PARAMETER temperature 0.4
PARAMETER top_p 0.9
PARAMETER top_k 20
MF
ollama create qwen3.8-et:27b-v8 -f /tmp/Modelfile-v8 >> "$A/ring8.log" 2>&1
python3 "$S/15_fraasisond.py" --n 0 --mudel qwen3.8-et:27b-v8 \
  --valjund /mnt/varu/qwen38-et-data/processed/fraasisond-ring8.jsonl > "$A/fraasisond-ring8.log" 2>&1
echo "fraasisond: $(grep TABAVUS "$A/fraasisond-ring8.log")"
echo "RING8 AHEL VALMIS — GPU VABA."
