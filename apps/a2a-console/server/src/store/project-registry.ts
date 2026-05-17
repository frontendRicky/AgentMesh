import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export type ProjectType = 'self_upgrade' | 'client_project' | 'generated_project' | 'maintenance';
export type ProjectAutomationMode = 'manual' | 'assisted' | 'selective_auto' | 'full_auto';

export interface Project {
  project_id: string;
  project_name: string;
  project_root: string;
  project_type: ProjectType;
  automation_mode: ProjectAutomationMode;
  max_parallel_runs: number;
  allowed_paths: string[];
  blocked_paths: string[];
  created_at: string;
  updated_at: string;
}

export interface ProjectInput {
  project_id?: string;
  project_name: string;
  project_root: string;
  project_type: ProjectType;
  automation_mode?: ProjectAutomationMode;
  max_parallel_runs?: number;
  allowed_paths?: string[];
  blocked_paths?: string[];
}

export type ProjectAddResult =
  | { ok: true; project: Project }
  | { ok: false; code: 'PROJECT_EXISTS' | 'SELF_UPGRADE_EXISTS'; message: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const APP_ROOT = path.resolve(__dirname, '..', '..');
const REGISTRY_FILE = path.join(APP_ROOT, '.projects-registry.json');
const DEFAULT_BLOCKED_PATHS = ['.env', '*.env', '.github/**', 'secrets/**'];

class ProjectRegistry {
  private readonly projects = new Map<string, Project>();

  constructor() {
    this.load();
  }

  add(input: ProjectInput): ProjectAddResult {
    const now = new Date().toISOString();
    const project: Project = {
      project_id: input.project_id ?? createProjectId(input.project_name),
      project_name: input.project_name,
      project_root: input.project_root,
      project_type: input.project_type,
      automation_mode: input.automation_mode ?? 'assisted',
      max_parallel_runs: input.max_parallel_runs ?? 2,
      allowed_paths: input.allowed_paths ?? [],
      blocked_paths: input.blocked_paths ?? DEFAULT_BLOCKED_PATHS,
      created_at: now,
      updated_at: now,
    };

    if (this.projects.has(project.project_id)) {
      return {
        ok: false,
        code: 'PROJECT_EXISTS',
        message: `Project already exists: ${project.project_id}`,
      };
    }

    if (
      project.project_type === 'self_upgrade'
      && this.list().some((item) => item.project_type === 'self_upgrade')
    ) {
      return {
        ok: false,
        code: 'SELF_UPGRADE_EXISTS',
        message: 'Only one self_upgrade project is allowed',
      };
    }

    this.projects.set(project.project_id, project);
    this.save();
    return { ok: true, project };
  }

  get(projectId: string): Project | null {
    return this.projects.get(projectId) ?? null;
  }

  update(projectId: string, patch: Partial<ProjectInput>): Project | null {
    const current = this.projects.get(projectId);
    if (!current) return null;
    const next: Project = {
      ...current,
      ...patch,
      project_id: current.project_id,
      created_at: current.created_at,
      updated_at: new Date().toISOString(),
    };
    this.projects.set(projectId, next);
    this.save();
    return next;
  }

  remove(projectId: string): boolean {
    const removed = this.projects.delete(projectId);
    if (removed) this.save();
    return removed;
  }

  list(): Project[] {
    return Array.from(this.projects.values()).sort((a, b) => {
      return a.project_name.localeCompare(b.project_name);
    });
  }

  save(): void {
    fs.writeFileSync(REGISTRY_FILE, JSON.stringify({ projects: this.list() }, null, 2), 'utf8');
  }

  private load(): void {
    if (!fs.existsSync(REGISTRY_FILE)) return;
    try {
      const raw = fs.readFileSync(REGISTRY_FILE, 'utf8');
      const parsed = JSON.parse(raw) as { projects?: unknown };
      if (!Array.isArray(parsed.projects)) return;
      for (const item of parsed.projects) {
        if (!isProject(item)) continue;
        this.projects.set(item.project_id, item);
      }
    } catch {
      this.projects.clear();
    }
  }
}

function createProjectId(name: string): string {
  const base = name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return base.length > 0 ? base.slice(0, 48) : `project-${Date.now()}`;
}

function isProject(value: unknown): value is Project {
  if (value === null || typeof value !== 'object') return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record['project_id'] === 'string'
    && typeof record['project_name'] === 'string'
    && typeof record['project_root'] === 'string'
    && isProjectType(record['project_type'])
    && isAutomationMode(record['automation_mode'])
    && typeof record['max_parallel_runs'] === 'number'
    && Array.isArray(record['allowed_paths'])
    && record['allowed_paths'].every((item) => typeof item === 'string')
    && Array.isArray(record['blocked_paths'])
    && record['blocked_paths'].every((item) => typeof item === 'string')
    && typeof record['created_at'] === 'string'
    && typeof record['updated_at'] === 'string'
  );
}

function isProjectType(value: unknown): value is ProjectType {
  return (
    value === 'self_upgrade'
    || value === 'client_project'
    || value === 'generated_project'
    || value === 'maintenance'
  );
}

function isAutomationMode(value: unknown): value is ProjectAutomationMode {
  return (
    value === 'manual'
    || value === 'assisted'
    || value === 'selective_auto'
    || value === 'full_auto'
  );
}

export const projectRegistry = new ProjectRegistry();
export const projectRegistryFilePath = REGISTRY_FILE;
