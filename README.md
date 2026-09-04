# Intrucate Full-Stack Case Study

Flask + MongoDB service that answers questions through a prompt template
stored in the database. The task spec lives in [docs/TASK.md](docs/TASK.md).

Two endpoints:

- `POST /ask` - one question in, one answer out
- `POST /ask/batch` - a list of questions, answered concurrently, returned
  in the same order

Every request pulls the prompt template from a Mongo `prompts` collection,
substitutes the user's text into it, calls a language model, and logs the
request/response pair to a `history` collection.

The model is pluggable through `LLM_PROVIDER`: mock (default, no key
needed), OpenAI, Groq, Gemini, or a local NVIDIA NIM proxy.

## Where things live

- `backend/` - the whole service. Setup, usage, and design notes are in
  [backend/README.md](backend/README.md)
- `backend/seed_prompts.py` - seeds the `Education_Prompt` template
- `docs/` - the task description, submission instructions, and the
  [architecture notes](docs/ARCHITECTURE.md)

## Quick start

```
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python seed_prompts.py
python app.py
```

Needs MongoDB running locally (or point `MONGO_URI` elsewhere). Runs fine
with no API key using the default mock provider.
