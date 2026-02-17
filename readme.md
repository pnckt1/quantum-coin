Quantum Coin – Hardware-Backed Randomness as a PWA
1. Problem

Most “random” web apps rely on pseudorandom number generators (Math.random() or server-side PRNGs).
I wanted to build a minimal web application where the outcome is decided by a real quantum measurement on physical hardware.

The goal was intentionally simple:

A single button that flips a coin — but the result must come from an actual superconducting qubit.

2. Concept

Each button press:

Creates a one-qubit quantum circuit.

Applies a Hadamard gate (puts qubit into superposition).

Measures the qubit on a real IBM Quantum backend.

Returns the classical result (0 or 1).

Displays “Heads” or “Tails” in the UI.

One shot. One collapse. One real quantum event.

3. Architecture

The system is a distributed architecture:

Client (Frontend)

HTML/CSS/JavaScript

Hosted on Netlify

Installable PWA

Fetches /flip from backend

Backend

Python 3

FastAPI

Hosted on Render

Uses qiskit-ibm-runtime Sampler primitive

Connects to IBM Quantum hardware

Returns JSON response

Quantum Layer

IBM Quantum Platform

Real backend (e.g. ibm_torino)

Transpiled circuit executed on hardware

Single-shot measurement

Architecture Flow

iPhone PWA
→ Netlify (static frontend)
→ Render (FastAPI backend)
→ IBM Quantum Runtime
→ Physical QPU measurement
→ JSON result
→ UI collapse animation

4. Deployment
Backend

Version controlled via Git

Hosted on GitHub

Automatically deployed to Render

IBM API token stored as environment variable

CORS enabled for cross-origin requests

Frontend

Static files deployed to Netlify

Connected to backend via HTTPS

Includes:

manifest.json

sw.js

App icons (192px / 512px)

PWA

Installable on iPhone via Safari

Runs standalone

Uses service worker

Full-screen app-like experience

5. Technical Challenges Solved

Migrated to new Qiskit Sampler API (V2)

Resolved backend compatibility issues

Implemented hardware transpilation

Fixed cross-origin (CORS) errors

Secured API credentials (removed hardcoded token)

Managed cloud deployment and CI pipeline

Optimized to single-shot measurement

6. Lessons Learned

Real-world deployment complexity exceeds local development.

CORS configuration is essential for multi-host architecture.

Modern quantum APIs evolve quickly — adapting to SDK changes is necessary.

Even “simple” apps become distributed systems when deployed properly.

Clean separation of frontend and backend improves maintainability.

Minimal UI with strong identity creates a memorable product.

7. Why This Project Matters

This project demonstrates:

Cloud deployment skills

Secure API integration

Distributed architecture design

CI/CD workflow

Frontend + backend integration

Real hardware integration

Product-level polish (PWA + design identity)

It intentionally over-engineers a trivial problem (coin flip) to demonstrate full-stack capability and infrastructure understanding.

8. Technologies Used

Python

FastAPI

Uvicorn

Qiskit

qiskit-ibm-runtime

Git

GitHub

Render

Netlify

PWA (manifest + service worker)

HTML / CSS / JavaScript

9. Summary

Quantum Coin is a publicly accessible, installable web application that performs a real quantum measurement on IBM superconducting hardware and presents the result through a minimalist neon-inspired interface.

It turns a trivial action into a fully deployed distributed system.

If you publish this with screenshots and the live URL, this is absolutely portfolio-level material.

Now let me ask you something important:

Do you want this documentation written in a more formal corporate tone,
or slightly more personality-driven but still professional?