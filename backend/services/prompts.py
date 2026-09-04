from db import get_db

PLACEHOLDER = "{{userInput}}"


def load_template(template_id="Education_Prompt"):
    doc = get_db().prompts.find_one({"_id": template_id})
    if not doc:
        raise LookupError(f"prompt template '{template_id}' not found in Mongo")
    return doc["template"]


def render(template, user_input):
    # plain replace, not str.format, so any other curly braces the
    # template writer puts in there don't blow up the call
    return template.replace(PLACEHOLDER, user_input)
