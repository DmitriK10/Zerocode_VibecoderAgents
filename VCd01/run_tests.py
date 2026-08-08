#!/usr/bin/env python
# run_tests.py
"""
Скрипт для запуска всех модульных тестов проекта.
Запускает все тесты из файлов с префиксом test_*.py в текущей директории.
"""

import unittest
import sys

if __name__ == "__main__":
    # Загружаем все тесты из текущей директории, соответствующие шаблону test_*.py
    loader = unittest.defaultTestLoader
    suite = loader.discover('.', pattern='test_*.py')
    
    # Запускаем тесты с выводом подробностей
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Возвращаем код завершения (0 – успешно, 1 – ошибка)
    sys.exit(0 if result.wasSuccessful() else 1)