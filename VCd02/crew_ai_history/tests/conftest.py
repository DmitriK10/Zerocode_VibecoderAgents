# tests/conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.generate.return_value = "test response"
    return llm