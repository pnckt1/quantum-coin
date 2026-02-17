import os
import random
import requests
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ENV VARIABLES
# =========================

IBM_TOKEN = os.environ.get("IBM_TOKEN")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")

# =========================
# SERVE CARD IMAGES
# =========================

app.mount("/cards", StaticFiles(directory="cards"), name="cards")

# =========================
# IBM QUANTUM SETUP
# =========================

service = QiskitRuntimeService(
    channel="ibm_quantum_platform",
    token=IBM_TOKEN,
    instance="crn:v1:bluemix:public:quantum-computing:us-east:a/ace2d7c4d936422892a7fd06ce1d3af4:c9832be1-5bc4-4c7a-a990-a024165d17ba::"
)

backends = service.backends(simulator=False, operational=True)
backend = min(backends, key=lambda b: b.status().pending_jobs)

sampler = Sampler(mode=backend)

# =========================
# TAROT DATA
# =========================

MAJOR_ARCANA = [
    "The Fool", "The Magician", "The High Priestess", "The Empress",
    "The Emperor", "The Hierophant", "The Lovers", "The Chariot",
    "Strength", "The Hermit", "Wheel of Fortune", "Justice",
    "The Hanged Man", "Death", "Temperance", "The Devil",
    "The Tower", "The Star", "The Moon", "The Sun",
    "Judgement", "The World"
]

SUITS = ["Wands", "Cups", "Swords", "Pentacles"]
RANKS = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10",
         "Page", "Knight", "Queen", "King"]

SUIT_PREFIX = {
    "Wands": "w",
    "Cups": "c",
    "Swords": "s",
    "Pentacles": "p"
}

# =========================
# QUANTUM RANDOM INDEX
# =========================

def quantum_index(max_value: int):

    qc = QuantumCircuit(1)
    qc.h(0)
    qc.measure_all()

    transpiled_qc = transpile(qc, backend)

    job = sampler.run([transpiled_qc], shots=8)
    result = job.result()

    counts = result[0].data.meas.get_counts()

    bitstring = list(counts.keys())[0]
    number = int(bitstring, 2)

    return number % max_value

# =========================
# STATUS
# =========================

@app.get("/status")
async def status():
    return {
        "backend": backend.name,
        "pending_jobs": backend.status().pending_jobs
    }

# =========================
# DRAW 3 CARDS
# =========================

@app.get("/draw")
async def draw_cards(question: str):

    selected = []
    available_major = list(range(22))
    available_minor = list(range(1, 15))

    for _ in range(3):

        if random.random() < 0.3:
            idx = quantum_index(len(available_major))
            card_number = available_major.pop(idx)
            filename = f"m{card_number:02}.jpg"
            card_name = MAJOR_ARCANA[card_number]
        else:
            suit = random.choice(SUITS)
            idx = quantum_index(len(available_minor))
            number = available_minor.pop(idx)
            filename = f"{SUIT_PREFIX[suit]}{number:02}.jpg"
            rank = RANKS[number - 1]
            card_name = f"{rank} of {suit}"

        selected.append({
            "name": card_name,
            "image": filename
        })

    return {
        "question": question,
        "cards": selected,
        "backend": backend.name
    }

# =========================
# INTERPRET SPREAD
# =========================

@app.post("/interpret")
async def interpret(data: dict):

    question = data.get("question")
    cards = data.get("cards")

    card_names = [card["name"] for card in cards]

    prompt = f"""
Interpret this tarot spread in a psychologically grounded but symbolic way.

Question:
{question}

Cards:
{", ".join(card_names)}

Provide a cohesive interpretation.
"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "HTTP-Referer": "https://quantum-coin-1k7w.onrender.com",
            "X-Title": "Quantum Tarot"
        },
        json={
            "model": "openai/gpt-4o-mini",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    )

    result = response.json()

    interpretation = result["choices"][0]["message"]["content"]

    return {
        "interpretation": interpretation
    }

# =========================
# ROOT
# =========================

@app.get("/")
async def root():
    return {"message": "Quantum Tarot Backend Running"}
