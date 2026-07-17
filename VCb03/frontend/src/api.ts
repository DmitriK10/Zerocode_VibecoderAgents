// src/api.ts
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export async function uploadFile(file: File, page?: number): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);
  let url = `${API_BASE}/upload`;
  if (page !== undefined) {
    url += `?page=${page}`;
  }
  const res = await fetch(url, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json();
    throw new Error(errorData.error || 'Ошибка загрузки');
  }
  return res.json();
}

export async function analyzeData(tableData: any[], model: string, fileId?: string): Promise<any> {
  const body: any = { model };
  if (fileId) {
    body.file_id = fileId;
  } else {
    body.table_data = tableData;
  }
  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const errorData = await res.json();
    throw new Error(errorData.error || 'Ошибка анализа');
  }
  return res.json();
}