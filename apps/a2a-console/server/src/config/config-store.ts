import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// dev: src/config/ → ../../   prod: dist/config/ → ../../
const APP_ROOT = path.resolve(__dirname, '..', '..');
const CONFIG_FILE = path.join(APP_ROOT, '.a2a-console-config.json');

export interface AppConfig {
  project_root: string | null;
  poll_interval_ms: number;
}

const DEFAULT_CONFIG: AppConfig = {
  project_root: null,
  poll_interval_ms: 5000,
};

export function loadConfig(): AppConfig {
  if (!fs.existsSync(CONFIG_FILE)) return { ...DEFAULT_CONFIG };
  try {
    const raw = fs.readFileSync(CONFIG_FILE, 'utf8');
    const parsed = JSON.parse(raw) as Partial<AppConfig>;
    return {
      project_root:
        typeof parsed.project_root === 'string' && parsed.project_root.length > 0
          ? parsed.project_root
          : null,
      poll_interval_ms:
        typeof parsed.poll_interval_ms === 'number' && parsed.poll_interval_ms >= 1000
          ? parsed.poll_interval_ms
          : DEFAULT_CONFIG.poll_interval_ms,
    };
  } catch {
    return { ...DEFAULT_CONFIG };
  }
}

export function saveConfig(config: AppConfig): void {
  fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2), 'utf8');
}

export function getConfigFilePath(): string {
  return CONFIG_FILE;
}
