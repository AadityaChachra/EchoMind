# 🧠 EchoMind — Mental Health Monitoring & Support System

> **EchoMind** is an intelligent AI-driven mental health support system designed to provide empathetic guidance, detect crises, and assist users with emotional well-being.
> It integrates **FastAPI (Backend)**, **Streamlit (Frontend)**, **LangGraph + LangChain Agents**, and **Ollama MedGemma model** for compassionate and context-aware conversations.

---

## 🌟 Key Features

* 🗣️ **Conversational AI Therapist** — Uses the MedGemma model to provide human-like, empathetic responses.
* 🚨 **Crisis Detection & Emergency Calls** — Automatically calls helplines using Twilio if user shows self-harm intent.
* 📍 **Therapist Finder** — Suggests nearby therapists based on user’s location.
* 💬 **Real-time Chat Interface** — Built with Streamlit for seamless mental health conversations.
* ⚙️ **FastAPI Backend** — Handles message processing, AI agent orchestration, and API communication.
* 🔗 **LangGraph Integration** — Coordinates LLM + tool usage (e.g., MedGemma, emergency call, therapist lookup).
* 🧩 **Modular Architecture** — Easy to extend with new AI tools or models.

---

## 🧩 Tech Stack

| Layer            | Technology                       |
| ---------------- | -------------------------------- |
| Frontend         | Streamlit                        |
| Backend          | FastAPI                          |
| AI Orchestration | LangChain + LangGraph            |
| Model            | Ollama (`alibayram/medgemma:4b`) |
| Communication    | Twilio API                       |
| Language Runtime | Python 3.11+                     |

---

## 🗂️ Project Structure

```
aadityachachra-echomind/
├── README.md
├── pyproject.toml
├── frontend.py             # Streamlit frontend UI
├── main.py                 # Entry point
└── backend/
    ├── main.py             # FastAPI backend
    ├── ai_agent.py         # LangGraph agent + tools integration
    ├── tools.py            # Model and Twilio calling API tool
```

---

## ⚡ Quick Start

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/AadityaChachra/EchoMind.git
cd EchoMind
```

### 2️⃣ Install Dependencies (using [uv](https://docs.astral.sh/uv/))

If you haven’t already:

```bash
uv sync
```

This command will:

* Create a virtual environment (if not present)
* Install all dependencies from `pyproject.toml`
* Set up the environment exactly as intended

---

## 🧠 Run the Application

### Step 1: Start Backend (FastAPI)

```bash
cd backend
uvicorn main:app --reload
```

Server will start at:

```
http://localhost:8000
```

### Step 2: Start Frontend (Streamlit)

```bash
streamlit run frontend.py
```

Now visit:

```
http://localhost:8501
```

---

## 🔐 Environment Variables

Create a `config.py` file in the `backend/` folder with the following values:

```bash
# Twilio credentials
TWILIO_ACCOUNT_SID = "your_twilio_account_sid"
TWILIO_AUTH_TOKEN = "your_twilio_auth_token"
TWILIO_FROM_NUMBER = "+11234567890" # your Twilio number
EMERGENCY_CONTACT = "+911234567890" # or your local emergency number 

# Groq API
GROQ_API_KEY = "your_groq_api_key"
```

---

## 🧩 Agent Tools Overview

| Tool                                           | Purpose                                               |
| ---------------------------------------------- | ----------------------------------------------------- |
| `ask_mental_health_specialist(query)`          | Generates therapeutic responses using MedGemma model  |
| `find_nearby_therapists_by_location(location)` | Suggests nearby licensed therapists                   |
| `emergency_call_tool()`                        | Triggers emergency call to safety helpline via Twilio |

---

## 🧠 System Prompt Philosophy

> “You are an AI engine supporting mental health conversations with warmth and vigilance.”

The AI agent:

* Responds with empathy and guidance
* Detects emergencies and calls help when needed
* Suggests local professional help appropriately

---

## 🧰 Example Interaction

**User:**

> I feel really lost and anxious lately.

**EchoMind:**

> I can sense how heavy that must feel. Many people feel overwhelmed when facing constant stress.
> What’s been the hardest part for you recently?

*(Tool Used → `ask_mental_health_specialist`)*

---

<img width="1253" height="447" alt="image" src="https://github.com/user-attachments/assets/a9f45ab4-e293-408d-ae68-72b6ee12fa99" />
<br></br>
<img width="1166" height="570" alt="image" src="https://github.com/user-attachments/assets/9d072775-f2c9-4112-896e-ab409c1a2689" />
<br></br>
<img width="1188" height="384" alt="image" src="https://github.com/user-attachments/assets/80970644-468d-4317-9cfd-b4b308035b8d" />
<br></br>
