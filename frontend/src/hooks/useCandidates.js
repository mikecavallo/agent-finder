import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../utils/api';

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => (await api.get('/health')).data,
    staleTime: 60_000,
  });
}

export function useJobs() {
  return useQuery({ queryKey: ['jobs'], queryFn: async () => (await api.get('/jobs')).data });
}

export function useJob(jobId) {
  return useQuery({ queryKey: ['jobs', jobId], queryFn: async () => (await api.get(`/jobs/${jobId}`)).data });
}

export function useCreateJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload) => (await api.post('/jobs', payload)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  });
}

export function useDeleteJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (jobId) => api.delete(`/jobs/${jobId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  });
}

export function useCandidates(jobId) {
  return useQuery({
    queryKey: ['candidates', jobId],
    queryFn: async () => (await api.get(`/jobs/${jobId}/candidates`)).data,
  });
}

export function useCandidate(candidateId) {
  return useQuery({
    queryKey: ['candidate', candidateId],
    queryFn: async () => (await api.get(`/candidates/${candidateId}`)).data,
    enabled: Boolean(candidateId),
  });
}

function useInvalidateJob(jobId) {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: ['candidates', jobId] });
    qc.invalidateQueries({ queryKey: ['jobs'] });
  };
}

export function useUploadResumes(jobId) {
  const invalidate = useInvalidateJob(jobId);
  return useMutation({
    mutationFn: async (files) => {
      const form = new FormData();
      files.forEach((f) => form.append('files', f));
      return (await api.post(`/jobs/${jobId}/candidates/upload`, form)).data;
    },
    onSuccess: invalidate,
  });
}

export function usePasteResume(jobId) {
  const invalidate = useInvalidateJob(jobId);
  return useMutation({
    mutationFn: async ({ text, label }) =>
      (await api.post(`/jobs/${jobId}/candidates/text`, { text, label: label || null })).data,
    onSuccess: invalidate,
  });
}

function useCandidateMutation(jobId, request) {
  const qc = useQueryClient();
  const invalidate = useInvalidateJob(jobId);
  return useMutation({
    mutationFn: request,
    onSuccess: (data) => {
      if (data?.id) qc.setQueryData(['candidate', data.id], data);
      invalidate();
    },
  });
}

export function useUpdateCandidate(jobId) {
  return useCandidateMutation(jobId, async ({ id, ...changes }) => (await api.patch(`/candidates/${id}`, changes)).data);
}

export function useRescoreCandidate(jobId) {
  return useCandidateMutation(jobId, async (id) => (await api.post(`/candidates/${id}/rescore`)).data);
}

export function useOutreachDraft(jobId) {
  return useCandidateMutation(
    jobId,
    async ({ id, recruiterName }) =>
      (await api.post(`/candidates/${id}/outreach`, { recruiter_name: recruiterName })).data,
  );
}

export function useDeleteCandidate(jobId) {
  const invalidate = useInvalidateJob(jobId);
  return useMutation({ mutationFn: async (id) => api.delete(`/candidates/${id}`), onSuccess: invalidate });
}
