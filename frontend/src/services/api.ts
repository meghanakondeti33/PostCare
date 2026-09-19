import type { User, Hospital, Patient, PatientTimeline, Campaign, OutreachTask, QueueSummary, Escalation, Protocol, EHRRecord } from '../types';

const API_BASE = 'http://localhost:8000/api/v1';

export function getAuthToken(): string | null {
  return localStorage.getItem('token');
}

export function setAuthToken(token: string) {
  localStorage.setItem('token', token);
}

export function clearAuthToken() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
}

export function getStoredUser(): User | null {
  const u = localStorage.getItem('user');
  return u ? JSON.parse(u) : null;
}

export function setStoredUser(user: User) {
  localStorage.setItem('user', JSON.stringify(user));
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const user = getStoredUser();
  if (user && user.hospital_id) {
    headers['X-Hospital-Id'] = user.hospital_id;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Network response was not ok' }));
    throw new Error(errorData.detail || `HTTP Error ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Auth
  login: async (email: string, password: string) => {
    const res = await request<{ access_token: string; token_type: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    setAuthToken(res.access_token);
    setStoredUser(res.user);
    return res;
  },

  getMe: () => request<User>('/auth/me'),

  // Hospitals
  getHospitals: () => request<Hospital[]>('/hospitals/'),

  // Patients & Timeline
  getPatients: (query?: string) => request<Patient[]>(`/patients/${query ? `?query=${encodeURIComponent(query)}` : ''}`),
  getPatientTimeline: (patientId: string) => request<PatientTimeline>(`/patients/${patientId}/timeline`),

  // Protocols
  getProtocols: () => request<Protocol[]>('/protocols/'),
  createProtocol: (data: any) =>
    request<Protocol>('/protocols/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // EHR Records
  getEHRRecords: () => request<EHRRecord[]>('/ehr/records'),

  // Campaigns
  getCampaigns: () => request<Campaign[]>('/campaigns/'),
  createCampaign: (data: any) =>
    request<Campaign>('/campaigns/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateCampaignStatus: (id: string, status: string) =>
    request<Campaign>(`/campaigns/${id}/status?status_str=${status}`, { method: 'POST' }),

  // Queue & Simulation
  getQueueSummary: () => request<QueueSummary>('/queue/summary'),
  getQueueTasks: (state?: string) => request<OutreachTask[]>(`/queue/tasks${state ? `?state=${state}` : ''}`),
  simulateQueueStep: (outcome?: string) =>
    request<any>(`/queue/simulate_step${outcome ? `?simulated_outcome=${outcome}` : ''}`, { method: 'POST' }),
  scheduleCallback: (taskId: string, requestedTimeIso: string) =>
    request<any>(`/queue/schedule_callback?task_id=${taskId}&requested_time_iso=${encodeURIComponent(requestedTimeIso)}`, {
      method: 'POST',
    }),

  // Calls
  simulateCall: (taskId: string, outcome?: string, responses?: string[]) =>
    request<any>('/calls/simulate', {
      method: 'POST',
      body: JSON.stringify({ task_id: taskId, simulated_outcome: outcome, patient_responses: responses }),
    }),
  getCallDetails: (callId: string) => request<any>(`/calls/${callId}`),

  // Escalations
  getEscalations: (state?: string) => request<Escalation[]>(`/escalations/${state ? `?state=${state}` : ''}`),
  getEscalationDetail: (id: string) => request<any>(`/escalations/${id}`),
  updateEscalation: (id: string, state?: string, notes?: string, reviewerId?: string) =>
    request<Escalation>(`/escalations/${id}/action`, {
      method: 'PUT',
      body: JSON.stringify({ state, resolution_notes: notes, assigned_reviewer_id: reviewerId }),
    }),

  // Observability & Analytics
  getHealth: () => request<any>('/observability/health'),
  getAuditLogs: () => request<any[]>('/observability/audit'),
  getAIMetrics: () => request<any>('/observability/ai_metrics'),
  getHospitalAnalytics: () => request<any>('/analytics/hospital'),
  getPlatformAnalytics: () => request<any>('/analytics/platform'),

  // Safety Evaluation
  runSafetyEval: () => request<any>('/evaluation/run', { method: 'POST' }),
};
