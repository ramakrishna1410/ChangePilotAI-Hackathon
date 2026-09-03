import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CHAT_MODEL = os.getenv("CHANGEPILOT_CHAT_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("CHANGEPILOT_EMBEDDING_MODEL", "text-embedding-3-small")

DB_PATH = os.getenv("CHANGEPILOT_DB_PATH", str(BASE_DIR / "changepilot.db"))
CHROMA_PATH = os.getenv("CHANGEPILOT_CHROMA_PATH", str(BASE_DIR / "chroma_store"))
SAMPLE_APP_PATH = os.getenv("CHANGEPILOT_SAMPLE_APP_PATH", str(BASE_DIR.parent / "sample-app"))

CHROMA_COLLECTION = "changepilot_code_knowledge"

# Retrieval tuning (§6.3 of the design doc).
RETRIEVAL_TOP_K = 8
RETRIEVAL_CANDIDATE_POOL = 20
