export type StatusLevel = 'pass' | 'fail' | 'unknown' | 'skipped'

export interface WorkingStatus {
  clean: boolean
  staged: number
  modified: number
  untracked: number
}

export interface RemoteStatus {
  ahead: number
  behind: number
  tracking?: string
}

export interface BuildStatus {
  status: StatusLevel
  exit_code?: number
  duration_seconds?: number
  timestamp?: string
  message?: string
}

export interface TestStatus {
  status: StatusLevel
  passed: number
  failed: number
  skipped: number
  duration_ms?: number
  timestamp?: string
  failures: { name: string; message: string }[]
}

export interface LastCommit {
  hash: string
  message: string
  time: string
  author?: string
}

export interface ProjectSummary {
  completed?: string
  working?: string
  failed?: string
  todos: number
  fixmes: number
}

export interface ProjectError {
  code: string
  message: string
  suggestion: string
  details?: string
}

export interface Project {
  id: string
  name: string
  path: string
  branch: string
  status: WorkingStatus
  remote: RemoteStatus
  build: BuildStatus
  test: TestStatus
  last_commit?: LastCommit
  summary: ProjectSummary
  error?: ProjectError
  parent?: string
  worktrees: Project[]
}

export interface ProjectDetail extends Project {
  recent_commits: LastCommit[]
  uncommitted_changes: { status: string; path: string }[]
}

export interface ProjectCreate {
  name: string
  path: string
  group?: string
  parent?: string
  build_log?: string
  test_log?: string
}

export interface ProjectListResponse {
  projects: Project[]
  updated_at: string
}

export interface UISettings {
  theme: string
  refresh_interval: number
  max_commits: number
}

export interface SettingsResponse {
  ui: UISettings
  summary: {
    scan_todo: boolean
    todo_patterns: string[]
  }
  llm: {
    enabled: boolean
    provider: string
  }
}
