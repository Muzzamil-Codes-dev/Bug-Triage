import os

# Use a dummy key so tests never pick up the real key from .env
# (load_dotenv does not override variables that are already set).
# Every LLM call in the tests is mocked.
os.environ.setdefault("OPENAI_API_KEY", "test-key")

# Keep tests isolated from the real data files: checkpoints live in
# memory and the LLM response cache is disabled.
os.environ["CHECKPOINT_DB"] = ":memory:"
os.environ["LLM_CACHE_DB"] = "off"
