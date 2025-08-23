import React, { useState } from 'react';
import api from '../utils/api';

const BulkActions = ({ selectedCandidateIds, onActionComplete }) => {
  const [recruiterName, setRecruiterName] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const handleBulkEmail = async () => {
    if (selectedCandidateIds.length === 0) {
      setError('Please select at least one candidate.');
      return;
    }
    if (!recruiterName) {
      setError('Please enter your name as the recruiter.');
      return;
    }

    setLoading(true);
    setMessage(null);
    setError(null);

    try {
      const response = await api.post('/email/bulk-send', {
        candidate_ids: selectedCandidateIds,
        recruiter_name: recruiterName,
      });
      setMessage(response.data.message);
      if (onActionComplete) {
        onActionComplete();
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send bulk emails.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-2">Bulk Actions</h3>
      <div className="mb-4">
        <label htmlFor="recruiterName" className="block text-sm font-medium text-gray-700">Your Name (Recruiter):</label>
        <input
          type="text"
          id="recruiterName"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
          value={recruiterName}
          onChange={(e) => setRecruiterName(e.target.value)}
          placeholder="e.g., Jane Doe"
        />
      </div>
      <button
        onClick={handleBulkEmail}
        disabled={loading || selectedCandidateIds.length === 0}
        className={`px-4 py-2 rounded-md text-white ${loading ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'}`}
      >
        {loading ? 'Sending...' : `Send Bulk Email (${selectedCandidateIds.length} selected)`}
      </button>
      {message && <p className="mt-2 text-sm text-green-600">{message}</p>}
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
};

export default BulkActions;
