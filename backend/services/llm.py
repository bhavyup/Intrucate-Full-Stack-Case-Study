import os

# Every provider here speaks the OpenAI chat API, so one code path covers
# all of them. The only things that change are the base URL, which env var
# holds the key, and a sensible default model.
PROVIDERS = {
    "mock": None,
    "openai": {
        "base_url": None,  # SDK default
        "key_env": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "default_model": "openai/gpt-oss-120b",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key_env": "GEMINI_API_KEY",
        "default_model": "gemini-2.0-flash",
    },
    "nim": {
        # local proxy in front of NVIDIA NIM, no key needed
        "base_url": "http://localhost:9797/v1",
        "key_env": None,
        "default_model": "meta/llama-3.2-90b-vision-instruct",
    },
}


def complete(prompt):
    """Single entry point used by both endpoints. LLM_PROVIDER decides the
    backend; mock removes the network entirely for key-less development."""
    provider = os.environ.get("LLM_PROVIDER", "mock").strip().lower()
    if provider == "mock":
        return _mock(prompt)
    if provider == "nim":
        return _chatNim(prompt, PROVIDERS[provider])
    if provider not in PROVIDERS:
        raise ValueError(f"unknown LLM_PROVIDER '{provider}'")
    return _chat(prompt, PROVIDERS[provider])


def _mock(prompt):
    return (
        "[mock response] This is a stand-in answer generated locally "
        f"for the prompt: ...{prompt[-80:]}"
    )


def _chat(prompt, cfg):
    from openai import OpenAI

    kwargs = {"api_key": "not-needed"}
    if cfg["key_env"]:
        kwargs["api_key"] = os.environ[cfg["key_env"]]
    if cfg["base_url"]:
        kwargs["base_url"] = cfg["base_url"]

    client = OpenAI(**kwargs)
    resp = client.chat.completions.create(
        model=os.environ.get("LLM_MODEL", cfg["default_model"]),
        stream=False,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content

def _chatNim(prompt, cfg):
    from openai import OpenAI

    kwargs = {"api_key": "not-needed"}
    if cfg["key_env"]:
        kwargs["api_key"] = os.environ[cfg["key_env"]]
    if cfg["base_url"]:
        kwargs["base_url"] = cfg["base_url"]

    client = OpenAI(**kwargs)
    resp = client.chat.completions.create(
        model=os.environ.get("LLM_MODEL", cfg["default_model"]),
        stream=False,
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0,
        top_p=0.95,
        max_tokens=4096,
        extra_body={"chat_template_kwargs": {"thinking": False}},
    )
    return resp.choices[0].message.content