# Build plan: Intucate case study

Notes for myself before I start coding. Task came in through the docs in /docs. The gist: a small Flask + MongoDB service that takes user questions, wraps them in a stored prompt template, fires them at a chat model, and logs everything. Two endpoints, one single and one batch. The OpenAI part is allowed to be mocked, which matters because I am not going to burn an API key on something the reviewers said they do not care about. They care about structure, async handling, and whether I can explain my choices.

Time situation: the folder link dies 48 hours after they sent it, not after I opened it. So the order of operations reflects that. Working things first, polish later.

## What I am actually building

Two endpoints:

1. `POST /ask` takes `{"userInput": "..."}` (yes, the task doc spells it `userInput`, and also `userlnput` with a lowercase L in one place, which I am assuming is a typo in the PDF and not a trick). It looks up the Education prompt template from Mongo, substitutes the user text into the `{{userInput}}` placeholder, calls the model, saves request plus response into a `history` collection, returns `{"response": "..."}`.

2. `POST /ask/batch` takes a list of strings instead of one string. Each item goes through the same pipeline, concurrently, and the responses come back as a list in the same order the inputs arrived. Order is a requirement, not a nicety. `asyncio.gather` preserves order by default, so this is easy as long as I do not get clever.

Mongo side, two collections:

- `prompts` - holds templates. I will seed it with the Education example from the task doc, `_id: "Education_Prompt"`, template text and all.
- `history` - one document per call, storing the raw user input, the final rendered prompt, the model's reply, and a timestamp. Batch calls get one document per item, not one fat document, because querying per-item history later is the more natural shape.

## Tech decisions and why

- Flask, plain, not Flask-RESTful or anything heavier. Two routes does not justify a framework on top of a framework. Requirement files say `flask`, `pymongo`, `openai`, `python-dotenv`. I pin versions in requirements.txt.
- PyMongo directly, no ODM. The data shape is two collections with obvious fields. Mongoose-style ceremony buys nothing here.
- The AI call goes behind a small interface, `llm.py`, with two implementations: a real OpenAI one and a mock one that returns a canned string with a label so it is obvious in history which path ran. A `USE_MOCK_LLM=true` flag in `.env` switches between them. The reviewers explicitly said a mock is fine, and this way the code proves I know where the real call goes without needing a key to demo.
- Async: Flask itself stays sync. Inside the batch route I use `asyncio.run()` over a list of coroutines, each calling the model in a thread executor (`asyncio.to_thread`) so one slow call does not sit on the others. The single endpoint does one blocking call, which is fine, there is nothing to parallelize.
- Error handling: validate the body (400 on missing/empty field, 400 if batch input is not a list of strings), 500 with a clean message if the model call throws, and per-item errors in batch mode return an error string in that slot instead of failing the whole request. One bad item should not poison nineteen good ones.

## Project layout

```
project/
  app.py            # entry point, route registration, nothing else
  routes/ask.py     # both endpoints
  services/prompts.py   # load template, render placeholder
  services/llm.py       # real + mock model calls, same function signature
  services/history.py   # write history documents
  seed_prompts.py   # inserts the Education_Prompt doc if missing
  .env.example
  requirements.txt
  README.md
```

Keeping routes thin is deliberate. If they ask me in the review why something lives where it does, the answer is boring and consistent: routes talk HTTP, services talk to things that are not HTTP.

## Build order

1. Skeleton first: venv, pip install, a Flask app that answers 404-free on both routes with dummy responses. Proves the harness runs before any real logic exists.
2. Mongo hookup. Local Mongo or a free Atlas cluster, connection string in `.env`, a tiny `get_db()` helper. Then `seed_prompts.py` so the prompts collection exists with the Education template before I ever hit it from a request.
3. Single endpoint end to end with the mock LLM. At this point everything works except the actual AI call. This is the shortest path to something demonstrable, which matters given the deadline mechanics.
4. Swap in the real OpenAI call behind the flag. Fifteen minutes of work once the interface exists, and only if I decide it is worth using a key.
5. Batch endpoint with `asyncio.gather` and `return_exceptions=False` on the outer level, per-item try/except inside. Test it by pointing the mock at an artificial 2-second sleep and firing five items; total wall time should be ~2 seconds, not 10. That number goes in the README as the async proof.
6. History writes, checked by querying the collection with a Mongo client rather than trusting my own logs.
7. README: setup steps, env vars, curl examples for both endpoints, a note on the mock flag, and the async timing observation.

## Submission checklist

- Code pushed to a GitHub repo (public, since it goes into the form).
- Google Drive folder containing: this repo either as a link or a zip, the README, and whatever case-study document the application packet refers to.
- Drive folder shared to dhariaenterprisesindia@gmail.com with Editor, not Viewer. They called this out twice, so check the permission twice.
- Fill the submission form only after the Drive link works from an incognito window.
- Do all of this well inside the 48-hour window. The clock started when the link was sent.

## Things to be ready to talk about in the review

- Why a mock LLM by default (their own FAQ said the API is optional and they care about backend design).
- Why batch reuses the single-item pipeline instead of duplicating logic.
- Why per-item errors do not abort the batch.
- Why Flask sync plus `asyncio` inside the route, instead of switching the whole app to Quart or FastAPI. The honest answer: the task says Flask, and mixing in async only where it earns its keep is a smaller, more readable diff.
- What I would change at real scale: a connection pool shared across requests instead of per-call clients, a queue for batch work past a few dozen items, and an index on `history.timestamp`.

That is the whole plan. Small project, done carefully, with the deadline respected before anything clever.

