import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]
KEYWORD_FILTER_THRESHOLD: float = float(os.getenv("KEYWORD_FILTER_THRESHOLD", "0.2"))
LLM_MATCH_THRESHOLD: float = float(os.getenv("LLM_MATCH_THRESHOLD", "0.6"))
DB_PATH: str = os.getenv("DB_PATH", "linked_whisper.db")
