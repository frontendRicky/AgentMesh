import { Cursor } from "@cursor/sdk";

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

let cachedModelId: string | null = null;

export async function resolveModelId(apiKey: string): Promise<string> {
  if (cachedModelId) return cachedModelId;

  const envOverride = process.env.A2A_MODEL_ID;
  if (envOverride) {
    cachedModelId = envOverride;
    return envOverride;
  }

  try {
    const models = await Cursor.models.list({ apiKey });
    const ids = models.map((m: { id: string }) => m.id);

    for (const pattern of PREFERRED_PATTERNS) {
      const found = ids.find((id) => pattern.test(id));
      if (found) {
        cachedModelId = found;
        return found;
      }
    }

    if (ids.length > 0) {
      cachedModelId = ids[0];
      return ids[0];
    }

    throw new Error("No models returned by Cursor.models.list()");
  } catch (err) {
    const fallback = "claude-4.6-sonnet";
    console.warn(
      `[model-config] models.list() 失败，使用兜底 model id: ${fallback}（错误：${(err as Error).message}）`,
    );
    cachedModelId = fallback;
    return fallback;
  }
}

export async function listAvailableModels(apiKey: string): Promise<string[]> {
  const models = await Cursor.models.list({ apiKey });
  return models.map((m: { id: string }) => m.id);
}
