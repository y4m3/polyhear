import { useState, useEffect } from "react";
import { RefreshCw, Settings, Plus, Ear } from "lucide-react";
import { useProjects, useSettings, useAutoRefresh } from "./hooks/useProjects";
import { ProjectCard } from "./components/ProjectCard";
import { ProjectDetail } from "./components/ProjectDetail";
import { ProjectForm } from "./components/ProjectForm";
import type { Project } from "./types/project";

export default function App() {
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);

  const { data: projectsData, isLoading, error, refetch } = useProjects();
  const { data: settings } = useSettings();

  // Auto-refresh based on settings
  const refreshInterval = (settings?.ui.refresh_interval ?? 30) * 1000;
  useAutoRefresh(refreshInterval);

  // Close modal on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setSelectedProject(null);
        setShowAddForm(false);
      }
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, []);

  const handleRefresh = () => {
    refetch();
  };

  const handleProjectClick = (project: Project) => {
    setSelectedProject(project.id);
  };

  const handleCloseDetail = () => {
    setSelectedProject(null);
  };

  const handleAddProject = () => {
    setShowAddForm(true);
  };

  const handleCloseForm = () => {
    setShowAddForm(false);
  };

  return (
    <div className="min-h-screen bg-surface-950">
      {/* Header */}
      <header className="border-b border-surface-800 bg-surface-900/50 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <Ear className="w-8 h-8 text-blue-400" />
              <h1 className="text-xl font-semibold text-surface-100">
                polyhear
              </h1>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleAddProject}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span className="hidden sm:inline">Add Project</span>
              </button>
              <button
                onClick={handleRefresh}
                disabled={isLoading}
                className="p-2 rounded-lg hover:bg-surface-800 text-surface-400 hover:text-surface-100 transition-colors disabled:opacity-50"
                title="Refresh"
              >
                <RefreshCw
                  className={`w-5 h-5 ${isLoading ? "animate-spin" : ""}`}
                />
              </button>
              <button
                className="p-2 rounded-lg hover:bg-surface-800 text-surface-400 hover:text-surface-100 transition-colors"
                title="Settings"
              >
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Error state */}
        {error && (
          <div className="mb-6 p-4 rounded-lg bg-red-900/30 border border-red-700 text-red-200">
            <p className="font-medium">Failed to load projects</p>
            <p className="text-sm mt-1">{error.message}</p>
          </div>
        )}

        {/* Loading state */}
        {isLoading && !projectsData && (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-8 h-8 text-surface-400 animate-spin" />
          </div>
        )}

        {/* Empty state */}
        {!isLoading && projectsData?.projects.length === 0 && (
          <div className="text-center py-12">
            <Ear className="w-16 h-16 text-surface-600 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-surface-300 mb-2">
              No projects registered
            </h2>
            <p className="text-surface-500 mb-6">
              Add your first Git project to start monitoring
            </p>
            <button
              onClick={handleAddProject}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Project
            </button>
          </div>
        )}

        {/* Project list */}
        {projectsData && projectsData.projects.length > 0 && (
          <div className="space-y-4">
            {projectsData.projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onClick={() => handleProjectClick(project)}
              />
            ))}
          </div>
        )}

        {/* Last updated */}
        {projectsData && (
          <div className="mt-6 text-center text-sm text-surface-500">
            Last updated:{" "}
            {new Date(projectsData.updated_at).toLocaleTimeString()}
          </div>
        )}
      </main>

      {/* Project detail modal */}
      {selectedProject && (
        <ProjectDetail
          projectId={selectedProject}
          onClose={handleCloseDetail}
        />
      )}

      {/* Add project form */}
      {showAddForm && <ProjectForm onClose={handleCloseForm} />}
    </div>
  );
}
