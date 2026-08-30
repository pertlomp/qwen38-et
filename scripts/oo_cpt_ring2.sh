#!/bin/bash
# CPT-haru ring 2: moodulite taastus (olemasolu, tööriistad, JSON, rektsioon, liitsõnad)
set -u
cd /mnt/varu/qwen38-et-data || exit 1
S=/home/pert/CLAUDE/ARENDUSED/LLMTRAINING/qwen38-et/scripts
A=/mnt/varu/qwen38-et-data/adapters
P=/mnt/varu/qwen38-et-data/processed

python3 - <<'PY'
import json, random
random.seed(20260831)
P = "/mnt/varu/qwen38-et-data/processed"
def loe(t):
    try: return [json.loads(r) for r in open(t)]
    except FileNotFoundError: return []
siht = loe(f"{P}/ring6_moodulid.jsonl") + loe(f"{P}/ring7_moodulid.jsonl") \
     + loe(f"{P}/ring8_moodulid.jsonl") + loe(f"{P}/ring10_moodulid.jsonl") \
     + loe(f"{P}/ring12_moodulid.jsonl")
r4 = loe(f"{P}/sft_v1_ring4.jsonl")
siht += [d for d in r4 if d.get("kategooria") in ("tooriistad","json-struktuur")]
# fraaside hoidmine väikeses mahus, et ring1 võit ei kaoks
siht += random.sample(loe(f"{P}/fraas_astmevaheldus.jsonl"), 250)
siht += loe(f"{P}/sft_fraasiparandused_cpt2.jsonl")
replay = [d for d in r4 if d.get("kategooria","").startswith("replay")]
replay = random.sample(replay, round(len(siht)/0.85*0.15))
koik = siht + replay
random.shuffle(koik)
with open(f"{P}/sft_cptring2.jsonl","w") as f:
    for d in koik:
        f.write(json.dumps({"messages": d["messages"]}, ensure_ascii=False)+"\n")
print(f"CPT-RING2: {len(koik)} näidet")
PY

.train-venv/bin/python "$S/06_train_sft.py" --run cpt1-ring2 \
  --data "$P/sft_cptring2.jsonl" --resume-adapter "$A/cpt1-ring1/final" \
  --lr 2e-5 --save-steps 200 > "$A/cpt1-ring2.log" 2>&1
grep -q "=== VALMIS" "$A/cpt1-ring2.log" || { echo EBAÕNNESTUS; exit 1; }
echo "treenitud $(date +%H:%M)"
sleep 10
.train-venv/bin/python "$S/07b_eval_local.py" --run cpt1-ring2-bnb --adapter "$A/cpt1-ring2/final" > "$A/eval-cpt1-ring2.log" 2>&1
grep -q "VALMIS →" "$A/eval-cpt1-ring2.log" && python3 "$S/08_score.py" --run cpt1-ring2-bnb > "$A/cpt1-ring2-skoor.txt" 2>&1
echo "EVAL: $(grep ÜLDSKOOR "$A/cpt1-ring2-skoor.txt" | head -1)"

.train-venv/bin/python llama.cpp/convert_lora_to_gguf.py "$A/cpt1-ring2/final" \
  --base models/Qwen3.8-27B --outfile "$A/qwen38-et-cptr2-lora.gguf" --outtype f16 >> "$A/cpt1-ring2.log" 2>&1
cat > /tmp/Modelfile-cptr2 <<'MF'
FROM qwen3.8:27b
ADAPTER /mnt/varu/qwen38-et-data/adapters/qwen38-et-cptr2-lora.gguf
SYSTEM Sa oled abivalmis assistent. Vasta loomulikus ja korrektses eesti keeles.
PARAMETER temperature 0.4
PARAMETER top_p 0.9
PARAMETER top_k 20
PARAMETER repeat_penalty 1.15
MF
ollama create qwen3.8-et:27b-cpt3 -f /tmp/Modelfile-cptr2 >> "$A/cpt1-ring2.log" 2>&1
python3 "$S/15_fraasisond.py" --n 0 --mudel qwen3.8-et:27b-cpt3 \
  --valjund "$P/fraasisond-cpt3.jsonl" > "$A/fraasisond-cpt3.log" 2>&1
echo "SOND: $(grep TABAVUS "$A/fraasisond-cpt3.log")"
echo "CPT-RING2 VALMIS $(date +%H:%M)"
