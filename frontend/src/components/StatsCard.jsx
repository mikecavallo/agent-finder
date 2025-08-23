import React from 'react';

const StatsCard = ({ title, value, icon: Icon, change, color }) => {
    const colorClasses = {
        blue: 'bg-blue-100 text-blue-800',
        green: 'bg-green-100 text-green-800',
        purple: 'bg-purple-100 text-purple-800',
        orange: 'bg-orange-100 text-orange-800',
    };

    return (
        <div className="bg-white rounded-lg shadow p-6 flex items-center justify-between">
            <div>
                <p className="text-sm font-medium text-gray-500">{title}</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
                <p className="text-xs text-gray-500 mt-1">{change}</p>
            </div>
            <div className={`p-3 rounded-full ${colorClasses[color]}`}>
                <Icon className="w-6 h-6" />
            </div>
        </div>
    );
};

export default StatsCard;
