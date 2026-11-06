# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

Not a git repo, and there is no build system, package manifest, linter, or test suite. It holds independent mini-games:

- `index.html` — "토끼 당근 피하기" (rabbit/carrot dodge), a single-file mobile-first HTML5 canvas game. Expects sibling assets `poster.png`, `music.mp3`, `ending.mp4`, which are **not in the repo**; the poster has an `error` fallback to a text title, so missing assets are tolerated.
- `intro.html` — a 10-second 1280x720 canvas intro animation for the same game (standalone).
- `shooter1945/` — "1945 SKY STRIKER", a vertical shooter implemented **twice**: Pygame (desktop) and a standalone browser port.

Open the HTML files directly in a browser (no server needed).

## shooter1945

```
cd shooter1945
pip install pygame
python main.py          # run the Pygame version
```

The browser port is `shooter1945/web/index.html` (one self-contained file with inline JS, no assets).

### Two parallel implementations
The Pygame code (`main.py` + modules) and `web/index.html` are separate ports of the same game, with the same constants (480x720, 60 FPS, `MAX_POWER=4`, `MAX_BOMBS=5`, `MAX_LIVES=5`). There is no shared code, so a gameplay or balance change (enemy stats, drops, stage waves, boss patterns) must be made in both. The web version stores the hi-score in `localStorage` (`shooter1945_hi`); the Pygame version uses `highscore.txt`.

### Pygame architecture
- `main.py` — `Game` class owns all state and the main loop. State machine: `title` → `play` → `gameover`/`victory`. All combat logic (collision, damage, drops, bombs, item effects, stage progression) lives here, not in the entity classes. Everything renders to an offscreen `canvas`, which is blitted with screen shake at the end of each frame.
- `stages.py` — `build(n)` procedurally generates a stage's wave timeline `(seconds, enemy_kind, x)` from a **seeded RNG** (`100 + n`), so stages are deterministic. Adds `boss_time`. Timing is in seconds and compared against the tick counter `t * FPS`.
- `enemies.py` — `TYPES` table (hp, radius, score, colors) plus `Enemy` and `Boss` (3-phase pattern). Enemy HP scales with stage. Kind names (`small`, `zigzag`, `swoop`, `medium`) are also keyed in `Game.drop()` drop-chance table, so a new enemy type needs entries in both.
- `bullets.py` — `Bullet` plus the `aim`/`fan`/`ring` pattern helpers used by enemies and bosses.
- `player.py`, `items.py`, `effects.py` (background, particles, popups, `draw_text`, `draw_plane`), `audio.py` — sounds are synthesized in code.
- No external image or sound assets: all graphics are drawn procedurally and audio is synthesized.
- UI text and comments are in Korean; keep that style.
