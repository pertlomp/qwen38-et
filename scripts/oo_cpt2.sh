#!/bin/bash
# CPT ahel v2: pakitud korpusega, jätkab sammust 3 (korpus+baasi-ppl tehtud)
set -u
cd /mnt/varu/qwen38-et-data || exit 1
S=/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/scripts
A=/mnt/varu/qwen38-et-data/adapters
P=/mnt/varu/qwen38-et-data/processed

echo "=== 3/7 CPT-treening PAKITULT $(date +%H:%M)"
.train-venv/bin/python "$S/43_train_cpt.py" --run cpt1 \
  --data "$P/cpt_korpus_pakitud.jsonl" > "$A/cpt1.log" 2>&1
grep -q "=== VALMIS" "$A/cpt1.log" || { echo "CPT EBAÕNNESTUS"; tail -5 "$A/cpt1.log"; exit 1; }
echo "CPT treenitud $(date +%H:%M)"

echo "=== 4/7 CPT perplexity $(date +%H:%M)"
.train-venv/bin/python "$S/44_perplexity.py" --adapter "$A/cpt1/final" --valjund "$A/ppl-cpt1.json" > "$A/ppl-cpt1.log" 2>&1 || echo "ppl viga (jätkan)"
grep PERPLEXITY "$A/ppl-cpt1.log" || true

echo "=== 5/7 SFT-kombo $(date +%H:%M)"
python3 "$S/45_build_sft_kombo.py" || exit 1
.train-venv/bin/python "$S/06_train_sft.py" --run cpt1-sft \
  --data "$P/sft_kombo.jsonl" --resume-adapter "$A/cpt1/final" \
  --lr 2e-5 --save-steps 200 > "$A/cpt1-sft.log" 2>&1
grep -q "=== VALMIS" "$A/cpt1-sft.log" || { echo "SFT-KOMBO EBAÕNNESTUS"; exit 1; }
echo "SFT-kombo treenitud $(date +%H:%M)"

echo "=== 6/7 eval $(date +%H:%M)"
sleep 10
.train-venv/bin/python "$S/07b_eval_local.py" --run cpt1-sft-bnb --adapter "$A/cpt1-sft/final" > "$A/eval-cpt1-sft.log" 2>&1
grep -q "VALMIS →" "$A/eval-cpt1-sft.log" && python3 "$S/08_score.py" --run cpt1-sft-bnb > "$A/cpt1-sft-skoor.txt" 2>&1
echo "EVAL: $(grep ÜLDSKOOR "$A/cpt1-sft-skoor.txt" | head -1)"

echo "=== 7/7 gguf + sond $(date +%H:%M)"
.train-venv/bin/python llama.cpp/convert_lora_to_gguf.py "$A/cpt1-sft/final" \
  --base models/Qwen3.8-27B --outfile "$A/qwen38-et-cpt1-lora.gguf" --outtype f16 >> "$A/cpt1-sft.log" 2>&1
cat > /tmp/Modelfile-cpt <<'MF'
FROM qwen3.8:27b
ADAPTER /mnt/varu/qwen38-et-data/adapters/qwen38-et-cpt1-lora.gguf
SYSTEM Sa oled abivalmis assistent. Vasta loomulikus ja korrektses eesti keeles.
PARAMETER temperature 0.4
PARAMETER top_p 0.9
PARAMETER top_k 20
PARAMETER repeat_penalty 1.15
MF
ollama create qwen3.8-et:27b-cpt1 -f /tmp/Modelfile-cpt >> "$A/cpt1-sft.log" 2>&1
python3 "$S/15_fraasisond.py" --n 0 --mudel qwen3.8-et:27b-cpt1 \
  --valjund "$P/fraasisond-cpt1.jsonl" > "$A/fraasisond-cpt1.log" 2>&1
echo "SOND: $(grep TABAVUS "$A/fraasisond-cpt1.log")"
echo "CPT-PILOOT VALMIS $(date +%H:%M) — GPU VABA"
