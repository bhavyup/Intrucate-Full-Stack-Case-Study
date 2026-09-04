import asyncio

from flask import Blueprint, jsonify, request

from services import history
from services.llm import complete
from services.prompts import load_template, render

ask_bp = Blueprint("ask", __name__)


def handle_one(user_input):
    """The full pipeline for a single question. Batch reuses this per item
    so there's exactly one place where the behaviour lives."""
    template = load_template()
    prompt = render(template, user_input)
    response = complete(prompt)
    history.save(user_input, prompt, response)
    return response


@ask_bp.post("/ask")
def ask():
    body = request.get_json(silent=True) or {}
    user_input = str(body.get("userInput") or "").strip()
    if not user_input:
        return jsonify({"error": "userInput is required"}), 400

    try:
        return jsonify({"response": handle_one(user_input)})
    except LookupError as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": "the model call failed saying: " + str(exc)}), 500


@ask_bp.post("/ask/batch")
def ask_batch():
    body = request.get_json(silent=True) or {}
    inputs = body.get("inputs")

    if (not isinstance(inputs, list) or not inputs
            or any(not isinstance(s, str) or not s.strip() for s in inputs)):
        return jsonify({"error": "inputs must be a non-empty list of strings"}), 400

    async def run_all():
        # each item runs in its own thread via to_thread, so a slow model
        # call doesn't hold up the others; gather() keeps result order
        # matching input order on its own
        tasks = [asyncio.to_thread(handle_one, s) for s in inputs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # one bad item fails in its own slot instead of killing the batch
        return [r if isinstance(r, str) else f"error: {r}" for r in results]

    return jsonify({"responses": asyncio.run(run_all())})
