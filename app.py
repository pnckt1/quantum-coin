import os
import requests
from fastapi import FastAPI
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler

app = FastAPI()

# =========================
# ENV VARIABLES
# =========================

IBM_TOKEN = os.environ.get("IBM_TOKEN")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")

# =========================
# IBM QUANTUM SETUP
# =========================

service = QiskitRuntimeService(
    channel="ibm_quantum_platform",
    token=IBM_TOKEN,
    instance="crn:v1:bluemix:public:quantum-computing:us-east:a/ace2d7c4d936422892a7fd06ce1d3af4:c9832be1-5bc4-4c7a-a990-a024165d17ba::"
)

backend = service.backend("ibm_torino")
sampler = Sampler(mode=backend)

# =========================
# TAROT DECK (78 CARDS)
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

MINOR_ARCANA = [f"{rank} of {suit}" for suit in SUITS for rank in RANKS]

TAROT_DECK = MAJOR_ARCANA + MINOR_ARCANA

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
    available = TAROT_DECK.copy()

    for _ in range(3):
        idx = quantum_index(len(available))
        card = available.pop(idx)
        selected.append(card)

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

    prompt = f"""
Interpret this tarot spread in a psychologically grounded but symbolic way.

Question:
{question}

Cards:
{", ".join(cards)}

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
        "cards": cards,
        "interpretation": interpretation
    }

# =========================
# ROOT
# =========================

@app.get("/")
async def root():
    return {"message": "Quantum Tarot Backend Running"}
