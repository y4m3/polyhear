import { useState } from "react";
import { X, FolderOpen, Loader2 } from "lucide-react";
import { useCreateProject } from "../hooks/useProjects";
import type { ProjectCreate } from "../types/project";

interface ProjectFormProps {
  onClose: () => void;
}

export function ProjectForm({ onClose }: ProjectFormProps) {
  const [formData, setFormData] = useState<ProjectCreate>({
    name: "",
    path: "",
    group: "",
    parent: "",
    build_log: "",
    test_log: "",
  });
  const [showAdvanced, setShowAdvanced] = useState(false);

  const createProject = useCreateProject();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Clean up optional fields
    const data: ProjectCreate = {
      name: formData.name.trim(),
      path: formData.path.trim(),
    };
    if (formData.group?.trim()) data.group = formData.group.trim();
    if (formData.parent?.trim()) data.parent = formData.parent.trim();
    if (formData.build_log?.trim()) data.build_log = formData.build_log.trim();
    if (formData.test_log?.trim()) data.test_log = formData.test_log.trim();

    try {
      await createProject.mutateAsync(data);
      onClose();
    } catch {
      // Error is handled by mutation state
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // Auto-fill name from path if name is empty
    if (name === "path" && !formData.name) {
      const pathParts = value.split("/").filter(Boolean);
      if (pathParts.length > 0) {
        setFormData((prev) => ({
          ...prev,
          name: pathParts[pathParts.length - 1],
        }));
      }
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-surface-900 border border-surface-700 rounded-xl w-full max-w-lg mx-4 shadow-2xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-surface-700 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-surface-100">
            Add Project
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-surface-800 text-surface-400 hover:text-surface-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Path */}
          <div>
            <label
              htmlFor="path"
              className="block text-sm font-medium text-surface-300 mb-1"
            >
              Repository Path <span className="text-red-400">*</span>
            </label>
            <div className="relative">
              <FolderOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500" />
              <input
                type="text"
                id="path"
                name="path"
                value={formData.path}
                onChange={handleChange}
                placeholder="/home/user/dev/my-project"
                required
                className="w-full pl-10 pr-4 py-2 bg-surface-800 border border-surface-600 rounded-lg text-surface-100 placeholder-surface-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <p className="text-xs text-surface-500 mt-1">
              Absolute path or relative to POLYHEAR_REPOS_ROOT
            </p>
          </div>

          {/* Name */}
          <div>
            <label
              htmlFor="name"
              className="block text-sm font-medium text-surface-300 mb-1"
            >
              Project Name <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="my-project"
              required
              className="w-full px-4 py-2 bg-surface-800 border border-surface-600 rounded-lg text-surface-100 placeholder-surface-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Advanced options toggle */}
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-blue-400 hover:text-blue-300"
          >
            {showAdvanced
              ? "- Hide advanced options"
              : "+ Show advanced options"}
          </button>

          {/* Advanced options */}
          {showAdvanced && (
            <div className="space-y-4 pt-2 border-t border-surface-700">
              {/* Group */}
              <div>
                <label
                  htmlFor="group"
                  className="block text-sm font-medium text-surface-300 mb-1"
                >
                  Group
                </label>
                <input
                  type="text"
                  id="group"
                  name="group"
                  value={formData.group}
                  onChange={handleChange}
                  placeholder="client-a"
                  className="w-full px-4 py-2 bg-surface-800 border border-surface-600 rounded-lg text-surface-100 placeholder-surface-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Parent (for worktrees) */}
              <div>
                <label
                  htmlFor="parent"
                  className="block text-sm font-medium text-surface-300 mb-1"
                >
                  Parent Project
                </label>
                <input
                  type="text"
                  id="parent"
                  name="parent"
                  value={formData.parent}
                  onChange={handleChange}
                  placeholder="main-project"
                  className="w-full px-4 py-2 bg-surface-800 border border-surface-600 rounded-lg text-surface-100 placeholder-surface-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="text-xs text-surface-500 mt-1">
                  For worktrees, specify the parent project name
                </p>
              </div>

              {/* Build log */}
              <div>
                <label
                  htmlFor="build_log"
                  className="block text-sm font-medium text-surface-300 mb-1"
                >
                  Build Log Path
                </label>
                <input
                  type="text"
                  id="build_log"
                  name="build_log"
                  value={formData.build_log}
                  onChange={handleChange}
                  placeholder=".build.log"
                  className="w-full px-4 py-2 bg-surface-800 border border-surface-600 rounded-lg text-surface-100 placeholder-surface-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Test log */}
              <div>
                <label
                  htmlFor="test_log"
                  className="block text-sm font-medium text-surface-300 mb-1"
                >
                  Test Log Path
                </label>
                <input
                  type="text"
                  id="test_log"
                  name="test_log"
                  value={formData.test_log}
                  onChange={handleChange}
                  placeholder=".test-results.json"
                  className="w-full px-4 py-2 bg-surface-800 border border-surface-600 rounded-lg text-surface-100 placeholder-surface-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          )}

          {/* Error message */}
          {createProject.error && (
            <div className="p-3 rounded-lg bg-red-900/30 border border-red-700 text-red-200 text-sm">
              {createProject.error.message}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg border border-surface-600 text-surface-300 hover:bg-surface-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createProject.isPending}
              className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {createProject.isPending && (
                <Loader2 className="w-4 h-4 animate-spin" />
              )}
              Add Project
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
