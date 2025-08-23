import React from 'react';
import SettingsPanel from '../components/SettingsPanel';

const Settings = () => {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
      <SettingsPanel />
    </div>
  );
};

export default Settings;
