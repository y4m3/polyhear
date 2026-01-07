import {
  X,
  ArrowLeft,
  GitBranch,
  GitCommit,
  FileEdit,
  CheckCircle,
  XCircle,
  HelpCircle,
  Loader2,
  ListTodo,
  Clock,
} from "lucide-react";
import { useProject } from "../hooks/useProjects";
import type { StatusLevel } from "../types/project";

interface ProjectDetailProps {
  projectId: string;
  onClose: () => void;
}

function StatusBadge({
  status,
  label,
}: {
  status: StatusLevel;
  label: string;
}) {
  const config = {
    pass: {
      icon: CheckCircle,
      color: "text-green-400 bg-green-400/10",
      text: "Success",
    },
    fail: {
      icon: XCircle,
      color: "text-red-400 bg-red-400/10",
      text: "Failed",
    },
    skipped: {
      icon: HelpCircle,
      color: "text-yellow-400 bg-yellow-400/10",
      text: "Skipped",
    },
    unknown: {
      icon: HelpCircle,
      color: "text-surface-500 bg-surface-500/10",
      text: "Unknown",
    },
  };

  const { icon: Icon, color, text } = config[status] || config.unknown;

  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${color}`}>
      <Icon className="w-4 h-4" />
      <span className="text-sm font-medium">
        {label}: {text}
      </span>
    </div>
  );
}

function ChangeStatusIcon({ status }: { status: string }) {
  const colors: Record<string, string> = {
    M: "text-yellow-400",
    A: "text-green-400",
    D: "text-red-400",
    R: "text-blue-400",
    C: "text-purple-400",
    "?": "text-surface-500",
  };

  return (
    <span
      className={`font-mono font-bold ${colors[status] || "text-surface-400"}`}
    >
      {status}
    </span>
  );
}

export function ProjectDetail({ projectId, onClose }: ProjectDetailProps) {
  const { data: project, isLoading, error } = useProject(projectId);
  // TODO: Phase 2 - Implement refresh functionality
  // const refreshMutation = useRefreshProject()

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-start justify-center overflow-y-auto py-8"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-surface-900 border border-surface-700 rounded-xl w-full max-w-3xl mx-4 shadow-2xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-surface-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="p-1 rounded hover:bg-surface-800 text-surface-400 hover:text-surface-100"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h2 className="text-lg font-semibold text-surface-100">
                {project?.name || projectId}
              </h2>
              {project && (
                <div className="flex items-center gap-2 text-sm text-surface-400">
                  <GitBranch className="w-4 h-4" />
                  <span>{project.branch}</span>
                </div>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-surface-800 text-surface-400 hover:text-surface-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Loading state */}
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-surface-400 animate-spin" />
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="p-4 rounded-lg bg-red-900/30 border border-red-700 text-red-200">
              <p className="font-medium">Failed to load project details</p>
              <p className="text-sm mt-1">{error.message}</p>
            </div>
          )}

          {/* Project content */}
          {project && !project.error && (
            <>
              {/* Progress Summary */}
              <section className="bg-surface-800 rounded-lg p-4">
                <h3 className="text-sm font-medium text-surface-400 mb-3">
                  Progress Summary
                </h3>
                <div className="space-y-2">
                  {project.summary.completed && (
                    <div className="flex items-start gap-2 text-surface-200">
                      <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                      <span>Completed: {project.summary.completed}</span>
                    </div>
                  )}
                  {project.summary.working && (
                    <div className="flex items-start gap-2 text-surface-200">
                      <FileEdit className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                      <span>{project.summary.working}</span>
                    </div>
                  )}
                  {project.summary.failed && (
                    <div className="flex items-start gap-2 text-red-300">
                      <XCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                      <span>Failed: {project.summary.failed}</span>
                    </div>
                  )}
                  {(project.summary.todos > 0 ||
                    project.summary.fixmes > 0) && (
                    <div className="flex items-start gap-2 text-surface-300">
                      <ListTodo className="w-4 h-4 text-surface-500 flex-shrink-0 mt-0.5" />
                      <span>
                        Remaining:
                        {project.summary.todos > 0 &&
                          ` ${project.summary.todos} TODOs`}
                        {project.summary.fixmes > 0 &&
                          ` ${project.summary.fixmes} FIXMEs`}
                      </span>
                    </div>
                  )}
                </div>
              </section>

              {/* Recent Commits */}
              <section>
                <h3 className="text-sm font-medium text-surface-400 mb-3">
                  Recent Commits
                </h3>
                <div className="bg-surface-800 rounded-lg divide-y divide-surface-700">
                  {project.recent_commits.length === 0 ? (
                    <p className="p-4 text-surface-500 text-sm">
                      No commits found
                    </p>
                  ) : (
                    project.recent_commits.map((commit) => (
                      <div
                        key={commit.hash}
                        className="px-4 py-3 flex items-start gap-3"
                      >
                        <GitCommit className="w-4 h-4 text-surface-500 flex-shrink-0 mt-0.5" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <code className="text-xs text-blue-400 font-mono">
                              {commit.hash}
                            </code>
                            <span className="text-surface-200 truncate">
                              {commit.message}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 mt-1 text-xs text-surface-500">
                            {commit.author && <span>{commit.author}</span>}
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {commit.time}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </section>

              {/* Uncommitted Changes */}
              {project.uncommitted_changes.length > 0 && (
                <section>
                  <h3 className="text-sm font-medium text-surface-400 mb-3">
                    Uncommitted Changes ({project.uncommitted_changes.length}{" "}
                    files)
                  </h3>
                  <div className="bg-surface-800 rounded-lg p-4">
                    <div className="space-y-1 font-mono text-sm">
                      {project.uncommitted_changes.map((change, i) => (
                        <div key={i} className="flex items-center gap-3">
                          <ChangeStatusIcon status={change.status} />
                          <span className="text-surface-300 truncate">
                            {change.path}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </section>
              )}

              {/* Build & Test Status */}
              <section>
                <h3 className="text-sm font-medium text-surface-400 mb-3">
                  Build & Test Status
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-surface-800 rounded-lg p-4">
                    <StatusBadge status={project.build.status} label="Build" />
                    {project.build.duration_seconds && (
                      <p className="text-xs text-surface-500 mt-2">
                        Duration: {project.build.duration_seconds}s
                      </p>
                    )}
                    {project.build.timestamp && (
                      <p className="text-xs text-surface-500 mt-1">
                        Last run:{" "}
                        {new Date(project.build.timestamp).toLocaleString()}
                      </p>
                    )}
                    {project.build.message && (
                      <p className="text-sm text-red-300 mt-2">
                        {project.build.message}
                      </p>
                    )}
                  </div>

                  <div className="bg-surface-800 rounded-lg p-4">
                    <StatusBadge status={project.test.status} label="Test" />
                    {project.test.status !== "unknown" && (
                      <div className="mt-2 text-sm">
                        <span className="text-green-400">
                          {project.test.passed} passed
                        </span>
                        {project.test.failed > 0 && (
                          <span className="text-red-400 ml-2">
                            {project.test.failed} failed
                          </span>
                        )}
                        {project.test.skipped > 0 && (
                          <span className="text-yellow-400 ml-2">
                            {project.test.skipped} skipped
                          </span>
                        )}
                      </div>
                    )}
                    {project.test.failures.length > 0 && (
                      <div className="mt-3 space-y-1">
                        {project.test.failures.slice(0, 3).map((f, i) => (
                          <div key={i} className="text-xs text-red-300">
                            <span className="font-medium">FAIL</span> {f.name}
                          </div>
                        ))}
                        {project.test.failures.length > 3 && (
                          <p className="text-xs text-surface-500">
                            + {project.test.failures.length - 3} more failures
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                <p className="text-xs text-surface-500 mt-2">
                  ℹ️ Status read from log files (execution feature planned for
                  Phase 2)
                </p>
              </section>
            </>
          )}

          {/* Error display for project with error */}
          {project?.error && (
            <div className="p-4 rounded-lg bg-red-900/30 border border-red-700 text-red-200">
              <p className="font-medium">{project.error.message}</p>
              <p className="text-sm mt-1">{project.error.suggestion}</p>
              {project.error.details && (
                <p className="text-xs mt-2 text-red-400">
                  {project.error.details}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
