"""Seeds the prompts collection with the template from the task spec.
Safe to run more than once; it upserts instead of duplicating."""

from dotenv import load_dotenv

load_dotenv()

from db import get_db

EDUCATION_TEMPLATE = (
    "You are an expert in education domain. Answer the following: {{userInput}}"
)


def seed():
    get_db().prompts.update_one(
        {"_id": "Education_Prompt"},
        {"$set": {"template": EDUCATION_TEMPLATE}},
        upsert=True,
    )
    print("seeded prompts collection")


if __name__ == "__main__":
    seed()
