#!/usr/bin/env python3
"""HumanEval pass@1 Ollama mudelile — kas parim-eesti on ka parim koodis?

Standardne 164 Pythoni ülesannet testidega. Genereeritud kood jookseb
subprocess'is 10 s timeoutiga. Deterministlik: temperatuur 0, sama järjekord.
"""
import argparse, gzip, json, re, subprocess, sys, tempfile, urllib.request

ANDMED = "/mnt/varu/qwen38-et-data/raw/HumanEval.jsonl.gz"

def kysi(mudel, prompt, think, n=900):
    d = json.dumps({"model": mudel, "think": think, "stream": False,
                    "messages": [{"role": "user", "content": prompt}],
                    "options": {"temperature": 0.0, "num_predict": n}}).encode()
    req = urllib.request.Request("http://localhost:11434/api/chat", data=d,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())["message"]["content"]

def eralda_kood(vastus, prompt):
    m = re.findall(r"```(?:python)?\n(.*?)```", vastus, re.S)
    kood = m[0] if m else vastus
    # kui mudel andis ainult keha, liida signatuuriga
    if "def " not in kood:
        return prompt + kood
    return kood

def jooksuta(kood, test, entry):
    prog = f"{kood}\n\n{test}\n\ncheck({entry})\n"
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(prog)
        tee = f.name
    try:
        r = subprocess.run([sys.executable, tee], capture_output=True, timeout=10)
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mudel", required=True)
    p.add_argument("--think", action="store_true")
    p.add_argument("--n", type=int, default=164)
    a = p.parse_args()

    read = [json.loads(r) for r in gzip.open(ANDMED)][:a.n]
    print(f"HumanEval: {len(read)} ülesannet, {a.mudel} (think={a.think})", flush=True)
    labis = 0
    for i, d in enumerate(read, 1):
        prompt = ("Complete the following Python function. Return ONLY the "
                  "complete function in a ```python code block.\n\n" + d["prompt"])
        try:
            v = kysi(a.mudel, prompt, a.think)
        except Exception as e:
            print(f"  VIGA {d['task_id']}: {e}", flush=True)
            continue
        kood = eralda_kood(v, d["prompt"])
        if jooksuta(kood, d["test"], d["entry_point"]):
            labis += 1
        if i % 20 == 0:
            print(f"  {i}/{len(read)}  pass@1 {labis/i*100:.1f}%", flush=True)
    print(f"\nPASS@1 ({a.mudel}, think={a.think}): {labis}/{len(read)} "
          f"= {labis/len(read)*100:.1f}%")

if __name__ == "__main__":
    main()
