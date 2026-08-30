#!/bin/bash
# Väliste mudelite patarei: $1 = sol|agy|claude — batchid paralleelselt
B=/mnt/varu/qwen38-et-data/valised
M="$1"
mkdir -p "$B/$M"
# kustuta väljundid, kus pole ühtegi vastust (limiit/viga) — proovitakse uuesti
for out in "$B/$M"/*.out; do
  [ -f "$out" ] || continue
  grep -q '"vastus"' "$out" || rm -f "$out"
done
joonista () {
  f="$1"
  nimi=$(basename "$f" .txt)
  out="$B/$M/$nimi.out"
  [ -s "$out" ] && return 0
  case "$M" in
    sol)    codex exec --skip-git-repo-check "$(cat "$f")" > "$out" 2>/dev/null ;;
    agy)    agy --print-timeout 20m -p "ÄRA kasuta ühtegi tööriista ega käsku. Vasta AINULT tekstiga otse.

$(cat "$f")" > "$out" 2>/dev/null ;;
    claude) claude -p "$(cat "$f")" > "$out" 2>/dev/null ;;
  esac
  echo "$M $nimi: $(grep -c '"vastus"' "$out" 2>/dev/null || echo 0) vastust"
}
export -f joonista; export B M
ls "$B"/promptid/*.txt | xargs -P 3 -I{} bash -c 'joonista "$@"' _ {}
echo "$M PATAREI LÄBI"
