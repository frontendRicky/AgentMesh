import { Cursor } from "@cursor/sdk";

import {
  AGENT_ALIASES,
  AGENT_MODEL_CONFIG,
  type AgentAlias,
} from "../agents-model.config.js";

/**
 * 偏好顺序：sonnet 4.6 系列 → 其他 sonnet → composer-2 兜底。
 * 实际可用 model id 通过 Cursor.models.list() 拉取确认。
 */
const PREFERRED_PATTERNS = [
  /^claude.*4\.?6.*sonnet/i,
  /^claude.*sonnet.*4\.?6/i,
  /sonnet.*4\.?6/i,
  /^claude.*sonnet/i,
  /^composer-2$/i,
];

const FALLBACK_MODEL_ID = "claude-4.6-sonnet";

const ENV_KEY_BY_ALIAS: Record<AgentAlias, string> = {
  pm: "A2A_MODEL_PM",
  architect: "A2A_MODEL_ARCHITECT",
  developer: "A2A_MODEL_DEVELOPER",
  qa: "A2A_MODEL_QA",
  controller: "A2A_MODEL_CONTROLLER",
};

let cachedAutoModelId: string | null = null;

/**
 * 解析"自动选择"层（Cursor.models.list 偏好匹配 + 兜底）。
 * 这一层会被缓存并在所有 agent 间共享。
 */
async function resolveAutoModelId(apiKey: string): Promise<string> {
  if (cachedAutoModelId) return cachedAutoModelId;

  try {
    const models = await Cursor.models.list({ apiKey });
    const ids = models.map((m: { id: string }) => m.id);

    for (const pattern of PREFERRED_PATTERNS) {
      const found = ids.find((id) => pattern.test(id));
      if (found) {
        cachedAutoModelId = found;
        return found;
      }
    }

    if (ids.length > 0) {
      cachedAutoModelId = ids[0];
      return ids[0];
    }

    throw new Error("No models returned by Cursor.models.list()");
  } catch (err) {
    console.warn(
      `[model-config] models.list() 失败，使用兜底 model id: ${FALLBACK_MODEL_ID}（错误：${(err as Error).message}）`,
    );
    cachedAutoModelId = FALLBACK_MODEL_ID;
    return FALLBACK_MODEL_ID;
  }
}

export type ModelSource =
  | "cli_override"
  | "agent_env"
  | "config_file"
  | "global_env"
  | "auto_resolved";

export interface ResolvedModel {
  agent: AgentAlias;
  modelId: string;
  source: ModelSource;
}

/**
 * 为某个 agent 解析最终生效的 model id。
 *
 * 优先级（高 → 低）：
 *   1. cliOverride：调用方显式传入（CLI --model）
 *   2. 单 agent 环境变量 A2A_MODEL_<AGENT>
 *   3. agents-model.config.ts 中的 AGENT_MODEL_CONFIG
 *   4. 全局环境变量 A2A_MODEL_ID（向后兼容）
 *   5. Cursor.models.list() 自动选择 → FALLBACK_MODEL_ID
 */
export async function resolveModelIdForAgent(
  agent: AgentAlias,
  apiKey: string,
  cliOverride?: string,
): Promise<ResolvedModel> {
  if (cliOverride && cliOverride.trim()) {
    return { agent, modelId: cliOverride.trim(), source: "cli_override" };
  }

  const agentEnv = process.env[ENV_KEY_BY_ALIAS[agent]];
  if (agentEnv && agentEnv.trim()) {
    return { agent, modelId: agentEnv.trim(), source: "agent_env" };
  }

  const fromConfig = AGENT_MODEL_CONFIG[agent];
  if (fromConfig && fromConfig.trim()) {
    return { agent, modelId: fromConfig.trim(), source: "config_file" };
  }

  const globalEnv = process.env.A2A_MODEL_ID;
  if (globalEnv && globalEnv.trim()) {
    return { agent, modelId: globalEnv.trim(), source: "global_env" };
  }

  const autoId = await resolveAutoModelId(apiKey);
  return { agent, modelId: autoId, source: "auto_resolved" };
}

/**
 * 一次性解析所有 agent 的有效模型分配，便于 ./model show 一行输出。
 */
export async function resolveAllAgentModels(
  apiKey: string,
  cliOverrides: Partial<Record<AgentAlias, string>> = {},
): Promise<ResolvedModel[]> {
  const out: ResolvedModel[] = [];
  for (const alias of AGENT_ALIASES) {
    out.push(await resolveModelIdForAgent(alias, apiKey, cliOverrides[alias]));
  }
  return out;
}

export async function listAvailableModels(apiKey: string): Promise<string[]> {
  const models = await Cursor.models.list({ apiKey });
  return models.map((m: { id: string }) => m.id);
}

/**
 * @deprecated 旧入口，保留向后兼容（外部脚本可能直接调用）。
 * 等同于 resolveModelIdForAgent("developer", apiKey).modelId 的"全局共用"语义：
 * 即只走 A2A_MODEL_ID + auto。新代码应改用 resolveModelIdForAgent。
 */
export async function resolveModelId(apiKey: string): Promise<string> {
  const globalEnv = process.env.A2A_MODEL_ID;
  if (globalEnv && globalEnv.trim()) return globalEnv.trim();
  return resolveAutoModelId(apiKey);
}
