#!/usr/bin/env python3
"""Liidab LoRA adapteri baasmudeli kaaludesse — üks iseseisev täismudel.

Kihthaaval otse safetensors-failides: iga baasi shard loetakse, sihtmoodulitele
lisatakse delta W += (B @ A) * (alpha/r), kirjutatakse uus shard. RAM-kulu on
ühe shardi jagu (~3 GB), tulemus on TÄPNE bf16 liitmine (mitte 4-bit dekvant).

Adapteri võtmed: base_model.model.model.language_model.layers.N.<moodul>.lora_{A,B}.weight
Baasi võtmed:                     model.language_model.layers.N.<moodul>.weight
"""
import argparse, json, os, shutil

import torch
from safetensors import safe_open
from safetensors.torch import save_file

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--baas", default="/mnt/varu/qwen38-et-data/models/Qwen3.8-27B")
    p.add_argument("--adapter",
                   default="/mnt/varu/qwen38-et-data/adapters/ring10/final")
    p.add_argument("--valjund",
                   default="/mnt/varu/qwen38-et-data/models/Qwen38-27B-ET-merged")
    a = p.parse_args()

    cfg = json.load(open(f"{a.adapter}/adapter_config.json"))
    skaala = cfg["lora_alpha"] / cfg["r"]
    print(f"skaala alpha/r = {skaala}")

    # adapteri deltad mällu (512 väikest tensorit, ~640 MB)
    ad = {}
    with safe_open(f"{a.adapter}/adapter_model.safetensors", "pt") as f:
        for k in f.keys():
            ad[k] = f.get_tensor(k)
    EES = "base_model.model."
    moodulid = {}   # baasi võtmenimi -> (A, B)
    for k in ad:
        if k.endswith(".lora_A.weight"):
            tyvi = k[len(EES):-len(".lora_A.weight")]
            moodulid[tyvi + ".weight"] = (ad[k], ad[EES + tyvi + ".lora_B.weight"])
    print(f"liidetavaid mooduleid: {len(moodulid)}")

    os.makedirs(a.valjund, exist_ok=True)
    indeks = json.load(open(f"{a.baas}/model.safetensors.index.json"))
    shardid = sorted(set(indeks["weight_map"].values()))
    liidetud = 0
    for si, shard in enumerate(shardid, 1):
        tensorid = {}
        with safe_open(f"{a.baas}/{shard}", "pt") as f:
            meta = f.metadata()
            for k in f.keys():
                t = f.get_tensor(k)
                if k in moodulid:
                    A, B = moodulid[k]
                    delta = (B.to(torch.float32) @ A.to(torch.float32)) * skaala
                    t = (t.to(torch.float32) + delta).to(t.dtype)
                    liidetud += 1
                tensorid[k] = t
        save_file(tensorid, f"{a.valjund}/{shard}", metadata=meta or {"format": "pt"})
        print(f"  shard {si}/{len(shardid)} kirjutatud", flush=True)

    if liidetud != len(moodulid):
        raise SystemExit(f"VIGA: liideti {liidetud}/{len(moodulid)} moodulit!")

    for f in os.listdir(a.baas):
        if not f.endswith(".safetensors"):
            shutil.copy(f"{a.baas}/{f}", f"{a.valjund}/{f}")
    print(f"VALMIS: {liidetud} moodulit liidetud → {a.valjund}")

if __name__ == "__main__":
    main()
