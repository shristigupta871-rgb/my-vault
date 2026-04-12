---
title: My Vault
emoji: 🔐
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# MindLock Vault — OpenEnv Hackathon

Open RL environment with a full browser-based puzzle game.
Solve binary, XOR, pattern, Fibonacci, squares and octal puzzles.
Compete against a Q-learning AI agent that learns in real time.

## Play in browser
Visit your Space URL — the game loads automatically.

## API Endpoints
| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/` | Loads the game webpage |
| POST | `/reset` | Start new puzzle episode |
| POST | `/step` | Submit a guess `{"guess":"42"}` |
| GET | `/state` | Current environment state |
| GET | `/health` | Health check |

## Run locally
```bash
pip install -r requirements.txt
uvicorn inference:app --host 0.0.0.0 --port 7860
# open http://localhost:7860
```