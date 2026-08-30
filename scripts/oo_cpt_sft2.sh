#!/bin/bash
# CPT-haru oskuste taastamine: kombo 2. epohh → eval + sond
set -u
cd /mnt/varu/qwen38-et-data || exit 1
S=/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/scripts
A=/mnt/varu/qwen38-et-data/adapters
P=/mnt/varu/qwen38-et-data/processed

echo "kombo e2 algab $(date +%H:%M)"
.train-venv/bin/python "$S/06_train_sft.py" --run cpt1-sft2 \
  --data "$P/sft_kombo.jsonl" --resume-adapter "$A/cpt1-sft/final" \
  --lr 1.5e-5 --save-steps 200 > "$A/cpt1-sft2.log" 2>&1
grep -q "=== VALMIS" "$A/cpt1-sft2.log" || { echo "E2 EBAÕNNESTUS"; exit 1; }
echo "kombo e2 treenitud $(date +%H:%M)"
sleep 10
.train-venv/bin/python "$S/07b_eval_local.py" --run cpt1-sft2-bnb --adapter "$A/cpt1-sft2/final" > "$A/eval-cpt1-sft2.log" 2>&1
grep -q "VALMIS →" "$A/eval-cpt1-sft2.log" && python3 "$S/08_score.py" --run cpt1-sft2-bnb > "$A/cpt1-sft2-skoor.txt" 2>&1
echo "EVAL: $(grep ÜLDSKOOR "$A/cpt1-sft2-skoor.txt" | head -1)"
.train-venv/bin/python llama.cpp/convert_lora_to_gguf.py "$A/cpt1-sft2/final" \
  --base models/Qwen3.8-27B --outfile "$A/qwen38-et-cpt1s2-lora.gguf" --outtype f16 >> "$A/cpt1-sft2.log" 2>&1
cat > /tmp/Modelfile-cpts2 <<'MF'
FROM qwen3.8:27b
ADAPTER /mnt/varu/qwen38-et-data/adapters/qwen38-et-cpt1s2-lora.gguf
SYSTEM Sa oled abivalmis assistent. Vasta loomulikus ja korrektses eesti keeles.
PARAMETER temperature 0.4
PARAMETER top_p 0.9
PARAMETER top_k 20
PARAMETER repeat_penalty 1.15
MF
ollama create qwen3.8-et:27b-cpt2 -f /tmp/Modelfile-cpts2 >> "$A/cpt1-sft2.log" 2>&1
python3 "$S/15_fraasisond.py" --n 0 --mudel qwen3.8-et:27b-cpt2 \
  --valjund "$P/fraasisond-cpt2.jsonl" > "$A/fraasisond-cpt2.log" 2>&1
echo "SOND: $(grep TABAVUS "$A/fraasisond-cpt2.log")"
echo "E2 AHEL VALMIS $(date +%H:%M)"
