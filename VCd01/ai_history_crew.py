# ai_history_crew.py
"""
Вспомогательный скрипт для запуска обзора истории ИИ с фактчекером в консоли.
Использует ту же логику, что и бот, но без Telegram-интерфейса.
"""

from agents_runner import run_ai_history

if __name__ == "__main__":
    print("\n=== Запуск CrewAI для создания обзора истории ИИ (с фактчекером) ===\n")
    result = run_ai_history(enable_fact_check=True)
    print("\n=== ФИНАЛЬНЫЙ ОБЗОР ===\n")
    print(result)

    # Сохраняем в файл
    from pathlib import Path
    output_path = Path(__file__).parent / "ai_history_review_factchecked.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"\n✅ Результат сохранён в файл: {output_path}")