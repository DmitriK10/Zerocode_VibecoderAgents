import React, { useState } from 'react';

interface DataTableProps {
  data: any[];
  totalRows: number;
}

const DataTable: React.FC<DataTableProps> = ({ data, totalRows }) => {
  const [visibleRows, setVisibleRows] = useState(100);
  const columns = data.length > 0 ? Object.keys(data[0]) : [];

  const loadMore = () => {
    setVisibleRows((prev) => Math.min(prev + 100, data.length));
  };

  return (
    <div className="data-table" style={{ overflowX: 'auto', marginTop: '20px' }}>
      <p>Показано {Math.min(visibleRows, data.length)} из {totalRows} строк</p>
      <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: '14px' }}>
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col} style={{ border: '1px solid #ddd', padding: '8px', background: '#f2f2f2' }}>
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.slice(0, visibleRows).map((row, idx) => (
            <tr key={idx}>
              {columns.map((col) => (
                <td key={col} style={{ border: '1px solid #ddd', padding: '8px' }}>
                  {row[col] !== undefined && row[col] !== null ? String(row[col]) : ''}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {visibleRows < data.length && (
        <button onClick={loadMore} style={{ marginTop: '10px' }}>
          Показать ещё 100
        </button>
      )}
    </div>
  );
};

export default DataTable;