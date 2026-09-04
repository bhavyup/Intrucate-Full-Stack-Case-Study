from datetime import datetime, timezone

from db import get_db

"""Service for saving the history of user inputs, prompts, and responses."""
def save(user_input, prompt, response):
    get_db().history.insert_one({
        "user_input": user_input,
        "prompt": prompt,
        "response": response,
        "created_at": datetime.now(timezone.utc),
    })
