# Slime Slash! — Multiplayer POC

Your mouse / finger **is** the sword. Shared real-time world via **Trystero** (Nostr strategy, WebRTC P2P, no server).

- ONE single world for everyone (fixed Trystero room id under the hood, no rooms/codes in the UI). Host (lowest peer id) owns slime spawning/HP; host migrates automatically if they leave.
- Slash cute slimes → coins + XP → level up → unlock weapons (Dagger, Sword, Katana, Greatsword, Warhammer) in the rack, buy upgrades at the FORGE (Damage / Reach / Swift Hands).
- Tap / click / Space = spin slash. Keys 1–5 switch weapons.
- Solo works too: with no peers you are the host of your own world.

## Run
Open `index.html` over HTTPS (or localhost) — WebRTC needs a secure context. No build step; Trystero loads from CDN.
