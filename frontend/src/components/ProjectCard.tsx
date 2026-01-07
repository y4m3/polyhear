import {
  GitBranch,
  ArrowUp,
  ArrowDown,
  CheckCircle,
  XCircle,
  HelpCircle,
  AlertCircle,
  FileEdit,
  FolderGit2,
  ListTodo,
} from "lucide-react";
import type { Project, StatusLevel } from "../types/project";

interface ProjectCardProps {
  project: Project;
  onClick: () => void;
  isWorktree?: boolean;
}

function StatusIcon({ status }: { status: StatusLevel }) {
  switch (status) {
    case "pass":
      return <CheckCircle className="w-4 h-4 text-green-400" />;
    case "fail":
      return <XCircle className="w-4 h-4 text-red-400" />;
    case "skipped":
      return <HelpCircle className="w-4 h-4 text-yellow-400" />;
    default:
      return <HelpCircle className="w-4 h-4 text-surface-500" />;
  }
}

function WorkingStatusBadge({ status }: { status: Project["status"] }) {
  if (status.clean) {
    return (
      <span className="flex items-center gap-1 text-green-400">
        <span className="w-2 h-2 rounded-full bg-green-400" />
        Clean
      </span>
    );
  }

  const total = status.staged + status.modified + status.untracked;
  const parts = [];
  if (status.staged > 0) parts.push(`+${status.staged}`);
  if (status.modified > 0) parts.push(`~${status.modified}`);
  if (status.untracked > 0) parts.push(`?${status.untracked}`);

  // Color based on amount of changes
  const colorClass = total > 10 ? "text-orange-400" : "text-yellow-400";
  const dotClass = total > 10 ? "bg-orange-400" : "bg-yellow-400";

  return (
    <span className={`flex items-center gap-1 ${colorClass}`}>
      <span className={`w-2 h-2 rounded-full ${dotClass}`} />
      {parts.join(" ")}
    </span>
  );
}

export function ProjectCard({
  project,
  onClick,
  isWorktree = false,
}: ProjectCardProps) {
  const hasError = !!project.error;
  const hasFailed =
    project.build.status === "fail" || project.test.status === "fail";

  return (
    <div className={isWorktree ? "ml-6 mt-2" : ""}>
      <div
        onClick={onClick}
        className={`
          rounded-lg border transition-all cursor-pointer
          ${
            hasError
              ? "bg-red-950/30 border-red-800 hover:border-red-700"
              : hasFailed
                ? "bg-surface-900 border-red-800/50 hover:border-red-700"
                : "bg-surface-900 border-surface-700 hover:border-surface-500"
          }
        `}
      >
        {/* Header row */}
        <div className="px-4 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            {isWorktree && (
              <FolderGit2 className="w-4 h-4 text-surface-500 flex-shrink-0" />
            )}
            <h3 className="font-medium text-surface-100 truncate">
              {project.name}
            </h3>
            <div className="flex items-center gap-1 text-sm text-surface-400">
              <GitBranch className="w-4 h-4" />
              <span className="truncate max-w-[150px]">{project.branch}</span>
            </div>
          </div>

          <div className="flex items-center gap-4 flex-shrink-0">
            <WorkingStatusBadge status={project.status} />

            {/* Remote status */}
            {(project.remote.ahead > 0 || project.remote.behind > 0) && (
              <div className="flex items-center gap-2 text-sm">
                {project.remote.ahead > 0 && (
                  <span className="flex items-center gap-0.5 text-blue-400">
                    <ArrowUp className="w-3 h-3" />
                    {project.remote.ahead}
                  </span>
                )}
                {project.remote.behind > 0 && (
                  <span className="flex items-center gap-0.5 text-orange-400">
                    <ArrowDown className="w-3 h-3" />
                    {project.remote.behind}
                  </span>
                )}
              </div>
            )}

            {/* Build/Test status */}
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1" title="Build">
                <span className="text-xs text-surface-500">Build</span>
                <StatusIcon status={project.build.status} />
              </div>
              <div className="flex items-center gap-1" title="Test">
                <span className="text-xs text-surface-500">Test</span>
                <StatusIcon status={project.test.status} />
                {project.test.failed > 0 && (
                  <span className="text-xs text-red-400">
                    ({project.test.failed})
                  </span>
                )}
              </div>
            </div>

            {/* Last update time */}
            {project.last_commit && (
              <span className="text-sm text-surface-500 min-w-[70px] text-right">
                {project.last_commit.time}
              </span>
            )}
          </div>
        </div>

        {/* Error display */}
        {hasError && project.error && (
          <div className="px-4 pb-3 flex items-start gap-2 text-red-300">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium">{project.error.message}</p>
              <p className="text-xs text-red-400">{project.error.suggestion}</p>
            </div>
          </div>
        )}

        {/* Summary section */}
        {!hasError && (
          <div className="px-4 pb-3 border-t border-surface-800 pt-2">
            <div className="space-y-1 text-sm">
              {/* Completed */}
              {project.summary.completed && (
                <div className="flex items-start gap-2 text-surface-300">
                  <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                  <span>{project.summary.completed}</span>
                </div>
              )}

              {/* Working on */}
              {project.summary.working && (
                <div className="flex items-start gap-2 text-surface-300">
                  <FileEdit className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                  <span>{project.summary.working}</span>
                </div>
              )}

              {/* Failed */}
              {project.summary.failed && (
                <div className="flex items-start gap-2 text-red-300">
                  <XCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                  <span>{project.summary.failed}</span>
                </div>
              )}

              {/* TODOs */}
              {(project.summary.todos > 0 || project.summary.fixmes > 0) && (
                <div className="flex items-center gap-2 text-surface-400">
                  <ListTodo className="w-4 h-4 flex-shrink-0" />
                  <span>
                    {project.summary.todos > 0 &&
                      `${project.summary.todos} TODOs`}
                    {project.summary.todos > 0 &&
                      project.summary.fixmes > 0 &&
                      ", "}
                    {project.summary.fixmes > 0 &&
                      `${project.summary.fixmes} FIXMEs`}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Worktrees */}
      {project.worktrees && project.worktrees.length > 0 && (
        <div className="space-y-2">
          {project.worktrees.map((worktree) => (
            <ProjectCard
              key={worktree.id}
              project={worktree}
              onClick={onClick}
              isWorktree
            />
          ))}
        </div>
      )}
    </div>
  );
}
