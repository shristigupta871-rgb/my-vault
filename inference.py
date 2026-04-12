from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from uuid import uuid4
import random
import os

app = FastAPI(title="MindLock Vault", version="3.0.0")

# ── Puzzle Generator ───────────────────────────────────────────

def generate_puzzle(difficulty: int = 1):
    puzzle_type = random.choice(["binary", "xor", "pattern", "fibonacci", "squares", "octal"])

    if puzzle_type == "binary":
        bits = 4 + difficulty * 2
        n = random.randint(2 ** (bits - 1), 2 ** bits - 1)
        return {
            "type": "BINARY",
            "question": f"Convert binary to decimal:\n{format(n, f'0{bits}b')}",
            "answer": str(n),
            "hint": "Split into groups of 4 bits and compute each group separately",
            "google_hint": f"binary {format(n, f'0{bits}b')} to decimal"
        }

    elif puzzle_type == "xor":
        a = random.randint(1, 15 * difficulty)
        b = random.randint(1, 15 * difficulty)
        return {
            "type": "XOR",
            "question": f"What is  {a}  XOR  {b}  ?",
            "answer": str(a ^ b),
            "hint": f"Binary: {format(a, '08b')}  XOR  {format(b, '08b')}",
            "google_hint": f"XOR bitwise operation {a} {b} decimal"
        }

    elif puzzle_type == "pattern":
        step = random.randint(2, 5 + difficulty)
        start = random.randint(1, 10)
        length = 4 + difficulty
        seq = [start + i * step for i in range(length)]
        return {
            "type": "PATTERN",
            "question": f"What comes next?\n{' ,  '.join(map(str, seq))} ,  ?",
            "answer": str(start + length * step),
            "hint": "The difference between each number is constant",
            "google_hint": f"arithmetic sequence {seq[0]} {seq[1]} {seq[2]} next term"
        }

    elif puzzle_type == "fibonacci":
        fibs = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]
        st = random.randint(0, 5)
        c = 4 + difficulty
        shown = fibs[st:st + c]
        return {
            "type": "FIBONACCI",
            "question": f"What comes next?\n{' ,  '.join(map(str, shown))} ,  ?",
            "answer": str(fibs[st + c]),
            "hint": "Each number equals the sum of the two numbers before it",
            "google_hint": "fibonacci sequence next number calculator"
        }

    elif puzzle_type == "squares":
        start = random.randint(1, 3 + difficulty)
        count = 4 + difficulty
        seq = [(start + i) ** 2 for i in range(count)]
        return {
            "type": "SQUARES",
            "question": f"What comes next?\n{' ,  '.join(map(str, seq))} ,  ?",
            "answer": str((start + count) ** 2),
            "hint": "These are perfect squares: 1², 2², 3², 4²...",
            "google_hint": f"perfect squares sequence {seq[0]} {seq[1]} next term"
        }

    else:
        n = random.randint(8, 64 * difficulty)
        return {
            "type": "OCTAL",
            "question": f"Convert octal to decimal:\n{oct(n)[2:]}",
            "answer": str(n),
            "hint": "Multiply each digit by 8 raised to its position from the right (starting at 0)",
            "google_hint": f"octal {oct(n)[2:]} to decimal converter"
        }


# ── Environment State ──────────────────────────────────────────

class EnvState:
    def __init__(self, difficulty: int = 1):
        self.episode_id = str(uuid4())
        self.step_count = 0
        self.puzzle = generate_puzzle(difficulty)
        self.done = False
        self.attempts = 0
        self.difficulty = difficulty


env = EnvState()


# ── Pydantic Models ────────────────────────────────────────────

class StepAction(BaseModel):
    guess: str
    difficulty: int = 1


# ── OpenEnv API Endpoints ──────────────────────────────────────

@app.post("/reset")
async def reset(difficulty: int = 1):
    global env
    env = EnvState(difficulty)
    return {
        "observation": {
            "message": f"[{env.puzzle['type']} | Difficulty {difficulty}]\n{env.puzzle['question']}",
            "puzzle_type": env.puzzle["type"],
            "question": env.puzzle["question"],
            "hint": "",
            "done": False,
            "reward": 0.0
        },
        "episode_id": env.episode_id,
        "step_count": 0,
        "info": "New episode started. POST /step with your guess."
    }


@app.post("/step")
async def step(action: StepAction):
    global env
    env.step_count += 1
    env.attempts += 1

    correct = action.guess.strip() == env.puzzle["answer"]
    reward = round(max(0.0, 1.0 - (env.attempts - 1) * 0.1), 2) if correct else 0.0
    env.done = correct

    hint = ""
    if not correct and env.attempts >= 2:
        hint = env.puzzle.get("hint", "")

    return {
        "observation": {
            "message": "Vault unlocked! Correct answer." if correct else f"Wrong answer. Attempt {env.attempts}.",
            "puzzle_type": env.puzzle["type"],
            "question": env.puzzle["question"],
            "hint": hint,
            "done": correct,
            "reward": reward
        },
        "reward": reward,
        "done": correct,
        "episode_id": env.episode_id,
        "step_count": env.step_count,
        "correct_answer": env.puzzle["answer"] if correct else "keep trying"
    }


@app.get("/state")
async def state():
    return {
        "episode_id": env.episode_id,
        "step_count": env.step_count,
        "puzzle_type": env.puzzle["type"],
        "attempts": env.attempts,
        "done": env.done,
        "difficulty": env.difficulty
    }


@app.get("/health")
async def health():
    return {"status": "ok", "env": "mindlock_vault", "version": "3.0.0"}


# ── Serve Web UI ───────────────────────────────────────────────

web_ui_path = os.path.join(os.path.dirname(__file__), "web_ui")

if os.path.exists(web_ui_path):
    app.mount("/static", StaticFiles(directory=web_ui_path), name="static")


@app.get("/")
async def root():
    index = os.path.join(web_ui_path, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"name": "MindLock Vault", "version": "3.0.0", "ui": "web_ui/index.html not found"}