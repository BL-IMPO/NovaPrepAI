# NovaPrepAI

This repository contains the source code for my university graduation project (scheduled for defense in May 2026). It is a full-stack educational platform designed to simulate the National Testing Certificate (ОРТ).

It took about 3000 lines of code to get everything running exactly how I wanted. The main goal was to build a system that generates test questions dynamically using LLMs, rather than pulling from a static database, and to stream that content to the user in real-time.

## Architecture Decisions

I intentionally avoided heavy frontend frameworks like React or Vue. The client is built with Vanilla JavaScript and Bootstrap 5. It manages state via `sessionStorage` and parses NDJSON streams natively. It is fast, lightweight, and doesn't overcomplicate the DOM for a simple testing interface.

The backend is a hybrid microservice setup:
* **Django (Port 8000):** Acts as the source of truth. It handles PostgreSQL, JWT authentication, and the core business logic. It's stable and synchronous.
* **FastAPI (Port 8001):** Acts as the asynchronous worker. It handles the OpenAI API calls. My background in data annotation and model training came in handy here—the prompts are heavily engineered with strict Pydantic schemas so the LLM outputs predictable JSON arrays every single time. FastAPI streams this data back to the client so users can start reading question 1 while question 10 is still generating.

Nginx sits in front as a reverse proxy to route the traffic to the correct containers.

## Core Features
* **Real-time Streaming:** Questions appear instantly without loading screens using chunked transfer encoding.
* **AI Tutor Sidebar:** An interactive chat that reads the context of the current question. It is strictly prompted to act as a guide, not an answer key.
* **State Recovery:** If you accidentally close the tab, your timer and answers are saved locally.
* **Analytics:** Chart.js integration to track scores and visualize progress across different subjects.

## Tech Stack
* **Backend:** Python, Django, FastAPI, PostgreSQL, Redis
* **Frontend:** Vanilla JS, Bootstrap 5, Chart.js, MathJax
* **DevOps:** Docker, Docker Compose, Nginx

The project is currently hosted. [NovaPrep AI](https://novaprepai.com)

License
Proprietary. This was built for academic evaluation. See the LICENSE file for details.

