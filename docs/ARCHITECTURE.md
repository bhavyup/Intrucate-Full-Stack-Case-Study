# Architecture

Overview of how the service in `backend/` is put together and why. Task spec
is [TASK.md](TASK.md).

## Request flow

```
client
  |  POST /ask or /ask/batch
  v
routes/ask.py            validation (400 on bad body)
  |
  v
services/prompts.py      fetch Education_Prompt from Mongo, render {{userInput}}
  |
  v
services/llm.py          model call (provider picked by LLM_PROVIDER)
  |
  v
services/history.py      write request/response document
  |
  v
JSON response            {"response": ...} or {"responses": [...]}
```

`app.py` only wires the blueprint up. Routes talk HTTP, services talk to
everything that is not HTTP, and nothing crosses that line in either
direction.

## Components

| file | job |
|-|-|
| `routes/ask.py` | both endpoints, input validation, batch fan-out |
| `services/prompts.py` | loads the template document, substitutes the placeholder |
| `services/llm.py` | one `complete(prompt)` entry point over mock / openai / groq / gemini / nim |
| `services/history.py` | inserts history documents |
| `db.py` | shared PyMongo client and database handle |
| `seed_prompts.py` | inserts `Education_Prompt` if missing |

## Data model

`prompts` — one document per template, keyed by name:

```json
{ "_id": "Education_Prompt",
  "template": "You are an expert in education domain. Answer the following: {{userInput}}" }
```

`history` — one document per model call, including each item of a batch:

```json
{ "user_input": "...",
  "prompt": "...",
  "response": "...",
  "created_at": "<utc datetime>" }
```

Per-item documents rather than one document per request, because querying a
single question's history is the natural read pattern.

## Concurrency

Flask stays synchronous. The batch route runs one `asyncio` event loop per
request: each item becomes a coroutine wrapping `asyncio.to_thread` around
the blocking model call, and `asyncio.gather` collects results. Gather
preserves submission order, so response `i` always answers input `i`.

With a 2-second artificial latency per item, five items complete in about
two seconds total. A single-item request has nothing to parallelize, so it
stays a plain blocking call.

Failure policy: exceptions are caught per item and returned as an error
string in that slot. One bad item never fails the other nineteen; the batch
endpoint itself only returns 400 for a malformed body.

## LLM providers

Every supported backend speaks the OpenAI chat-completions API, so
`services/llm.py` is a provider table (base URL, env var for the key,
default model) plus one shared call path:

- `mock` (default): canned response, no network. Keeps the project runnable
  and reviewable without any API key; routing, rendering, concurrency, and
  history behave identically.
- `openai`, `groq`, `gemini`: cloud APIs behind `*_API_KEY` env vars.
- `nim`: a local proxy in front of NVIDIA NIM at `http://localhost:9797`,
  no key.

`LLM_PROVIDER` selects, `LLM_MODEL` overrides the default model.

## Decisions worth noting

- **Plain Flask, plain PyMongo.** Two routes and two collections do not
  justify an app framework or an ODM.
- **Batch reuses the single-item pipeline.** The only batch-specific code
  is the gather loop; rendering, the model call, and history writes are the
  same functions. Divergence between single and batch behavior is
  impossible by construction.
- **History write is part of the request path,** not a background task. It
  is one insert against a local-ish Mongo and keeps "did logging happen"
  answerable with one query, at the cost of a few milliseconds per call.

## Known limits / what real scale would change

- One event loop per batch request; a queue worker past a few dozen items
  per request.
- No timeouts on the model call; add per-item deadlines first.
- No index on `history.created_at`.
- Provider table is hardcoded; fine at five entries, a config file past
  that.
