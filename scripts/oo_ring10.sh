#!/bin/bash
# Ring 8 → eval → gguf v8 → fraasisond
cd /mnt/varu/qwen38-et-data || exit 1
S=/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/scripts
A=/mnt/varu/qwen38-et-data/adapters

ollama stop qwen3.8-et:27b-v9 2>/dev/null; sleep 8
echo "ring10 algab $(date +%H:%M)"
.train-venv/bin/python "$S/06_train_sft.py" --run ring10 \
  --data /mnt/varu/qwen38-et-data/processed/sft_v1_ring10.jsonl \
  --resume-adapter "$A/ring9/final" --lr 2e-5 --save-steps 100 > "$A/ring10.log" 2>&1
grep -q "=== VALMIS" "$A/ring10.log" || { echo "RING8 EBAÕNNESTUS"; exit 1; }
echo "ring10 treenitud $(date +%H:%M)"

sleep 15
.train-venv/bin/python "$S/07b_eval_local.py" --run ring10-bnb --adapter "$A/ring10/final" > "$A/eval-ring10-bnb.log" 2>&1
if grep -q "VALMIS →" "$A/eval-ring10-bnb.log"; then
  python3 "$S/08_score.py" --run ring10-bnb > "$A/ring10-bnb-skoor.txt" 2>&1
  echo "ring10 HINNATUD: $(grep ÜLDSKOOR "$A/ring10-bnb-skoor.txt" | head -1)"
else
  echo "ring10 EVAL EBAÕNNESTUS"; exit 1
fi

.train-venv/bin/python llama.cpp/convert_lora_to_gguf.py "$A/ring10/final" \
  --base models/Qwen3.8-27B --outfile "$A/qwen38-et-v8-ring10-lora.gguf" --outtype f16 >> "$A/ring10.log" 2>&1
cat > /tmp/Modelfile-v10 <<'MF'
FROM qwen3.8:27b
ADAPTER /mnt/varu/qwen38-et-data/adapters/qwen38-et-v8-ring10-lora.gguf
SYSTEM Sa oled abivalmis assistent. Vasta loomulikus ja korrektses eesti keeles.
PARAMETER temperature 0.4
PARAMETER top_p 0.9
PARAMETER top_k 20
MF
ollama create qwen3.8-et:27b-v10 -f /tmp/Modelfile-v10 >> "$A/ring10.log" 2>&1
python3 "$S/15_fraasisond.py" --n 0 --mudel qwen3.8-et:27b-v10 \
  --valjund /mnt/varu/qwen38-et-data/processed/fraasisond-ring10.jsonl > "$A/fraasisond-ring10.log" 2>&1
echo "fraasisond: $(grep TABAVUS "$A/fraasisond-ring10.log")"
echo "RING8 AHEL VALMIS — GPU VABA."
