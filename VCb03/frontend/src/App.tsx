// App.tsx
import React, { useState } from 'react';
import './styles/App.css';
import DataTable from './components/DataTable';
import ModelSelector from './components/ModelSelector';
import AnalysisBlock from './components/AnalysisBlock';
import { uploadFile, analyzeData } from './api';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [tableData, setTableData] = useState<any[]>([]);
  const [totalRows, setTotalRows] = useState<number>(0);
  const [fileId, setFileId] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedModel, setSelectedModel] = useState<string>('yandex');
  const [analysisReport, setAnalysisReport] = useState<string>('');
  const [analysisLoading, setAnalysisLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError('');
    try {
      const result = await uploadFile(file);
      setTableData(result.data);
      setTotalRows(result.total_rows);
      setFileId(result.file_id);
      setAnalysisReport('');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!tableData.length && !fileId) {
      alert('Сначала загрузите данные');
      return;
    }
    setAnalysisLoading(true);
    setError('');
    try {
      // Используем fileId, если есть, иначе первые 15 строк
      const result = await analyzeData(
        fileId ? [] : tableData.slice(0, 15),
        selectedModel,
        fileId || undefined
      );
      setAnalysisReport(result.report);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setAnalysisLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>📊 Аналитика данных</h1>
        <p>Загрузите Excel, CSV или PDF</p>
      </header>

      <div className="upload-section">
        <input type="file" onChange={handleFileChange} accept=".xlsx,.xls,.csv,.pdf" />
        <button onClick={handleUpload} disabled={loading}>
          {loading ? 'Загрузка...' : 'Загрузить'}
        </button>
      </div>

      {error && <div className="error-message" style={{ color: 'red', margin: '10px 0' }}>{error}</div>}

      {tableData.length > 0 && (
        <>
          <div className="model-selector">
            <ModelSelector selectedModel={selectedModel} onModelChange={setSelectedModel} />
            <button onClick={handleAnalyze} disabled={analysisLoading}>
              {analysisLoading ? 'Анализируем...' : '🧠 Проанализировать данные'}
            </button>
          </div>

          <AnalysisBlock report={analysisReport} loading={analysisLoading} />

          <DataTable data={tableData} totalRows={totalRows} />
        </>
      )}
    </div>
  );
}

export default App;