# Security

A2A Console 是单机本地工具，不引入鉴权。但有几条**硬约束**：

## 1. 不写 .ai-agents/**

- 路由层**不注册**任何写 `.ai-agents/**` 的接口
- `server/src/services/workspace-reader.ts` 仅暴露 read 函数
- 唯一 fs.write：`server/src/config/config-store.ts`，仅写 `apps/a2a-console/.a2a-console-config.json`

验证：

```bash
grep -rn "router.post\|router.put\|router.delete" apps/a2a-console/server/src/routes/
# 期望：仅 config.ts 命中

grep -rn "writeFile\|fs.write\|fs.append\|appendFile" apps/a2a-console/server/src/
# 期望：仅 config/config-store.ts 命中
```

## 2. 不调用 child_process / LLM

- 无任何 `child_process.spawn / exec`
- 无任何 LLM SDK / fetch 到外网

验证：

```bash
grep -rn "child_process\|spawn(\|exec(" apps/a2a-console/
# 期望：零命中
```

## 3. Path traversal 防护

`server/src/lib/path-guard.ts` 单点防护：

```ts
const real = fs.realpathSync(path.resolve(root, requested));
const realRoot = fs.realpathSync(root);
if (real !== realRoot && !real.startsWith(realRoot + path.sep)) {
  throw new PathTraversalError();
}
```

防护场景：

- `?path=../../../etc/passwd` → 拒绝
- `?path=..%2F..%2Fetc%2Fpasswd` → 拒绝（express 自动 decode 后 path 含 `..`）
- `?path=/abs/path` → 拒绝（path.resolve 后会越界）
- 通过 symlink 跨 root → realpath 揭穿后拒绝
- 含 null byte 路径 → Node 自带拒绝

## 4. CORS

仅 `origin: http://localhost:5173`，仅 GET + 单 POST `/config/project-root`。

## 5. Server 启动校验

- 启动时检查 `apps/a2a-console/.a2a-console-config.json` 是否存在；不存在则 project_root = null
- 任何依赖 project_root 的 GET 在 project_root = null 时返回 400 PROJECT_ROOT_MISSING
