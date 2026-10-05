const API_BASE = '/api/v1';

export interface UserProfile {
  id: string;
  email: string;
  username: string;
  role: string;
  display_name: string;
  preferred_language: string;
  personalization_enabled: boolean;
}

export interface ChatMessage {
  conversation_id: string;
  message_id: string;
  role: string;
  content: string;
  tokens_input: number;
  tokens_output: number;
  latency_ms: number;
  cost_usd: number;
  risk_tier: string;
  detected_policy: string;
  memory_created?: string;
}

export interface CandidateItem {
  id: string;
  source_channel: string;
  pillar: string;
  format: string;
  candidate_text: string;
  risk_tier: string;
  status: string;
  created_at: string;
}

export interface AnalyticsDashboard {
  north_star_wmcr: number;
  dau: number;
  wau: number;
  total_tokens_processed: number;
  total_cost_usd: number;
  total_cost_inr: number;
  total_revenue_inr: number;
  contribution_margin_inr: number;
  feature_breakdown: Array<{ feature: string; calls: number; cost_usd: number }>;
  strategic_insights: Array<{ rule: string; diagnosis: string; recommended_action: string }>;
}

let authToken: string | null = localStorage.getItem('kalyan_token');

export const setAuthToken = (token: string | null) => {
  authToken = token;
  if (token) {
    localStorage.setItem('kalyan_token', token);
  } else {
    localStorage.removeItem('kalyan_token');
  }
};

export const getAuthToken = () => authToken;

const authHeaders = () => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  return headers;
};

export const api = {
  // Auth
  async signup(data: any) {
    const res = await fetch(`${API_BASE}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Signup failed');
    const json = await res.json();
    setAuthToken(json.access_token);
    return json;
  },

  async login(data: any) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Login failed');
    const json = await res.json();
    setAuthToken(json.access_token);
    return json;
  },

  async getMe(): Promise<UserProfile | null> {
    if (!authToken) return null;
    const res = await fetch(`${API_BASE}/auth/me`, { headers: authHeaders() });
    if (!res.ok) return null;
    return res.json();
  },

  async togglePersonalization(enabled: boolean) {
    const res = await fetch(`${API_BASE}/auth/privacy/toggle-personalization?enabled=${enabled}`, {
      method: 'POST',
      headers: authHeaders(),
    });
    return res.json();
  },

  // Chat
  async sendMessage(message: string, convId?: string, lang?: string): Promise<ChatMessage> {
    const res = await fetch(`${API_BASE}/chat/message`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        message,
        conversation_id: convId,
        language_preference: lang || 'hinglish',
        channel: 'web',
      }),
    });
    if (!res.ok) throw new Error('Chat failed');
    return res.json();
  },

  async getConversations() {
    const res = await fetch(`${API_BASE}/chat/conversations`, { headers: authHeaders() });
    if (!res.ok) return [];
    return res.json();
  },

  // Memories
  async getMemories() {
    const res = await fetch(`${API_BASE}/memories/`, { headers: authHeaders() });
    if (!res.ok) return [];
    return res.json();
  },

  async deleteMemory(id: string) {
    const res = await fetch(`${API_BASE}/memories/${id}`, {
      method: 'DELETE',
      headers: authHeaders(),
    });
    return res.json();
  },

  async clearMemories() {
    const res = await fetch(`${API_BASE}/memories/clear/all`, {
      method: 'DELETE',
      headers: authHeaders(),
    });
    return res.json();
  },

  // Approval Console
  async getCandidates(status?: string): Promise<CandidateItem[]> {
    const url = status ? `${API_BASE}/approval/candidates?status=${status}` : `${API_BASE}/approval/candidates`;
    const res = await fetch(url, { headers: authHeaders() });
    if (!res.ok) return [];
    return res.json();
  },

  async generateCandidates(count = 3, channel = 'x') {
    const res = await fetch(`${API_BASE}/approval/candidates/generate`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ count, channel }),
    });
    return res.json();
  },

  async approveCandidate(id: string) {
    const res = await fetch(`${API_BASE}/approval/candidates/${id}/approve`, {
      method: 'POST',
      headers: authHeaders(),
    });
    return res.json();
  },

  async rejectCandidate(id: string, reason: string) {
    const res = await fetch(`${API_BASE}/approval/candidates/${id}/reject?reason=${encodeURIComponent(reason)}`, {
      method: 'POST',
      headers: authHeaders(),
    });
    return res.json();
  },

  async editCandidate(id: string, new_text: string) {
    const res = await fetch(`${API_BASE}/approval/candidates/${id}/edit`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ new_text }),
    });
    return res.json();
  },

  // Publisher
  async publishCandidate(id: string) {
    const res = await fetch(`${API_BASE}/publisher/publish/${id}`, {
      method: 'POST',
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Publishing failed');
    return res.json();
  },

  async getPublishedHistory() {
    const res = await fetch(`${API_BASE}/publisher/published-history`, { headers: authHeaders() });
    if (!res.ok) return [];
    return res.json();
  },

  // Analytics
  async getAnalytics(): Promise<AnalyticsDashboard> {
    const res = await fetch(`${API_BASE}/analytics/dashboard`, { headers: authHeaders() });
    if (!res.ok) throw new Error('Analytics failed');
    return res.json();
  },

  // Experiments
  async getExperiments() {
    const res = await fetch(`${API_BASE}/experiments/`, { headers: authHeaders() });
    if (!res.ok) return [];
    return res.json();
  },

  // Subscriptions
  async getPlans() {
    const res = await fetch(`${API_BASE}/subscriptions/plans`);
    return res.json();
  },

  async getMyEntitlement() {
    const res = await fetch(`${API_BASE}/subscriptions/my-entitlement`, { headers: authHeaders() });
    if (!res.ok) return null;
    return res.json();
  },

  async checkout(plan_tier: string) {
    const res = await fetch(`${API_BASE}/subscriptions/checkout`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ plan_tier }),
    });
    return res.json();
  },

  // Admin & Kill switch
  async getKillSwitchStatus() {
    const res = await fetch(`${API_BASE}/admin/kill-switch/status`);
    return res.json();
  },

  async activateKillSwitch(reason: string) {
    const res = await fetch(`${API_BASE}/admin/kill-switch/activate`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ reason }),
    });
    return res.json();
  },

  async deactivateKillSwitch(reason: string) {
    const res = await fetch(`${API_BASE}/admin/kill-switch/deactivate`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ reason }),
    });
    return res.json();
  },

  async getAuditLogs() {
    const res = await fetch(`${API_BASE}/admin/audit-logs`, { headers: authHeaders() });
    if (!res.ok) return [];
    return res.json();
  },

  async getLore() {
    const res = await fetch(`${API_BASE}/admin/lore`);
    if (!res.ok) return [];
    return res.json();
  },

  async createLore(title: string, content: string, category: string, lore_type: string) {
    const res = await fetch(`${API_BASE}/admin/lore`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ title, content, category, lore_type }),
    });
    return res.json();
  },
};
