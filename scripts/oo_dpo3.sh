#!/bin/bash
# error-DPO (dpo3): ring5 + on-policy fraasivead → treening → eval
cd /mnt/varu/qwen38-et-data || exit 1
S=/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/scripts
A=/mnt/varu/qwen38-et-data/adapters
P=/mnt/varu/qwen38-et-data/processed

# liida sondi 70 + korje paarid, dedup prompti järgi
python3 - <<'PY'
import json
nahtud, koik = set(), []
for tee in ("/mnt/varu/qwen38-et-data/processed/dpo_fraasivead_r5.jsonl",
            "/mnt/varu/qwen38-et-data/processed/dpo_onpolicy_r5.jsonl"):
    for r in open(tee):
        d = json.loads(r)
        if d["prompt"] not in nahtud and d["chosen"].lower() != d["rejected"].lower():
            nahtud.add(d["prompt"]); koik.append(d)
with open("/mnt/varu/qwen38-et-data/processed/dpo3_korpus.jsonl", "w") as f:
    for d in koik:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")
print(f"dpo3 korpus: {len(koik)} paari")
PY

echo "dpo3 treening algab $(date +%H:%M)"
.train-venv/bin/python "$S/14_train_dpo.py" --run dpo3 \
  --resume-adapter "$A/ring5/final" \
  --data "$P/dpo3_korpus.jsonl" \
  --lr 1.5e-6 --beta 0.3 --ctx 1024 --grad-accum 8 > "$A/dpo3.log" 2>&1
grep -q "=== VALMIS" "$A/dpo3.log" || { echo "DPO3 EBAÕNNESTUS"; exit 1; }
echo "dpo3 treenitud $(date +%H:%M)"

sleep 15
.train-venv/bin/python "$S/07b_eval_local.py" --run dpo3-bnb --adapter "$A/dpo3/final" > "$A/eval-dpo3-bnb.log" 2>&1
if grep -q "VALMIS →" "$A/eval-dpo3-bnb.log"; then
  python3 "$S/08_score.py" --run dpo3-bnb > "$A/dpo3-bnb-skoor.txt" 2>&1
  echo "dpo3 HINNATUD: $(grep ÜLDSKOOR "$A/dpo3-bnb-skoor.txt" | head -1)"
else
  echo "dpo3 EVAL EBAÕNNESTUS"; exit 1
fi
echo "DPO3 AHEL VALMIS — GPU VABA."
