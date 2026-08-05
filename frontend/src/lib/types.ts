export interface RepositorySummary {
  owner: string;
  name: string;
  full_name: string;
  description?: string | null;
  private: boolean;
  default_branch: string;
  html_url: string;
  open_pull_requests: number;
  updated_at?: string | null;
}

export interface PullRequestSummary {
  number: number;
  title: string;
  state: string;
  draft: boolean;
  author: string;
  html_url: string;
  created_at?: string | null;
  updated_at?: string | null;
  head_branch: string;
  base_branch: string;
}

export interface PullRequestDetail extends PullRequestSummary {
  changed_files: number;
  additions: number;
  deletions: number;
  commits: number;
  comments: number;
}

export interface ReviewCommentSummary {
  comment_id: number;
  created_at: string;
  updated_at: string;
  overall_rating?: number | null;
  markdown: string;
}

export interface PullRequestReviewResponse {
  repository: string;
  pull_number: number;
  reviewed: boolean;
  review_count: number;
  latest_review?: ReviewCommentSummary | null;
}

export interface DashboardSummary {
  repositories_count: number;
  open_pull_requests: number;
  reviewed_pull_requests: number;
  recent_pull_requests: PullRequestSummary[];
  average_score?: number | null;
}

export interface HealthCheckResponse {
  status: string;
  service: string;
}

export interface WorkerHealthResponse {
  status: string;
  redis_connected: boolean;
  queue_depth: number;
  running_workers: number;
  metrics: {
    total_jobs: number;
    queued: number;
    running: number;
    completed: number;
    failed: number;
    retry: number;
    dead_letter: number;
  };
  concurrency_limit: number;
  max_retries: number;
}

export interface ReviewJob {
  job_id: string;
  repository: string;
  pr_number: number;
  pr_title?: string | null;
  delivery_id?: string | null;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'retry' | 'dead_letter';
  priority: number;
  attempts: number;
  max_retries: number;
  failure_reason?: string | null;
  worker_id?: string | null;
  created_at: string;
  updated_at: string;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface User {
  id: number;
  github_id: number;
  username: string;
  email?: string | null;
  name?: string | null;
  avatar_url?: string | null;
  role: string;
  organizations?: Organization[];
  created_at: string;
}

export interface Organization {
  id: number;
  github_id: number;
  login: string;
  avatar_url?: string | null;
  description?: string | null;
  created_at: string;
}

export interface Installation {
  id: number;
  installation_id: number;
  account_login: string;
  account_id: number;
  account_type: string;
  target_type: string;
  repository_selection: string;
  status: string;
  created_at: string;
}

export interface OnboardRepoRequest {
  installation_id?: number;
  owner: string;
  name: string;
}

export interface AIProviderInfo {
  name: string;
  default_model: string;
  healthy: boolean;
  priority: number;
}

export interface PromptTemplateInfo {
  id: number;
  name: string;
  version: string;
  description: string;
  system_prompt: string;
  template_text: string;
  is_active: boolean;
}

export interface ModelSettingsInfo {
  owner_repo: string;
  provider: string;
  model: string;
  temperature: string;
  max_tokens: number;
  review_depth: string;
}

export interface EvaluationRunInfo {
  id: number;
  run_name: string;
  provider: string;
  model: string;
  status: string;
  quality_score: number;
  total_tests: number;
  passed_tests: number;
  created_at: string;
}

export interface SearchResultChunk {
  chunk_id: number;
  repository: string;
  file_path: string;
  symbol?: string | null;
  symbol_type?: string | null;
  start_line: number;
  end_line: number;
  content: string;
  score: number;
  citation: string;
}

export interface CodeSearchResponse {
  repository: string;
  query: string;
  total_results: number;
  results: SearchResultChunk[];
}

export interface RepositoryIndexStatus {
  id?: number;
  repository: string;
  status: string;
  commit_sha?: string | null;
  branch?: string | null;
  chunk_count: number;
  indexed_files: number;
  failed_files: number;
  embedding_provider?: string;
  embedding_model?: string;
  updated_at?: string | null;
}

export interface ReviewPolicyInfo {
  id: number;
  name: string;
  description?: string | null;
  enabled: boolean;
  version: string;
  rule_count: number;
  created_at?: string | null;
}

export interface RuleEvaluationInfo {
  id: number;
  rule_key: string;
  status: string;
  message: string;
  file_path?: string | null;
  start_line?: number | null;
  end_line?: number | null;
  metadata?: Record<string, unknown> | null;
}

export interface PolicyEvaluationInfo {
  id?: number;
  review_id?: number | null;
  passed: boolean;
  warning_count: number;
  failure_count: number;
  blocking_count: number;
  created_at?: string | null;
  rule_evaluations: RuleEvaluationInfo[];
}

export interface AnalyticsOverviewInfo {
  total_repositories: number;
  total_pull_requests: number;
  total_reviews: number;
  total_findings: number;
}

export interface ReviewAnalyticsInfo {
  total_reviews: number;
  clean_reviews: number;
  flagged_reviews: number;
  approval_rate: number;
}

export interface FindingAnalyticsInfo {
  by_severity: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
  };
  by_category: Record<string, number>;
  total_findings: number;
}

export interface AIUsageAnalyticsInfo {
  total_requests: number;
  total_tokens: number;
  total_cost_usd: string;
  by_provider: { provider: string; requests: number; tokens: number }[];
}

export interface JobAnalyticsInfo {
  total_jobs: number;
  completed: number;
  failed: number;
  queued: number;
  processing: number;
  success_rate_percent: number;
}

export interface AuditEventInfo {
  id: number;
  event_type: string;
  actor: string;
  organization_id?: number | null;
  repository_id?: number | null;
  user_id?: number | null;
  resource_type?: string | null;
  resource_id?: string | null;
  description?: string | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditEventsResponse {
  total: number;
  limit: number;
  offset: number;
  events: AuditEventInfo[];
}
