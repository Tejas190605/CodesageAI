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
