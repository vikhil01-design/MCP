import os
from pathlib import Path

from dotenv import load_dotenv


def load_runtime_environment() -> None:
    """Load environment values from the project .env file and Streamlit secrets."""
    project_root = Path(__file__).resolve().parent.parent

    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)

    secrets_path = project_root / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        try:
            import tomllib

            with secrets_path.open("rb") as fh:
                data = tomllib.load(fh)

            for key, value in data.items():
                os.environ.setdefault(key, str(value))
        except Exception:
            pass

    try:
        import streamlit as st

        if hasattr(st, "secrets"):
            for key in st.secrets:
                os.environ.setdefault(key, str(st.secrets[key]))
    except Exception:
        pass


load_runtime_environment()
