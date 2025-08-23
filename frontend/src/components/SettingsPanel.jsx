import React from 'react';

const SettingsPanel = () => {
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-xl font-semibold mb-4">Application Settings</h2>
      <p>Settings options will be implemented here.</p>
      {/* Example setting: API Key input */}
      <div className="mb-4">
        <label htmlFor="openaiApiKey" className="block text-sm font-medium text-gray-700">OpenAI API Key:</label>
        <input
          type="text"
          id="openaiApiKey"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
          placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        />
      </div>
      {/* More settings can be added here */}
    </div>
  );
};

export default SettingsPanel;
