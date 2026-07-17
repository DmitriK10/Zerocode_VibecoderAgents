import React from 'react';

interface ModelSelectorProps {
  selectedModel: string;
  onModelChange: (model: string) => void;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({ selectedModel, onModelChange }) => {
  return (
    <div style={{ margin: '10px 0' }}>
      <label htmlFor="model-select" style={{ marginRight: '10px' }}>
        Выберите модель:
      </label>
      <select
        id="model-select"
        value={selectedModel}
        onChange={(e) => onModelChange(e.target.value)}
        style={{ padding: '6px 12px', borderRadius: '4px', border: '1px solid #ccc' }}
      >
        <option value="yandex">YandexGPT</option>
        <option value="proxy">GPT-4o-mini (через ProxyAPI)</option>
      </select>
    </div>
  );
};

export default ModelSelector;