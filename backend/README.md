# backend

Small Flask + MongoDB service for the Intucate case study. Takes a question,
wraps it in a prompt template stored in Mongo, asks a language model, logs the
exchange, and returns the answer. Endpoints for one question at a time and for
a batch of questions processed concurrently.

## Layout

- `app.py` - entry point, registers the blueprint
- `routes/ask.py` - the two endpoints; HTTP only, no business logic
- `services/prompts.py` - loads the template from Mongo, substitutes the user text
- `services/llm.py` - the model call, with a mock and a real implementation
- `services/history.py` - writes request/response documents
- `seed_prompts.py` - inserts the Education prompt template
- `db.py` - shared Mongo connection

## Setup

```
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # then edit if needed
```

You need MongoDB running somewhere. A local install works out of the box with
the default `MONGO_URI=mongodb://localhost:27017`. A free Atlas cluster works
too, just change the URI.

Seed the prompt template once:

```
python seed_prompts.py
```

Run the server:

```
python app.py
```

## Usage

Single question:

```
curl -X POST http://localhost:5000/ask ^
  -H "Content-Type: application/json" ^
  -d "{\"userInput\": \"How much should I score in each subject to pass CA final?\"}"
```

Response:

```json
{"response": "..."}
```

Batch:

```
curl -X POST http://localhost:5000/ask/batch ^
  -H "Content-Type: application/json" ^
  -d "{\"inputs\": [\"First question\", \"Second question\"]}"
```

Response:

```json
{"responses": ["...", "..."]}
```

The `responses` array is in the same order as `inputs`. If one item fails,
only that slot contains an error string; the rest still come through.

## Picking a model

`LLM_PROVIDER` in `.env` decides what answers the questions:

| value | what it talks to | needs a key? |
|-|-|-|
| `mock` (default) | nobody, returns a canned string | no |
| `nim` | a local OpenAI-compatible proxy at `http://localhost:9797/v1` | no |
| `groq` | Groq cloud | `GROQ_API_KEY` |
| `gemini` | Gemini's OpenAI-compatible endpoint | `GEMINI_API_KEY` |
| `openai` | OpenAI | `OPENAI_API_KEY` |

The mock is the default on purpose: routing, template substitution, async
batching, and history writes are identical either way, so the project runs end
to end with no key at all.

Each provider has a sensible default model. To override it, set `LLM_MODEL`,
for example `LLM_MODEL=meta/llama-3.2-90b-vision-instruct` for NIM. If your
proxy or endpoint needs extra fields beyond the key, put them in `.env` the
same way.

## Notes on the async part

Flask itself stays synchronous. Inside the batch route, each item is pushed
into a thread with `asyncio.to_thread` and the results are collected with
`asyncio.gather`, which returns them in input order. A quick way to see it
working: run five questions through `/ask/batch` and compare the wall time
against five sequential calls to `/ask`. With the mock the difference is
small, but against a real model with second-plus latency the batch call comes
back in roughly the time of one question, not five.

## What I would do if this grew

- Per-item timeouts so one hanging model call cannot stall a batch forever
- An index on `history.created_at`
- A queue (Celery, or just a background worker) once batch sizes get past a
  couple dozen items - one HTTP request should not own that much work
