from fastapi.middleware.cors import CORSMiddleware


from fastapi.responses import FileResponse


import os
from fastapi import FastAPI
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # we can restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IBM_TOKEN = os.environ.get("IBM_TOKEN")

# 1️⃣ First create the service
service = QiskitRuntimeService(
    channel="ibm_quantum_platform",
    token=IBM_TOKEN,
    instance="crn:v1:bluemix:public:quantum-computing:us-east:a/ace2d7c4d936422892a7fd06ce1d3af4:c9832be1-5bc4-4c7a-a990-a024165d17ba::"
)

# 2️⃣ THEN create backend

# Get all operational real backends
real_backends = service.backends(simulator=False, operational=True)

# Choose backend with smallest queue
backend = min(real_backends, key=lambda b: b.status().pending_jobs)

sampler = Sampler(mode=backend)


@app.get("/flip")
async def flip():

    qc = QuantumCircuit(1)
    qc.h(0)
    qc.measure_all()

    transpiled_qc = transpile(qc, backend)

    job = sampler.run([transpiled_qc], shots=1)
    result = job.result()

    counts = result[0].data.meas.get_counts()
    bit = list(counts.keys())[0]

    return {
    "result": int(bit),
    "backend": backend.name,
    "mode": "hardware"
}


@app.get("/status")
async def status():
    return {
        "backend": backend.name,
        "pending_jobs": backend.status().pending_jobs
    }

@app.get("/")
async def root():
    return FileResponse("index.html")
