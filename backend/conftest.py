"""Root-level conftest: stub heavy AI/ML dependencies before app imports.

Uses try/except so real packages take precedence when installed (Windows venv).
Falls back to MagicMock stubs when packages are unavailable (CI / WSL without deps).
The actual AI/vector features are not tested here — only the CRUD and auth endpoints.
"""
import sys
from unittest.mock import MagicMock


def _stub(name: str) -> MagicMock:
    mock = MagicMock()
    sys.modules[name] = mock
    return mock


# chromadb
try:
    import chromadb  # noqa: F401
except ImportError:
    _stub("chromadb")
    _stub("chromadb.config")

# sentence_transformers
try:
    from sentence_transformers import SentenceTransformer  # noqa: F401
except ImportError:
    import numpy as np

    class _FakeSentenceTransformer:
        def __init__(self, *args, **kwargs):
            pass

        def encode(self, text, **kwargs):
            if isinstance(text, str):
                return np.zeros(384, dtype=np.float32)
            return np.zeros((len(text), 384), dtype=np.float32)

    st_stub = MagicMock()
    st_stub.SentenceTransformer = _FakeSentenceTransformer
    sys.modules["sentence_transformers"] = st_stub

# google.genai  (chat.py: from google import genai)
try:
    from google import genai  # noqa: F401
except (ImportError, AttributeError):
    if "google" not in sys.modules:
        google_mock = _stub("google")
        genai_mock = _stub("google.genai")
        google_mock.genai = genai_mock
    else:
        genai_mock = _stub("google.genai")
        sys.modules["google"].genai = genai_mock  # type: ignore[attr-defined]

# openai / anthropic (lazily imported classifiers — stub just in case)
try:
    import openai  # noqa: F401
except ImportError:
    _stub("openai")

try:
    import anthropic  # noqa: F401
except ImportError:
    _stub("anthropic")
