import React from 'react';

interface AnalysisBlockProps {
  report: string;
  loading: boolean;
}

const AnalysisBlock: React.FC<AnalysisBlockProps> = ({ report, loading }) => {
  return (
    <div className="analysis-block" style={{ margin: '20px 0', padding: '15px', background: '#f5f5f5', borderRadius: '8px' }}>
      <h3>🧠 Анализ от нейросети</h3>
      {loading && <p>⏳ Генерация анализа...</p>}
      {!loading && report && (
        <div style={{ whiteSpace: 'pre-wrap', textAlign: 'left' }}>
          {report}
        </div>
      )}
      {!loading && !report && <p style={{ color: '#999' }}>Здесь появится вывод от нейросети после анализа.</p>}
    </div>
  );
};

export default AnalysisBlock;