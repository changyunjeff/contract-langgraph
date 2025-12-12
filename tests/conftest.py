"""Pytest configuration and fixtures."""

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv


def pytest_configure() -> None:
    """Load environment variables from .env file before tests run."""
    # Get the project root directory (where .env file is located)
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    # Add project root to Python path for imports (allows 'from src.llm import ...')
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Load .env file if it exists
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded environment variables from {env_file}")
    else:
        print(f"Warning: .env file not found at {env_file}")


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"


@pytest.fixture(scope="session")
def openai_api_key() -> str:
    """Get OpenAI API key from environment variables.
    
    Raises:
        ValueError: If OPENAI_API_KEY is not set.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please set it in your .env file or environment."
        )
    return api_key
