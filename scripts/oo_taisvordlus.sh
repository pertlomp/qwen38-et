#!/bin/bash
# Täisvõrdlus, eval IGA sammu järel:
#   rank16: ring1-4 (tehtud) + DPO
#   rank32: ring3 (tehtud) + ring1 + ring2 + ring4 + DPO
# Käivitatakse pärast rank16 DPO treeningu algust; ootab selle lõppu ise.
cd /mnt/varu/qwen38-et-data || exit 1
S=/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/scripts
A=/mnt/varu/qwen38-et-data/adapters

hinda () {   # $1=run_id  $2=adapteri tee
  sleep 15
  .train-venv/bin/python "$S/07b_eval_local.py" --run "$1" --adapter "$2" > "$A/eval-$1.log" 2>&1
  if grep -q "VALMIS →" "$A/eval-$1.log"; then
    python3 "$S/08_score.py" --run "$1" > "$A/$1-skoor.txt" 2>&1
    echo "$1 HINNATUD $(date +%H:%M): $(grep ÜLDSKOOR "$A/$1-skoor.txt" | head -1)"
  else
    echo "$1 EVAL EBAÕNNESTUS"
  fi
}

# --- 1. rank16 DPO lõpp + eval ---
until grep -q "=== VALMIS" "$A/dpo1.log" 2>/dev/null || \
      grep -qE "Traceback|OutOfMemory|Killed" "$A/dpo1.log" 2>/dev/null; do sleep 60; done
if grep -q "=== VALMIS" "$A/dpo1.log"; then
  echo "rank16 DPO treenitud $(date +%H:%M)"
  hinda dpo1-bnb "$A/dpo1/final"
else
  echo "rank16 DPO EBAÕNNESTUS — jätkan rank32 ketiga"
fi

# --- 2. rank32 kett, eval iga ringi järel ---
EELMINE="$A/rank32-solo/final"
for R in "r32-ring1:processed/sft_v1_10m.jsonl" \
         "r32-ring2:processed/sft_v1_ring2.jsonl" \
         "r32-ring4:processed/sft_v1_ring4.jsonl"; do
  NIMI="${R%%:*}"; DATA="${R##*:}"
  echo "$NIMI algab $(date +%H:%M)"
  .train-venv/bin/python "$S/06_train_sft.py" --run "$NIMI" \
    --data "/mnt/varu/qwen38-et-data/$DATA" --rank 32 --alpha 64 \
    --resume-adapter "$EELMINE" --save-steps 500 > "$A/$NIMI.log" 2>&1
  if ! grep -q "=== VALMIS" "$A/$NIMI.log"; then
    echo "$NIMI EBAÕNNESTUS — kett peatub"; exit 1
  fi
  echo "$NIMI treenitud $(date +%H:%M)"
  EELMINE="$A/$NIMI/final"
  hinda "$NIMI-bnb" "$EELMINE"
done

# --- 3. rank32 DPO (sümmeetriline rank16-ga) ---
echo "rank32 DPO algab $(date +%H:%M)"
.train-venv/bin/python "$S/14_train_dpo.py" --run dpo-r32 \
  --resume-adapter "$EELMINE" --ctx 1024 --grad-accum 8 > "$A/dpo-r32.log" 2>&1
if grep -q "=== VALMIS" "$A/dpo-r32.log"; then
  echo "rank32 DPO treenitud $(date +%H:%M)"
  hinda dpo-r32-bnb "$A/dpo-r32/final"
else
  echo "rank32 DPO EBAÕNNESTUS"
fi
echo "TÄISVÕRDLUS VALMIS — GPU VABA."
