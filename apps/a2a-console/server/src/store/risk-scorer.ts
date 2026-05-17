export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface EvaluatedPath {
  path: string;
  risk: RiskLevel;
}

export const RISK_RANK: Record<RiskLevel, number> = {
  low: 0,
  medium: 1,
  high: 2,
  critical: 3,
};

export const CRITICAL_PATH_RULES: RegExp[] = [
  /(^|\/)\.env($|[./-])/,
  /(^|\/)secrets\//,
  /(^|\/)\.github\//,
  /(^|\/)(auth|payment|billing)(\/|$)/,
  /\/(auth|payment|billing)\//,
];

export const HIGH_PATH_RULES: RegExp[] = [
  /(^|\/)package\.json$/,
  /(^|\/)package-lock\.json$/,
  /(^|\/)(vite|webpack)\.config\.[cm]?[jt]s$/,
  /(^|\/)tsconfig(\.[^/]+)?\.json$/,
  /(^|\/)(migrations|db\/migrations)\//,
  /(^|\/)(ci|deploy|scripts\/ci)\//,
  /(^|\/)(ci|deploy)\.[^/]+$/,
];

export const MEDIUM_PATH_RULES: RegExp[] = [
  /(^|\/)src\/store\//,
  /(^|\/)src\/hooks\//,
  /(^|\/)(pnpm-lock\.yaml|yarn\.lock)$/,
  /(^|\/)src\/(App|main|router|routes)\.[tj]sx?$/,
  /(^|\/)src\/router\//,
  /(^|\/)src\/routes\//,
];

export function scorePaths(paths: string[]): EvaluatedPath[] {
  return paths.map((path) => {
    const normalized = normalizePath(path);
    return { path: normalized, risk: scorePath(normalized) };
  });
}

export function scorePath(path: string): RiskLevel {
  if (matchesAny(CRITICAL_PATH_RULES, path)) return 'critical';
  if (matchesAny(HIGH_PATH_RULES, path)) return 'high';
  if (matchesAny(MEDIUM_PATH_RULES, path)) return 'medium';
  return 'low';
}

export function maxRiskLevel(items: EvaluatedPath[]): RiskLevel {
  return items.reduce<RiskLevel>((max, item) => {
    return RISK_RANK[item.risk] > RISK_RANK[max] ? item.risk : max;
  }, 'low');
}

function normalizePath(path: string): string {
  return path.trim().replaceAll('\\', '/').replace(/^\.\//, '').replace(/\/+/g, '/');
}

function matchesAny(rules: RegExp[], path: string): boolean {
  return rules.some((rule) => rule.test(path));
}
