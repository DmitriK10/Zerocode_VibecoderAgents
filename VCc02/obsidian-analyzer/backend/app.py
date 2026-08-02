"""
Flask-приложение (SRP: отвечает только за маршруты и HTTP)
DIP: использует абстракции MCPAdapter и NoteAnalyzer
"""

import os
import json
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS

from config import config
from mcp_adapter import MCPAdapter
from analyzer import NoteAnalyzer


# Создаём приложение
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
CORS(app)

# Инициализируем адаптер MCP (DIP: внедрение зависимости)
mcp_adapter = MCPAdapter(config.OBSIDIAN_VAULT_PATH)


# HTML-шаблон для отображения отчёта
REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Obsidian Note Analyzer</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        h1 { color: #7c3aed; }
        .card { background: white; border-radius: 10px; padding: 20px; margin: 15px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .stat-item { background: #f0f0ff; padding: 15px; border-radius: 8px; text-align: center; }
        .stat-value { font-size: 28px; font-weight: bold; color: #7c3aed; }
        .stat-label { font-size: 14px; color: #666; }
        .tag-cloud { display: flex; flex-wrap: wrap; gap: 8px; }
        .tag { background: #e0e7ff; padding: 5px 12px; border-radius: 15px; font-size: 14px; }
        .tag:hover { background: #c7d2fe; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f0f0ff; }
        .refresh-btn { background: #7c3aed; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        .refresh-btn:hover { background: #6d28d9; }
        .loading { display: none; color: #666; }
        .error { color: #dc2626; }
    </style>
</head>
<body>
    <h1>📊 Obsidian Note Analyzer</h1>
    <button class="refresh-btn" onclick="refreshData()">🔄 Обновить</button>
    <span class="loading" id="loading">Загрузка...</span>
    <div id="report"></div>

    <script>
        async function refreshData() {
            document.getElementById('loading').style.display = 'inline';
            try {
                const response = await fetch('/api/analyze');
                const data = await response.json();
                renderReport(data);
            } catch (e) {
                document.getElementById('report').innerHTML = '<div class="card error">Ошибка загрузки данных: ' + e.message + '</div>';
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }

        function renderReport(data) {
            let html = '';
            
            // Общая статистика
            html += `<div class="card">
                <h2>📈 Общая статистика</h2>
                <div class="stats-grid">
                    <div class="stat-item"><div class="stat-value">${data.total_notes || 0}</div><div class="stat-label">Всего заметок</div></div>
                    <div class="stat-item"><div class="stat-value">${data.daily_notes_count || 0}</div><div class="stat-label">Ежедневных заметок</div></div>
                    <div class="stat-item"><div class="stat-value">${Object.keys(data.tags || {}).length}</div><div class="stat-label">Уникальных тегов</div></div>
                    <div class="stat-item"><div class="stat-value">${Object.keys(data.links || {}).length}</div><div class="stat-label">Уникальных связей</div></div>
                </div>
            </div>`;

            // Теги
            if (data.tags && Object.keys(data.tags).length > 0) {
                html += `<div class="card"><h2>🏷️ Популярные теги</h2><div class="tag-cloud">`;
                for (const [tag, count] of Object.entries(data.tags)) {
                    const size = Math.min(24, 12 + count * 2);
                    html += `<span class="tag" style="font-size:${size}px">#${tag} (${count})</span>`;
                }
                html += `</div></div>`;
            }

            // Связи
            if (data.links && Object.keys(data.links).length > 0) {
                html += `<div class="card"><h2>🔗 Внутренние связи</h2><table>
                    <tr><th>Заметка</th><th>Количество ссылок</th></tr>`;
                for (const [note, count] of Object.entries(data.links)) {
                    html += `<tr><td>${note}</td><td>${count}</td></tr>`;
                }
                html += `</table></div>`;
            }

            // Частота слов
            if (data.word_frequency && Object.keys(data.word_frequency).length > 0) {
                html += `<div class="card"><h2>📝 Частота слов (топ-20)</h2><table>
                    <tr><th>Слово</th><th>Количество</th></tr>`;
                let count = 0;
                for (const [word, freq] of Object.entries(data.word_frequency)) {
                    if (count++ >= 20) break;
                    if (freq > 1) {
                        html += `<tr><td>${word}</td><td>${freq}</td></tr>`;
                    }
                }
                html += `</table></div>`;
            }

            document.getElementById('report').innerHTML = html;
        }

        // Автоматическая загрузка
        refreshData();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Главная страница"""
    return render_template_string(REPORT_TEMPLATE)


@app.route('/api/analyze')
def analyze():
    """API для получения аналитики по заметкам"""
    try:
        # Получаем список файлов через MCP-адаптер
        files = mcp_adapter.list_files()
        
        # Создаём анализатор (DIP: передаём зависимость)
        analyzer = NoteAnalyzer(files, mcp_adapter.get_file_content)
        
        # Выполняем анализ
        results = analyzer.analyze()
        
        return jsonify(results)
    except Exception as e:
        import traceback
        print(f"ERROR in /api/analyze: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/search')
def search():
    """API для поиска по заметкам"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({"results": []})
    
    try:
        results = mcp_adapter.search(query)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/backlinks/<path:note>')
def backlinks(note: str):
    """API для получения обратных ссылок"""
    try:
        files = mcp_adapter.list_files()
        analyzer = NoteAnalyzer(files, mcp_adapter.get_file_content)
        backlinks = analyzer.find_backlinks(note)
        return jsonify({"backlinks": backlinks})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/health')
def health():
    """Проверка здоровья сервиса"""
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=config.DEBUG)