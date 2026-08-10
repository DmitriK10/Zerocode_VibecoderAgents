# run_tests.py
import sys
import pytest

if __name__ == "__main__":
    # Запускаем pytest с параметрами
    sys.exit(pytest.main([
        "tests/",
        "-v",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--tb=short"
    ]))