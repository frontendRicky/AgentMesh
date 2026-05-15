import fs from 'node:fs';
import path from 'node:path';

const ROLES = ['pm', 'architect', 'developer', 'qa', 'controller', 'risk'] as const;
type Role = (typeof ROLES)[number];

export interface ModelPresets {
  overrides: Record<Role, string | null>;
  defaults: Record<Role, string>;
}

const DEFAULT_RECOMMEND: Record<Role, string> = {
  pm: 'claude-4.6-sonnet-medium-thinking',
  architect: 'claude-opus-4-7-thinking-high',
  developer: 'gpt-5.5',
  qa: 'claude-opus-4-7-thinking-high',
  controller: 'gpt-5.5-mini',
  risk: 'claude-opus-4-7-thinking-high',
};

/**
 * 解析 .ai-agents/agent-cards/model-overrides.md 中每个 ## <role> section 的 - [x] 勾选项
 *  - 每 section 取第一个 `- [x] <slug>`
 *  - slug 可能后接 ` -- comment`，截断在 `--` 前
 */
export function readModelPresets(projectRoot: string): ModelPresets {
  const file = path.join(projectRoot, '.ai-agents', 'agent-cards', 'model-overrides.md');
  const overrides: Record<Role, string | null> = {
    pm: null,
    architect: null,
    developer: null,
    qa: null,
    controller: null,
    risk: null,
  };
  if (!fs.existsSync(file)) {
    return { overrides, defaults: DEFAULT_RECOMMEND };
  }
  const raw = fs.readFileSync(file, 'utf8');
  const lines = raw.split('\n');
  let currentRole: Role | null = null;
  for (const line of lines) {
    const headingMatch = /^##\s+([a-z]+)\s*$/.exec(line);
    if (headingMatch) {
      const role = headingMatch[1] as Role;
      currentRole = (ROLES as readonly string[]).includes(role) ? role : null;
      continue;
    }
    if (!currentRole) continue;
    const checkMatch = /^\s*-\s*\[x\]\s+([^\s][^\n]*)$/i.exec(line);
    if (checkMatch && overrides[currentRole] === null) {
      const raw = (checkMatch[1] ?? '').trim();
      const slug = raw.split(/\s+--\s+/)[0]?.trim() ?? raw;
      overrides[currentRole] = slug || null;
    }
  }
  return { overrides, defaults: DEFAULT_RECOMMEND };
}
