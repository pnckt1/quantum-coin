import os
import requests
from fastapi import FastAPI
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler

app = FastAPI()

# =========================
# ENV
# =========================

IBM_TOKEN = os.environ.get("IBM_TOKEN")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")

# =========================
# IBM SETUP
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
# TAROT DECK
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
# CARD IMAGE MAPPING
# =========================

def card_filename(card_name):

    major_map = {
        "The Fool": "m00.jpg",
        "The Magician": "m01.jpg",
        "The High Priestess": "m02.jpg",
        "The Empress": "m03.jpg",
        "The Emperor": "m04.jpg",
        "The Hierophant": "m05.jpg",
        "The Lovers": "m06.jpg",
        "The Chariot": "m07.jpg",
        "Strength": "m08.jpg",
        "The Hermit": "m09.jpg",
        "Wheel of Fortune": "m10.jpg",
        "Justice": "m11.jpg",
        "The Hanged Man": "m12.jpg",
        "Death": "m13.jpg",
        "Temperance": "m14.jpg",
        "The Devil": "m15.jpg",
        "The Tower": "m16.jpg",
        "The Star": "m17.jpg",
        "The Moon": "m18.jpg",
        "The Sun": "m19.jpg",
        "Judgement": "m20.jpg",
        "The World": "m21.jpg"
    }

    if card_name in major_map:
        return major_map[card_name]

    rank, _, suit = card_name.partition(" of ")

    suit_letter = {
        "Wands": "w",
        "Cups": "c",
        "Swords": "s",
        "Pentacles": "p"
    }[suit]

    rank_map = {
        "Ace": "01",
        "2": "02", "3": "03", "4": "04", "5": "05",
        "6": "06", "7": "07", "8": "08", "9": "09",
        "10": "10",
        "Page": "11", "Knight": "12",
        "Queen": "13", "King": "14"
    }

    return f"{suit_letter}{rank_map[rank]}.jpg"

# =========================
# QUANTUM DRAW (ONE JOB)
# =========================

def quantum_draw_three(deck):

    qc = QuantumCircuit(20)
    qc.h(range(20))
    qc.measure_all()

    transpiled_qc = transpile(qc, backend)

    job = sampler.run([transpiled_qc], shots=1)
    result = job.result()

    counts = result[0].data.meas.get_counts()
    bitstring = list(counts.keys())[0]

    seed = int(bitstring, 2)

    shuffled = deck.copy()

    # Deterministic Fisher-Yates shuffle
    for i in range(len(shuffled) - 1, 0, -1):
        seed = (seed * 1664525 + 1013904223) & 0xffffffff
        j = seed % (i + 1)
        shuffled[i], shuffled[j] = shuffled[j], shuffled[i]

    return shuffled[:3]

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
# DRAW ENDPOINT
# =========================

@app.get("/draw")
async def draw_cards(question: str):

    selected_cards = quantum_draw_three(TAROT_DECK)

    result_cards = [
        {
            "name": card,
            "image": card_filename(card)
        }
        for card in selected_cards
    ]

    return {
        "question": question,
        "cards": result_cards,
        "backend": backend.name
    }

# =========================
# INTERPRET
# =========================

@app.post("/interpret")
async def interpret(data: dict):

    question = data.get("question")
    cards = data.get("cards")

    if not OPENROUTER_KEY:
        return {"interpretation": "OPENROUTER_API_KEY not set on server."}

    prompt = f"""
Interpret this tarot spread in a psychologically grounded but symbolic way.

Question:
{question}

Cards:
{", ".join(cards)}
"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=90
        )

        result = response.json()

        if "choices" not in result:
            return {"interpretation": f"OpenRouter error: {result}"}

        return {
            "interpretation": result["choices"][0]["message"]["content"]
        }

    except Exception as e:
        return {"interpretation": f"Server exception: {str(e)}"}

# =========================
# ROOT
# =========================

@app.get("/")
async def root():
    return {"message": "Quantum Tarot Backend Running"}
