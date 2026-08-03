import {
  DashboardSummary,
  RepositorySummary,
  PullRequestSummary,
  PullRequestDetail,
  PullRequestReviewResponse,
  HealthCheckResponse,
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
