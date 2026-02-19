import os
import requests
from uuid import uuid4
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IBM_TOKEN = os.environ.get("IBM_TOKEN")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")

INSTANCE = "crn:v1:bluemix:public:quantum-computing:us-east:a/ace2d7c4d936422892a7fd06ce1d3af4:c9832be1-5bc4-4c7a-a990-a024165d17ba::"

jobs = {}

# IBM init
service = QiskitRuntimeService(
    channel="ibm_quantum_platform",
    token=IBM_TOKEN,
    instance=INSTANCE
)

backends = service.backends(simulator=False, operational=True)
backend = min(backends, key=lambda b: b.status().pending_jobs)
sampler = Sampler(mode=backend)

print("IBM backend selected:", backend.name)

# Tarot deck
MAJOR_ARCANA = [
    "The Fool","The Magician","The High Priestess","The Empress",
    "The Emperor","The Hierophant","The Lovers","The Chariot",
    "Strength","The Hermit","Wheel of Fortune","Justice",
    "The Hanged Man","Death","Temperance","The Devil",
    "The Tower","The Star","The Moon","The Sun",
    "Judgement","The World"
]

SUITS = ["Wands","Cups","Swords","Pentacles"]
RANKS = ["Ace","2","3","4","5","6","7","8","9","10",
         "Page","Knight","Queen","King"]

MINOR_ARCANA = [f"{r} of {s}" for s in SUITS for r in RANKS]
TAROT_DECK = MAJOR_ARCANA + MINOR_ARCANA

def card_filename(card_name):
    major_map = {f"The {name}": f"m{str(i).zfill(2)}.jpg"
                 for i, name in enumerate([
                     "Fool","Magician","High Priestess","Empress","Emperor",
                     "Hierophant","Lovers","Chariot","Strength","Hermit",
                     "Wheel of Fortune","Justice","Hanged Man","Death",
                     "Temperance","Devil","Tower","Star","Moon","Sun",
                     "Judgement","World"
                 ])}

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
        "Ace": "01","2": "02","3": "03","4": "04","5": "05",
        "6": "06","7": "07","8": "08","9": "09","10": "10",
        "Page": "11","Knight": "12","Queen": "13","King": "14"
    }

    return f"{suit_letter}{rank_map[rank]}.jpg"


@app.post("/draw")
async def create_draw(data: dict):
    qc = QuantumCircuit(8)
    qc.h(range(8))
    qc.measure_all()

    transpiled_qc = transpile(qc, backend)
    ibm_job = sampler.run([transpiled_qc], shots=1)

    job_id = str(uuid4())
    jobs[job_id] = {"ibm_job_id": ibm_job.job_id()}

    return {"job_id": job_id}


@app.get("/result/{job_id}")
async def get_result(job_id: str):

    if job_id not in jobs:
        return {"status": "error", "message": "Invalid job_id"}

    ibm_job = service.job(jobs[job_id]["ibm_job_id"])
    status = ibm_job.status()

    status_name = str(status)

    if status_name in ["QUEUED", "RUNNING"]:
        return {
            "status": "running",
            "ibm_status": status_name,
            "backend": backend.name
        }

    if status_name in ["ERROR", "CANCELLED"]:
        return {
            "status": "error",
            "ibm_status": status_name
        }

    result = ibm_job.result()
    counts = result[0].data.meas.get_counts()
    bitstring = list(counts.keys())[0]
    seed = int(bitstring, 2)

    shuffled = TAROT_DECK.copy()

    for i in range(len(shuffled) - 1, 0, -1):
        seed = (seed * 1664525 + 1013904223) & 0xffffffff
        j = seed % (i + 1)
        shuffled[i], shuffled[j] = shuffled[j], shuffled[i]

    selected = shuffled[:3]

    return {
        "status": "done",
        "cards": [
            {
                "name": c,
                "image": card_filename(c)
            }
            for c in selected
        ],
        "backend": backend.name
    }


@app.post("/interpret")
async def interpret(data: dict):

    question = data.get("question")
    cards = data.get("cards")

    if not OPENROUTER_KEY:
        return {"interpretation": "Missing OPENROUTER_API_KEY"}

    prompt = f"""
Answer in the same language as the question.
Maximum 400 words.

Question:
{question}

Cards:
{", ".join(cards)}
"""

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
        timeout=60
    )

    result = response.json()

    if "choices" not in result:
        return {"interpretation": str(result)}

    return {
        "interpretation": result["choices"][0]["message"]["content"]
    }


@app.get("/")
async def root():
    return {"message": "Quantum Tarot Backend FINAL"}
