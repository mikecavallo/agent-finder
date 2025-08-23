// components/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import { Users, TrendingUp, Mail, FileText, RefreshCw } from 'lucide-react';
import { useCandidates } from '../hooks/useCandidates';
import CandidateTable from './CandidateTable';
import StatsCard from './StatsCard';

const Dashboard = () => {
    const { candidates, stats, loading, refresh } = useCandidates();
    const [filter, setFilter] = useState('all');

    const statsCards = [
        {
            title: 'Total Candidates',
            value: stats.total,
            icon: Users,
            change: `+${stats.newToday} today`,
            color: 'blue'
        },
        {
            title: 'High Scores (8+)',
            value: stats.highScoring,
            icon: TrendingUp,
            change: `${stats.highScoringPercent}% of total`,
            color: 'green'
        },
        {
            title: 'Contacted',
            value: stats.contacted,
            icon: Mail,
            change: `${stats.responseRate}% response rate`,
            color: 'purple'
        },
        {
            title: 'Resumes Downloaded',
            value: stats.resumesDownloaded,
            icon: FileText,
            change: `${stats.resumeSuccessRate}% success rate`,
            color: 'orange'
        }
    ];

    const filteredCandidates = candidates.filter(candidate => {
        switch (filter) {
            case 'high-score':
                return candidate.ai_score >= 8;
            case 'new':
                // Assuming date_added is a string that can be parsed
                return new Date(candidate.date_added) > new Date(Date.now() - 24 * 60 * 60 * 1000);
            case 'not-contacted':
                return !candidate.contacted;
            default:
                return true;
        }
    });

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold text-gray-900">Candidate Dashboard</h1>
                <button
                    onClick={refresh}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
                >
                    <RefreshCw size={18} />
                    <span>Refresh Data</span>
                </button>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {statsCards.map((card, index) => (
                    <StatsCard key={index} {...card} />
                ))}
            </div>

            {/* Filters */}
            <div className="flex space-x-4">
                <button
                    onClick={() => setFilter('all')}
                    className={`px-4 py-2 rounded-lg ${filter === 'all' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'}`}
                >
                    All Candidates
                </button>
                <button
                    onClick={() => setFilter('high-score')}
                    className={`px-4 py-2 rounded-lg ${filter === 'high-score' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'}`}
                >
                    High Score
                </button>
                <button
                    onClick={() => setFilter('new')}
                    className={`px-4 py-2 rounded-lg ${filter === 'new' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'}`}
                >
                    New Today
                </button>
                <button
                    onClick={() => setFilter('not-contacted')}
                    className={`px-4 py-2 rounded-lg ${filter === 'not-contacted' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'}`}
                >
                    Not Contacted
                </button>
            </div>

            {/* Candidate Table */}
            <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Candidate List</h2>
                {loading ? (
                    <p>Loading candidates...</p>
                ) : error ? (
                    <p className="text-red-500">Error loading candidates: {error.message}</p>
                ) : (
                    <CandidateTable candidates={filteredCandidates} />
                )}
            </div>
        </div>
    );
};

export default Dashboard;
