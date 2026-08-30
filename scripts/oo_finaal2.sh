#!/bin/bash
# Lõpuahela jätk ring3-st (GPU vabastusega)
set -u
cd /mnt/varu/qwen38-et-data || exit 1
S=/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/scripts
A=/mnt/varu/qwen38-et-data/adapters
P=/mnt/varu/qwen38-et-data/processed

for m in $(ollama ps 2>/dev/null | tail -n +2 | awk '{print $1}' | grep -v bge); do ollama stop "$m" 2>/dev/null; done
until [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -lt 8000 ]; do sleep 5; done
echo "GPU vaba, ring3 algab $(date +%H:%M)"

.train-venv/bin/python "$S/06_train_sft.py" --run cpt1-ring3 \
  --data "$P/sft_cptring3.jsonl" --resume-adapter "$A/cpt1-ring2/final" \
  --lr 1.5e-5 --save-steps 200 > "$A/cpt1-ring3.log" 2>&1
grep -q "=== VALMIS" "$A/cpt1-ring3.log" || { echo RING3 EBAÕNNESTUS; exit 1; }
echo "ring3 treenitud $(date +%H:%M)"

.train-venv/bin/python "$S/14_train_dpo.py" --run cpt1-dpo --resume-adapter "$A/cpt1-ring3/final" \
  --data "$P/dpo_fraasivead_cpt2.jsonl" \
  --lr 1.5e-6 --beta 0.3 --ctx 1024 --grad-accum 8 > "$A/cpt1-dpo.log" 2>&1
grep -q "=== VALMIS" "$A/cpt1-dpo.log" && LOPP="$A/cpt1-dpo/final" || { echo "DPO kukkus, kasutan ring3"; LOPP="$A/cpt1-ring3/final"; }
echo "LÕPP-ADAPTER: $LOPP"

sleep 10
.train-venv/bin/python "$S/07b_eval_local.py" --run FINAL-bnb --adapter "$LOPP" > "$A/eval-FINAL.log" 2>&1
grep -q "VALMIS →" "$A/eval-FINAL.log" && python3 "$S/08_score.py" --run FINAL-bnb > "$A/FINAL-skoor.txt" 2>&1
echo "EVAL: $(grep ÜLDSKOOR "$A/FINAL-skoor.txt" | head -1)"
.train-venv/bin/python llama.cpp/convert_lora_to_gguf.py "$LOPP" \
  --base models/Qwen3.8-27B --outfile "$A/qwen38-et-FINAL-lora.gguf" --outtype f16 >> "$A/cpt1-dpo.log" 2>&1
cat > /tmp/Modelfile-FINAL <<'MF'
FROM qwen3.8:27b
ADAPTER /mnt/varu/qwen38-et-data/adapters/qwen38-et-FINAL-lora.gguf
SYSTEM Sa oled abivalmis assistent. Vasta loomulikus ja korrektses eesti keeles.
PARAMETER temperature 0.4
PARAMETER top_p 0.9
PARAMETER top_k 20
PARAMETER repeat_penalty 1.15
MF
ollama create qwen3.8-et:27b-FINAL -f /tmp/Modelfile-FINAL >> "$A/cpt1-dpo.log" 2>&1
python3 "$S/15_fraasisond.py" --n 0 --mudel qwen3.8-et:27b-FINAL \
  --valjund "$P/fraasisond-FINAL.jsonl" > "$A/fraasisond-FINAL.log" 2>&1
echo "SOND: $(grep TABAVUS "$A/fraasisond-FINAL.log")"
python3 "$S/28_valine_eval.py" --mudel qwen3.8-et:27b-FINAL --valjund /home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/eval/runs/mmlu-FINAL.json > "$A/mmlu-FINAL.log" 2>&1
echo "MMLU: $(grep TÄPSUS "$A/mmlu-FINAL.log" | tail -1)"
.dl-venv/bin/python "$S/31_estqa_eval.py" --mudel qwen3.8-et:27b-FINAL --valjund /home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/eval/runs/estqa-FINAL.json > "$A/estqa-FINAL.log" 2>&1
echo "EstQA: $(grep 'EstQA (' "$A/estqa-FINAL.log" | tail -1)"
python3 "$S/38_humaneval.py" --mudel qwen3.8-et:27b-FINAL --n 60 > "$A/he-FINAL.log" 2>&1
echo "HumanEval: $(grep PASS@1 "$A/he-FINAL.log")"
echo "LÕPUAHEL VALMIS $(date +%H:%M) — GPU VABA"
