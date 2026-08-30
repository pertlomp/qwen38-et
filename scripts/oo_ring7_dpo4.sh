#!/bin/bash
# Ootab korje lõppu → ring7 SFT → eval → dpo4 (korje + ring6-sondi paarid) → eval → gguf v6 → sond
cd /mnt/varu/qwen38-et-data || exit 1
S=/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/scripts
A=/mnt/varu/qwen38-et-data/adapters
P=/mnt/varu/qwen38-et-data/processed

hinda () {
  sleep 15
  .train-venv/bin/python "$S/07b_eval_local.py" --run "$1" --adapter "$2" > "$A/eval-$1.log" 2>&1
  if grep -q "VALMIS →" "$A/eval-$1.log"; then
    python3 "$S/08_score.py" --run "$1" > "$A/$1-skoor.txt" 2>&1
    echo "$1 HINNATUD: $(grep ÜLDSKOOR "$A/$1-skoor.txt" | head -1)"
  else
    echo "$1 EVAL EBAÕNNESTUS"; exit 1
  fi
}

# 1. oota korje lõppu (Ollama vabastab GPU ise)
until grep -q "valmis:" "$A/onpolicy-korje-v5.log" 2>/dev/null; do sleep 20; done
ollama stop qwen3.8-et:27b-v5 2>/dev/null; sleep 10
echo "korje valmis: $(grep 'valmis:' "$A/onpolicy-korje-v5.log")"

# 2. ring7 SFT
echo "ring7 algab $(date +%H:%M)"
.train-venv/bin/python "$S/06_train_sft.py" --run ring7 \
  --data "$P/sft_v1_ring7.jsonl" \
  --resume-adapter "$A/ring6/final" --lr 2e-5 --save-steps 100 > "$A/ring7.log" 2>&1
grep -q "=== VALMIS" "$A/ring7.log" || { echo "RING7 EBAÕNNESTUS"; exit 1; }
echo "ring7 treenitud $(date +%H:%M)"
hinda ring7-bnb "$A/ring7/final"

# 3. dpo4 korpus: ring6-sondi 60 + korje ~350, dedup
python3 - <<'PY'
import json
nahtud, koik = set(), []
for tee in ("/mnt/varu/qwen38-et-data/processed/dpo_fraasivead_ring6.jsonl",
            "/mnt/varu/qwen38-et-data/processed/dpo_onpolicy_r6.jsonl"):
    for r in open(tee):
        d = json.loads(r)
        if d["prompt"] not in nahtud and d["chosen"].lower() != d["rejected"].lower():
            nahtud.add(d["prompt"]); koik.append(d)
with open("/mnt/varu/qwen38-et-data/processed/dpo4_korpus.jsonl", "w") as f:
    for d in koik:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")
print(f"dpo4 korpus: {len(koik)} paari")
PY

# 4. dpo4
echo "dpo4 algab $(date +%H:%M)"
.train-venv/bin/python "$S/14_train_dpo.py" --run dpo4 --resume-adapter "$A/ring7/final" \
  --data "$P/dpo4_korpus.jsonl" \
  --lr 1.5e-6 --beta 0.3 --ctx 1024 --grad-accum 8 > "$A/dpo4.log" 2>&1
grep -q "=== VALMIS" "$A/dpo4.log" || { echo "DPO4 EBAÕNNESTUS"; exit 1; }
echo "dpo4 treenitud $(date +%H:%M)"
hinda dpo4-bnb "$A/dpo4/final"

# 5. gguf v6 + sond
.train-venv/bin/python llama.cpp/convert_lora_to_gguf.py "$A/dpo4/final" \
  --base models/Qwen3.8-27B --outfile "$A/qwen38-et-v6-dpo4-lora.gguf" --outtype f16 >> "$A/dpo4.log" 2>&1
cat > /tmp/Modelfile-v6 <<'MF'
FROM qwen3.8:27b
ADAPTER /mnt/varu/qwen38-et-data/adapters/qwen38-et-v6-dpo4-lora.gguf
SYSTEM Sa oled abivalmis assistent. Vasta loomulikus ja korrektses eesti keeles.
PARAMETER temperature 0.4
PARAMETER top_p 0.9
PARAMETER top_k 20
MF
ollama create qwen3.8-et:27b-v6 -f /tmp/Modelfile-v6 >> "$A/dpo4.log" 2>&1
python3 "$S/15_fraasisond.py" --n 0 --mudel qwen3.8-et:27b-v6 \
  --valjund "$P/fraasisond-dpo4.jsonl" > "$A/fraasisond-dpo4.log" 2>&1
echo "fraasisond: $(grep TABAVUS "$A/fraasisond-dpo4.log")"
echo "RING7+DPO4 AHEL VALMIS — GPU VABA."
