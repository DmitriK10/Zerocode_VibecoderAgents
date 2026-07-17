# pdf_server.py
import os
import logging
import json
import uuid
import tempfile
from io import BytesIO
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import pdfplumber
import openpyxl
from dotenv import load_dotenv

from analyzers.factory import AnalyzerFactory
from config import Config
from dto import UploadResponse, AnalyzeRequest, AnalyzeResponse

# Загружаем переменные окружения (уже в config)
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
CORS(app)  # Разрешаем запросы с фронтенда

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаём папку для загрузок, если её нет
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# ---------- Вспомогательные функции для чтения файлов ----------

def read_excel(file_bytes: bytes) -> list:
    """Читает Excel-файл (xlsx/xls) и возвращает список словарей."""
    df = pd.read_excel(BytesIO(file_bytes), engine='openpyxl')
    return df.to_dict(orient='records')

def read_csv(file_bytes: bytes) -> list:
    """Читает CSV-файл с автоопределением разделителя."""
    for sep in [',', ';', '\t']:
        try:
            df = pd.read_csv(BytesIO(file_bytes), sep=sep, encoding='utf-8')
            if len(df.columns) > 1:
                return df.to_dict(orient='records')
        except:
            continue
    df = pd.read_csv(BytesIO(file_bytes), encoding='utf-8')
    return df.to_dict(orient='records')

def read_pdf(file_bytes: bytes, page_number: int = 0) -> list:
    """
    Извлекает таблицы из PDF. Если page_number >= 0, ищет на указанной странице.
    Если на указанной странице нет таблиц, ищет на всех страницах и возвращает первую найденную.
    """
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        total_pages = len(pdf.pages)
        pages_to_try = []
        if page_number >= 0 and page_number < total_pages:
            pages_to_try = [page_number]
        else:
            pages_to_try = range(total_pages)

        for page_idx in pages_to_try:
            page = pdf.pages[page_idx]
            tables = page.extract_tables()
            if tables:
                # Берём первую таблицу на странице
                table = tables[0]
                if len(table) > 0:
                    headers = table[0]
                    rows = []
                    for row in table[1:]:
                        row_dict = {}
                        for i, header in enumerate(headers):
                            if i < len(row):
                                row_dict[header] = row[i]
                            else:
                                row_dict[header] = None
                        rows.append(row_dict)
                    return rows
        return []

# ---------- Кэширование данных ----------
# Храним данные в памяти для быстрого доступа, а также сохраняем на диск
data_cache = {}  # file_id -> list

def save_data_to_cache(data: list) -> str:
    """Сохраняет данные в папку uploads и возвращает file_id."""
    file_id = str(uuid.uuid4())
    file_path = os.path.join(Config.UPLOAD_FOLDER, f"{file_id}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    data_cache[file_id] = data
    return file_id

def load_data_from_cache(file_id: str) -> list:
    """Загружает данные из кэша (сначала из памяти, потом с диска)."""
    if file_id in data_cache:
        return data_cache[file_id]
    file_path = os.path.join(Config.UPLOAD_FOLDER, f"{file_id}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            data_cache[file_id] = data
            return data
    return None

# ---------- Основной маршрут для загрузки файла ----------

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не передан'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400

    # Проверка расширения
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in Config.ALLOWED_EXTENSIONS:
        return jsonify({'error': f'Неподдерживаемый формат. Разрешены: {", ".join(Config.ALLOWED_EXTENSIONS)}'}), 400

    # Проверка MIME-типа (опционально)
    # if file.mimetype not in Config.ALLOWED_MIMETYPES.values():
    #     return jsonify({'error': 'Неверный MIME-тип файла'}), 400

    file_bytes = file.read()
    try:
        if ext in ('xlsx', 'xls'):
            data = read_excel(file_bytes)
        elif ext == 'csv':
            data = read_csv(file_bytes)
        elif ext == 'pdf':
            # Получаем номер страницы из аргументов запроса (по умолчанию 0)
            page_num = request.args.get('page', 0, type=int)
            data = read_pdf(file_bytes, page_number=page_num)
        else:
            return jsonify({'error': 'Неподдерживаемый формат файла'}), 400

        if not data:
            return jsonify({'error': 'Не удалось извлечь данные из файла'}), 400

        # Сохраняем в кэш
        file_id = save_data_to_cache(data)

        response = UploadResponse(
            data=data[:100],
            total_rows=len(data),
            columns=list(data[0].keys()) if data else [],
            file_id=file_id
        )
        return jsonify(response.__dict__)
    except Exception as e:
        logger.error(f"Ошибка при чтении файла: {e}")
        return jsonify({'error': str(e)}), 500

# ---------- Эндпоинт для анализа нейросетью ----------

@app.route('/analyze', methods=['POST'])
def analyze_data():
    req_data = request.get_json()
    if not req_data:
        return jsonify({'error': 'Нет данных'}), 400

    # Используем DTO для валидации
    try:
        analyze_req = AnalyzeRequest(
            table_data=req_data.get('table_data'),
            model=req_data.get('model', 'yandex'),
            file_id=req_data.get('file_id')
        )
    except Exception as e:
        return jsonify({'error': f'Неверный формат запроса: {str(e)}'}), 400

    # Если передан file_id, загружаем данные из кэша
    if analyze_req.file_id:
        table_data = load_data_from_cache(analyze_req.file_id)
        if table_data is None:
            return jsonify({'error': 'Данные не найдены по указанному file_id'}), 404
    else:
        table_data = analyze_req.table_data

    if not table_data:
        return jsonify({'error': 'Нет данных для анализа'}), 400

    # Получаем анализатор через фабрику с конфигом
    try:
        analyzer = AnalyzerFactory.get_analyzer(analyze_req.model, config=Config)
        report = analyzer.analyze(table_data)
        response = AnalyzeResponse(report=report)
        return jsonify(response.__dict__)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Ошибка анализа: {e}")
        return jsonify({'error': str(e)}), 500

# ---------- Запуск ----------

if __name__ == '__main__':
    app.run(debug=True, port=5000)