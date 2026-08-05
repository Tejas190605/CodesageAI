import {
  DashboardSummary,
  RepositorySummary,
  PullRequestSummary,
  PullRequestDetail,
  PullRequestReviewResponse,
  HealthCheckResponse,
  ReviewJob,
  WorkerHealthResponse,
  User,
  Installation,
  OnboardRepoRequest,
  AIProviderInfo,
  PromptTemplateInfo,
  ModelSettingsInfo,
  EvaluationRunInfo,
  CodeSearchResponse,
  RepositoryIndexStatus,
  ReviewPolicyInfo,
  PolicyEvaluationInfo,
  AnalyticsOverviewInfo,
  ReviewAnalyticsInfo,
  FindingAnalyticsInfo,
  AIUsageAnalyticsInfo,
  JobAnalyticsInfo,
  AuditEventsResponse,
} from './types';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, '') ||
  'http://127.0.0.1:8000';

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {}),
      },
      credentials: 'include',
      cache: 'no-store',
    });

    if (!response.ok) {
      let errorMessage = `API request failed with status ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string'
            ? errorData.detail
            : JSON.stringify(errorData.detail);
        }
      } catch {
        // Fallback to HTTP status text if body is not JSON
      }
      throw new ApiError(errorMessage, response.status);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(
      `Unable to connect to CodeSage backend at ${API_BASE_URL}. Please verify FastAPI is running.`,
      0
    );
  }
}

export async function getHealth(): Promise<HealthCheckResponse> {
  return fetchJson<HealthCheckResponse>('/health');
}

export async function getDashboard(): Promise<DashboardSummary> {
  return fetchJson<DashboardSummary>('/api/dashboard');
}

export async function getRepositories(): Promise<RepositorySummary[]> {
  return fetchJson<RepositorySummary[]>('/api/repositories');
}

export async function getRepository(
  owner: string,
  repo: string
): Promise<{ repository: RepositorySummary; pull_requests: PullRequestSummary[] }> {
  const safeOwner = encodeURIComponent(owner);
  const safeRepo = encodeURIComponent(repo);
  return fetchJson<{ repository: RepositorySummary; pull_requests: PullRequestSummary[] }>(
    `/api/repositories/${safeOwner}/${safeRepo}`
  );
}

export async function getPullRequests(
  owner: string,
  repo: string,
  state: string = 'all'
): Promise<PullRequestSummary[]> {
  const safeOwner = encodeURIComponent(owner);
  const safeRepo = encodeURIComponent(repo);
  const safeState = encodeURIComponent(state);
  return fetchJson<PullRequestSummary[]>(
    `/api/repositories/${safeOwner}/${safeRepo}/pulls?state=${safeState}`
  );
}

export async function getPullRequest(
  owner: string,
  repo: string,
  number: number
): Promise<PullRequestDetail> {
  const safeOwner = encodeURIComponent(owner);
  const safeRepo = encodeURIComponent(repo);
  return fetchJson<PullRequestDetail>(
    `/api/pulls/${safeOwner}/${safeRepo}/${number}`
  );
}

export async function getPullRequestReview(
  owner: string,
  repo: string,
  number: number
): Promise<PullRequestReviewResponse> {
  const safeOwner = encodeURIComponent(owner);
  const safeRepo = encodeURIComponent(repo);
  return fetchJson<PullRequestReviewResponse>(
    `/api/pulls/${safeOwner}/${safeRepo}/${number}/review`
  );
}

// ======================================================
// JOB QUEUE & WORKER APIS
// ======================================================

export async function getJobs(status: string = 'all'): Promise<ReviewJob[]> {
  const safeStatus = encodeURIComponent(status);
  return fetchJson<ReviewJob[]>(`/api/jobs?status=${safeStatus}`);
}

export async function getJobDetail(jobId: string): Promise<ReviewJob> {
  const safeJobId = encodeURIComponent(jobId);
  return fetchJson<ReviewJob>(`/api/jobs/${safeJobId}`);
}

export async function retryJob(jobId: string): Promise<{ message: string; job: ReviewJob }> {
  const safeJobId = encodeURIComponent(jobId);
  return fetchJson<{ message: string; job: ReviewJob }>(`/api/jobs/${safeJobId}/retry`, {
    method: 'POST',
  });
}

export async function cancelJob(jobId: string): Promise<{ message: string; job: ReviewJob }> {
  const safeJobId = encodeURIComponent(jobId);
  return fetchJson<{ message: string; job: ReviewJob }>(`/api/jobs/${safeJobId}`, {
    method: 'DELETE',
  });
}

export async function getWorkerHealth(): Promise<WorkerHealthResponse> {
  return fetchJson<WorkerHealthResponse>('/api/worker/health');
}

// ======================================================
// AUTHENTICATION & INSTALLATION APIS
// ======================================================

export async function getCurrentUser(): Promise<User> {
  return fetchJson<User>('/api/auth/me');
}

export async function getAuthLoginUrl(): Promise<{ oauth_enabled: boolean; auth_url?: string | null; message?: string }> {
  return fetchJson<{ oauth_enabled: boolean; auth_url?: string | null; message?: string }>('/api/auth/github/login');
}

export async function logoutUser(): Promise<{ status: string; message: string }> {
  return fetchJson<{ status: string; message: string }>('/api/auth/logout', {
    method: 'POST',
  });
}

export async function getInstallations(): Promise<Installation[]> {
  return fetchJson<Installation[]>('/api/installations');
}

export async function getInstallationDetail(installationId: number): Promise<Installation> {
  return fetchJson<Installation>(`/api/installations/${installationId}`);
}

export async function onboardRepo(data: OnboardRepoRequest): Promise<{ status: string; repository: string }> {
  return fetchJson<{ status: string; repository: string }>('/api/installations/onboard', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ======================================================
// PHASE 5A — AI PLATFORM FOUNDATION APIS
// ======================================================

export async function getAIProviders(): Promise<AIProviderInfo[]> {
  return fetchJson<AIProviderInfo[]>('/api/ai/providers');
}

export async function getPromptTemplates(): Promise<PromptTemplateInfo[]> {
  return fetchJson<PromptTemplateInfo[]>('/api/ai/prompts');
}

export async function getModelSettings(owner: string, repo: string): Promise<ModelSettingsInfo> {
  const safeOwner = encodeURIComponent(owner);
  const safeRepo = encodeURIComponent(repo);
  return fetchJson<ModelSettingsInfo>(`/api/ai/settings/${safeOwner}/${safeRepo}`);
}

export async function updateModelSettings(
  owner: string,
  repo: string,
  settings: Partial<ModelSettingsInfo>
): Promise<ModelSettingsInfo> {
  const safeOwner = encodeURIComponent(owner);
  const safeRepo = encodeURIComponent(repo);
  return fetchJson<ModelSettingsInfo>(`/api/ai/settings/${safeOwner}/${safeRepo}`, {
    method: 'PUT',
    body: JSON.stringify(settings),
  });
}

export async function getAIUsage(): Promise<{
  summary: { total_requests: number; total_tokens: number; total_cost_usd: string };
  records: Record<string, unknown>[];
}> {
  return fetchJson<{
    summary: { total_requests: number; total_tokens: number; total_cost_usd: string };
    records: Record<string, unknown>[];
  }>('/api/ai/usage');
}

export async function getEvaluations(): Promise<EvaluationRunInfo[]> {
  return fetchJson<EvaluationRunInfo[]>('/api/ai/evaluations');
}

export async function triggerEvaluationRun(runName: string, provider: string, model: string): Promise<EvaluationRunInfo> {
  return fetchJson<EvaluationRunInfo>('/api/ai/evaluations/run', {
    method: 'POST',
    body: JSON.stringify({ run_name: runName, provider, model }),
  });
}

// ======================================================
// PHASE 5B — REPOSITORY INTELLIGENCE & SEMANTIC SEARCH
// ======================================================

export async function searchCode(
  repository: string,
  query: string,
  topK: number = 10,
  language?: string | null,
  filePath?: string | null
): Promise<CodeSearchResponse> {
  return fetchJson<CodeSearchResponse>('/api/search/code', {
    method: 'POST',
    body: JSON.stringify({
      repository,
      query,
      top_k: topK,
      language: language || null,
      file_path: filePath || null,
    }),
  });
}

export async function getRepoIndexStatus(owner: string, repo: string): Promise<RepositoryIndexStatus> {
  const safeOwner = encodeURIComponent(owner);
  const safeRepo = encodeURIComponent(repo);
  return fetchJson<RepositoryIndexStatus>(`/api/repositories/${safeOwner}/${safeRepo}/index/status`);
}

export async function triggerRepoIndexing(
  owner: string,
  repo: string,
  commitSha: string = 'main'
): Promise<{ message: string; repository: string; status: string; chunk_count: number }> {
  const safeOwner = encodeURIComponent(owner);
  const safeRepo = encodeURIComponent(repo);
  return fetchJson<{ message: string; repository: string; status: string; chunk_count: number }>(
    `/api/repositories/${safeOwner}/${safeRepo}/index`,
    {
      method: 'POST',
      body: JSON.stringify({ commit_sha: commitSha }),
    }
  );
}

// ======================================================
// PHASE 5C — POLICY ENGINE & REVIEW RULES
// ======================================================

export async function getPolicies(): Promise<ReviewPolicyInfo[]> {
  return fetchJson<ReviewPolicyInfo[]>('/api/policies');
}

export async function getEffectivePolicy(
  owner: string,
  repo: string
): Promise<{ repository: string; effective_policy: Record<string, unknown> }> {
  const safeOwner = encodeURIComponent(owner);
  const safeRepo = encodeURIComponent(repo);
  return fetchJson<{ repository: string; effective_policy: Record<string, unknown> }>(
    `/api/policies/effective/${safeOwner}/${safeRepo}`
  );
}

export async function getReviewPolicyEvaluation(reviewId: number): Promise<PolicyEvaluationInfo> {
  return fetchJson<PolicyEvaluationInfo>(`/api/reviews/${reviewId}/policy`);
}

// ======================================================
// PHASE 5D — ANALYTICS & AUDIT LOGS
// ======================================================

export async function getAnalyticsOverview(): Promise<AnalyticsOverviewInfo> {
  return fetchJson<AnalyticsOverviewInfo>('/api/analytics/overview');
}

export async function getReviewAnalytics(): Promise<ReviewAnalyticsInfo> {
  return fetchJson<ReviewAnalyticsInfo>('/api/analytics/reviews');
}

export async function getFindingAnalytics(): Promise<FindingAnalyticsInfo> {
  return fetchJson<FindingAnalyticsInfo>('/api/analytics/findings');
}

export async function getAIUsageAnalytics(): Promise<AIUsageAnalyticsInfo> {
  return fetchJson<AIUsageAnalyticsInfo>('/api/analytics/ai-usage');
}

export async function getJobAnalytics(): Promise<JobAnalyticsInfo> {
  return fetchJson<JobAnalyticsInfo>('/api/analytics/jobs');
}

export async function getAuditEvents(
  eventType?: string,
  limit: number = 50,
  offset: number = 0
): Promise<AuditEventsResponse> {
  const query = new URLSearchParams();
  if (eventType) query.set('event_type', eventType);
  query.set('limit', limit.toString());
  query.set('offset', offset.toString());

  return fetchJson<AuditEventsResponse>(`/api/audit-events?${query.toString()}`);
}

