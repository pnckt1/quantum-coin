import os
import requests
from uuid import uuid4
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler

# =========================
# APP
# =========================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # pro stabilitu teď povolíme vše
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ENV
# =========================

IBM_TOKEN = os.environ.get("IBM_TOKEN")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")

INSTANCE = "crn:v1:bluemix:public:quantum-computing:us-east:a/ace2d7c4d936422892a7fd06ce1d3af4:c9832be1-5bc4-4c7a-a990-a024165d17ba::"

# =========================
# JOB STORAGE (in-memory)
# =========================

jobs = {}

# =========================
# IBM FACTORY
# =========================

def get_sampler():
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=IBM_TOKEN,
        instance=INSTANCE
    )

    backends = service.backends(simulator=False, operational=True)
    backend = min(backends, key=lambda b: b.status().pending_jobs)

    sampler = Sampler(mode=backend)
    return sampler, backend

# =========================
# TAROT DECK
# =========================

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

# =========================
# CREATE DRAW JOB
# =========================

@app.post("/draw")
async def create_draw(data: dict):

    question = data.get("question")

    sampler, backend = get_sampler()

    qc = QuantumCircuit(8)
    qc.h(range(8))
    qc.measure_all()

    transpiled_qc = transpile(qc, backend)

    ibm_job = sampler.run([transpiled_qc], shots=1)

    job_id = str(uuid4())

    jobs[job_id] = {
    "ibm_job_id": ibm_job.job_id(),
    "backend": backend.name,
    "question": question
}

    return {"job_id": job_id}

# =========================
# RESULT POLLING
# =========================

@app.get("/result/{job_id}")

async def get_result(job_id: str):

    if job_id not in jobs:
        return {"error": "Invalid job_id"}

    job_data = jobs[job_id]
    service = QiskitRuntimeService(
    channel="ibm_quantum_platform",
    token=IBM_TOKEN,
    instance=INSTANCE
)

ibm_job = service.job(job_data["ibm_job_id"])

    status = ibm_job.status()

    if status.name != "DONE":
        return {
            "status": "running",
            "ibm_status": status.name,
            "backend": job_data["backend"]
        }

    result = ibm_job.result()

data = result[0].data

if not hasattr(data, "meas"):
    return {"status": "error", "ibm_status": "INVALID_RESULT"}

counts = data.meas.get_counts()

if not counts:
    return {"status": "error", "ibm_status": "EMPTY_COUNTS"}

bitstring = list(counts.keys())[0]


    seed = int(bitstring, 2)

    shuffled = TAROT_DECK.copy()
    for i in range(len(shuffled) - 1, 0, -1):
        seed = (seed * 1664525 + 1013904223) & 0xffffffff
        j = seed % (i + 1)
        shuffled[i], shuffled[j] = shuffled[j], shuffled[i]

    cards = shuffled[:3]

return {
    "status": "done",
    "cards": [
        {
            "name": c,
            "image": c.replace(" ", "_") + ".jpg"
        }
        for c in cards
    ],
    "backend": job_data["backend"]
}


# =========================
# INTERPRET
# =========================

@app.post("/interpret")
async def interpret(data: dict):

    question = data.get("question")
    cards = data.get("cards")

    if not OPENROUTER_KEY:
        return {"interpretation": "Missing OPENROUTER_API_KEY"}

    prompt = f"""
Interpret this tarot spread in a psychologically grounded but symbolic way.
Keep it under 250 words.

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
            timeout=60
        )

        result = response.json()

        if "choices" not in result:
            return {"interpretation": str(result)}

        return {
            "interpretation": result["choices"][0]["message"]["content"]
        }

    except Exception as e:
        return {"interpretation": f"Server error: {str(e)}"}

# =========================
# ROOT
# =========================

@app.get("/")
async def root():
    return {"message": "Quantum Tarot Backend FINAL VERSION"}
