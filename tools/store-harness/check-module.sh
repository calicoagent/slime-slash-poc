#!/bin/bash
# node --check on the game module: CDN imports stubbed (this check only — the
# boot mode of harness.js loads the REAL imports in Chromium).
f="${1:-$(dirname "$0")/../../index.html}"
out="${TMPDIR:-/tmp}/slimeslash-module.mjs"
awk '/<script type="module">/{f=1;next} /<\/script>/{f=0} f' "$f" \
 | sed -e "s#^import { joinRoom, selfId } from 'https://cdn.jsdelivr.net/npm/trystero@0.21.6/nostr/+esm';#const selfId='stub'; const joinRoom=()=>{throw new Error('stub')};#" \
       -e "s#^import { createStore } from 'https://cdn.jsdelivr.net/npm/zustand@5.1.0/vanilla/+esm';#const createStore=f=>{let s;const g=()=>s,set=p=>{s=Object.assign({},s,typeof p==='function'?p(s):p)};s=f(set,g);return{getState:g,setState:set,subscribe:()=>()=>{}};};#" > "$out"
if grep -q "^import " "$out"; then echo "unstubbed import left:"; grep "^import " "$out"; exit 1; fi
node --check "$out" && echo "node --check OK ($(wc -l < "$out" | tr -d ' ') lines, imports stubbed)"
