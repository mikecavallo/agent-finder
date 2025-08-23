import { useQuery } from 'react-query';
import api from '../utils/api';

export const useCandidates = () => {
  const { data, isLoading, error, refetch } = useQuery('candidates', async () => {
    const response = await api.get('/candidates'); // Assuming a /candidates endpoint
    return response.data;
  });

  // Placeholder for stats calculation
  const stats = {
    total: data?.length || 0,
    newToday: 0, // To be implemented
    highScoring: data?.filter(c => c.ai_score >= 8).length || 0,
    highScoringPercent: data?.length ? ((data.filter(c => c.ai_score >= 8).length / data.length) * 100).toFixed(2) : 0,
    contacted: data?.filter(c => c.contacted).length || 0,
    responseRate: 0, // To be implemented
    resumesDownloaded: data?.filter(c => c.resume_path).length || 0,
    resumeSuccessRate: data?.length ? ((data.filter(c => c.resume_path).length / data.length) * 100).toFixed(2) : 0,
  };

  return {
    candidates: data || [],
    stats,
    loading: isLoading,
    error,
    refresh: refetch,
  };
};
