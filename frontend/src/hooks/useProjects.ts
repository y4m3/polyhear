import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type {
  Project,
  ProjectDetail,
  ProjectCreate,
  ProjectListResponse,
  SettingsResponse,
} from "../types/project";

const API_BASE = "/api";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Queries

export function useProjects() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: () => fetchJson<ProjectListResponse>(`${API_BASE}/projects`),
  });
}

export function useProject(id: string | null) {
  return useQuery({
    queryKey: ["project", id],
    queryFn: () => fetchJson<ProjectDetail>(`${API_BASE}/projects/${id}`),
    enabled: !!id,
  });
}

export function useSettings() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: () => fetchJson<SettingsResponse>(`${API_BASE}/settings`),
  });
}

// Mutations

export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (project: ProjectCreate) =>
      fetchJson<Project>(`${API_BASE}/projects`, {
        method: "POST",
        body: JSON.stringify(project),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      fetchJson<{ message: string }>(`${API_BASE}/projects/${id}`, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useRefreshProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      fetchJson<Project>(`${API_BASE}/projects/${id}/refresh`, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

// Auto-refresh hook
export function useAutoRefresh(intervalMs: number) {
  const queryClient = useQueryClient();

  return useQuery({
    queryKey: ["auto-refresh"],
    queryFn: async () => {
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
      return Date.now();
    },
    refetchInterval: intervalMs,
    enabled: intervalMs > 0,
  });
}
