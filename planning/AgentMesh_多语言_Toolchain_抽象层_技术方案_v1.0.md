# AgentMesh 多语言 Toolchain 抽象层 — 技术方案

**版本：v1.0 · 2026-05-18**
**用途：作为 OS-2026-009 的输入；让 AgentMesh 从"只能升级前端项目"演进为"能升级 Python/Java/Rust/Go 等多语言项目（含自身 a2a_runtime）"。**
**前置依赖：OS-2026-007（Context Pack + Sandbox + Test Runner）+ OS-2026-008（Runner 实接 + Auto Orchestrator）必须先完成。**

---

## 0. 为什么需要这一层

### 0.1 现状的隐藏前提

OS-2026-007 设计完成后，AgentMesh 的执行层有 4 个模块默认**只懂 nodejs**：

| 模块 | 当前硬编码 | 多语言时的问题 |
|---|---|---|
| Test Runner | `npm run typecheck/lint/build` | Python 用 `mypy/ruff/pytest`，Java 用 `mvn verify`，Rust 用 `cargo check` |
| Sandbox apply | unified text diff | Python `__pycache__/`、Java `*.class`、Rust `target/` 是二进制 |
| risk-scorer | 硬编码 `package.json`/`auth/` | Python 高风险是 `setup.py`/`requirements.txt`，Java 是 `pom.xml`/`build.gradle` |
| Context Pack | `file_path` + 摘要 | Python venv / Java classpath / Go modules 没体现 |

**结论：不做这一层重构，下一次想用 AgentMesh 改 `a2a_runtime/*` (Python) 时基本要推倒 Test Runner / Sandbox 重做。**

### 0.2 目标

把 AgentMesh 从"前端专用执行平台"升级为：

> **语言无关的 A2A 自动编程执行平台**：通过统一 ToolchainAdapter 抽象层，让 Test Runner / Sandbox / risk-scorer / Context Pack 全部"问 Adapter 该用什么命令"，而不是"自己硬编码 npm"。

### 0.3 核心原则

1. **零回归**：OS-2026-007 已交付的前端能力 100% 兼容，nodejs 项目继续按现有方式工作
2. **只追加不修改**：现有 schema 只 append 字段，现有路由保持向后兼容
3. **接口先行**：先定义 IToolchainAdapter，再逐步实接各语言
4. **Detector 自动识别**：用户不需要手动配每个项目的 toolchain
5. **白名单原则**：任何 child_process.spawn 必须先通过 Adapter 校验

---

## 1. 整体架构

### 1.1 当前架构（OS-2026-007 交付后）

```
┌─────────────────────────────────────────┐
│  Test Runner Route (/api/a2a/test)      │
│  ├─ child_process.spawn('npm', [...])  │ ← 硬编码 npm
│  └─ suites: ['typecheck','lint','build'] │ ← 硬编码 3 个
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  Sandbox Store                          │
│  ├─ generateUnifiedDiff(old, new, path) │ ← 默认 text diff
│  └─ apply() 直接 fs.writeFileSync       │ ← 不处理二进制
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  Risk Scorer                            │
│  ├─ CRITICAL = [/.env/, /secrets\//]    │ ← 硬编码
│  └─ HIGH = [/package\.json/, ...]       │ ← 硬编码 nodejs
└─────────────────────────────────────────┘
```

### 1.2 目标架构（OS-2026-009 交付后）

```
┌─────────────────────────────────────────┐
│  Test Runner Route (/api/a2a/test)      │
│  └─ ToolchainAdapter.runTest(           │
│       project_id, suite                 │
│     )                                   │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────────────────┐
│              ToolchainAdapter Registry              │
│  ┌─────────────────────────────────────────────┐  │
│  │  resolve(project_id) → IToolchainAdapter    │  │
│  └─────────────────────────────────────────────┘  │
│            ↓                                       │
│  ┌──────────────┬──────────────┬──────────────┐  │
│  │ NodejsAdapter│PythonAdapter │ JavaAdapter  │  │
│  │ (npm/pnpm)   │ (pip/poetry) │ (mvn/gradle) │  │
│  └──────────────┴──────────────┴──────────────┘  │
└─────────────────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│        ProjectRegistry                  │
│  Project.runtime_profile = 'python'    │
│  Project.toolchain = {                  │
│    package_manager: 'poetry',           │
│    test_command: 'pytest',              │
│    ...                                  │
│  }                                      │
└─────────────────────────────────────────┘
```

### 1.3 数据流

```
1. 用户注册项目 → POST /api/a2a/projects { project_root: '/path/to/python-app' }
2. ProjectRegistry 内部调 Detector.detect(project_root)
3. Detector 扫描根目录文件特征 → 推断 runtime_profile + toolchain
4. Project 写入 Registry，含 runtime_profile/toolchain 字段
5. 用户触发 Test → POST /api/a2a/test/run { project_id, suite: 'typecheck' }
6. Test Runner 调 ToolchainAdapter.resolve(project_id) → 返回 PythonAdapter
7. PythonAdapter.getCommand('typecheck') → 'mypy .' 
8. child_process.spawn(...)，结果归一化后回写 RunSession
```

---

## 2. 核心模块设计

### 2.1 Project schema 扩展（向后兼容追加）

**文件**：`apps/a2a-console/packages/contract/src/projects.ts`

```ts
// 当前
export const projectSchema = z.object({
  project_id, project_name, project_root,
  project_type: z.enum(['self_upgrade','client_project',...]),
  automation_mode, max_parallel_runs, allowed_paths, blocked_paths,
  created_at, updated_at,
});

// OS-2026-009 追加（全部 optional，旧 client 零回归）
runtime_profile: z.enum([
  'nodejs','python','java','rust','go','mixed','unknown'
]).default('unknown'),

toolchain: z.object({
  package_manager: z.enum([
    'npm','pnpm','yarn','pip','poetry','uv',
    'maven','gradle','cargo','go'
  ]).nullable().default(null),
  workspace_root: z.string().optional(),
  test_command: z.string().nullable().default(null),
  build_command: z.string().nullable().default(null),
  lint_command: z.string().nullable().default(null),
  typecheck_command: z.string().nullable().default(null),
  install_command: z.string().nullable().default(null),
  detected_at: z.string().optional(),
  detection_confidence: z.enum(['high','medium','low']).default('medium'),
}).optional(),

language_specific_blocked_paths: z.array(z.string()).default([]),
  // 例：Python 项目自动加 ['__pycache__/**', '.venv/**', '*.pyc']
  //     Java 项目自动加 ['target/**', '*.class', '.gradle/**']
  //     Rust 项目自动加 ['target/**', 'Cargo.lock']
```

### 2.2 IToolchainAdapter 接口

**文件**：`apps/a2a-console/server/src/toolchain/base.ts`

```ts
export interface IToolchainAdapter {
  readonly name: string;                    // 'nodejs' / 'python' / 'java' / ...
  readonly supported_suites: TestSuite[];   // ['typecheck','lint','build','test'] etc

  // 命令解析
  getCommand(suite: TestSuite): {
    command: string;        // 'mypy' / 'npm' / 'mvn' / ...
    args: string[];         // ['.'] / ['run', 'typecheck'] / ['verify','-DskipTests']
    cwd_subpath?: string;   // 工作目录可在 project_root 下的子路径
    timeout_ms: number;     // 默认 30000，可按 suite 调整
  } | null;                 // null = 此 suite 该语言不支持

  // 文件分类（diff 算法分流用）
  classifyFile(relative_path: string): 'text' | 'binary' | 'generated' | 'ignored';
  // 例：Python 'foo.py' → text, '__pycache__/x.pyc' → ignored
  //     Java 'Foo.java' → text, 'target/Foo.class' → generated

  // 高风险路径
  getHighRiskPaths(): { critical: RegExp[]; high: RegExp[]; medium: RegExp[] };
  // 例：Python → critical: [/.env/], high: [/pyproject\.toml/, /setup\.py/]

  // 默认 blocked paths（语言特定的运行态文件）
  getDefaultBlockedPaths(): string[];
  // 例：Python → ['__pycache__/**', '.venv/**', '*.pyc']

  // Context Pack 摘要（toolchain 维度）
  getToolchainSummary(project_root: string): Promise<{
    package_manager: string;
    main_deps_count: number;
    dev_deps_count: number;
    lockfile_hash?: string;
    notes: string[];      // 给 Agent 看的人类可读摘要
  }>;
}
```

### 2.3 Adapter 实现清单

| Adapter | 文件 | 实现优先级 | 触发场景 |
|---|---|---|---|
| **NodejsAdapter** | `nodejs-toolchain.ts` | P0 | 从 OS-2026-007 现有逻辑迁移 |
| **PythonAdapter** | `python-toolchain.ts` | P0 | 让 AgentMesh 升级 a2a_runtime |
| **JavaAdapter** | `java-toolchain.ts` | P1 | 客户 Java 项目（如果你有） |
| **RustAdapter** | `rust-toolchain.ts` | P2 | 性能敏感的客户项目 |
| **GoAdapter** | `go-toolchain.ts` | P2 | 微服务客户项目 |
| **MixedAdapter** | `mixed-toolchain.ts` | P3 | monorepo 多语言并存 |

### 2.4 各 Adapter 命令规则（关键参考）

#### NodejsAdapter（迁移自 OS-2026-007）

```ts
typecheck: { command: 'npm', args: ['run', 'typecheck'], timeout_ms: 30000 }
lint:      { command: 'npm', args: ['run', 'lint'], timeout_ms: 30000 }
build:     { command: 'npm', args: ['run', 'build'], timeout_ms: 60000 }
test:      { command: 'npm', args: ['test'], timeout_ms: 120000 }

classifyFile:
  *.ts, *.tsx, *.js, *.jsx, *.json, *.md → text
  *.png, *.jpg, *.ico → binary
  node_modules/**, dist/**, .next/** → ignored

high_risk_paths:
  critical: [/.env/, /\.github\//]
  high:     [/package\.json$/, /package-lock\.json$/, /tsconfig\.json$/]
  medium:   [/src\/store\//, /src\/hooks\//]
```

#### PythonAdapter

```ts
typecheck: { command: 'mypy', args: ['.', '--ignore-missing-imports'], timeout_ms: 45000 }
lint:      { command: 'ruff', args: ['check', '.'], timeout_ms: 30000 }
build:     null  // Python 一般不需要 build
test:      { command: 'pytest', args: ['-x'], timeout_ms: 120000 }

# 如果用 poetry，命令会被自动包装：
# 'mypy .' → 'poetry run mypy .'

classifyFile:
  *.py, *.pyi, *.toml, *.cfg, *.ini → text
  *.pyc, *.so, *.whl → binary
  __pycache__/**, .venv/**, .pytest_cache/**, dist/**, *.egg-info/** → ignored

high_risk_paths:
  critical: [/.env/, /secrets/]
  high:     [/pyproject\.toml/, /setup\.py/, /setup\.cfg/, /requirements.*\.txt/]
  medium:   [/conftest\.py/, /__init__\.py/]
```

#### JavaAdapter

```ts
typecheck: { command: 'mvn', args: ['compile', '-DskipTests'], timeout_ms: 90000 }
lint:      { command: 'mvn', args: ['checkstyle:check'], timeout_ms: 60000 }
build:     { command: 'mvn', args: ['package', '-DskipTests'], timeout_ms: 180000 }
test:      { command: 'mvn', args: ['test'], timeout_ms: 300000 }

# gradle 项目自动切换：
# 'mvn compile' → './gradlew compileJava'

classifyFile:
  *.java, *.xml, *.properties, *.yaml → text
  *.class, *.jar, *.war → binary
  target/**, build/**, .gradle/** → ignored

high_risk_paths:
  critical: [/.env/, /application.*\.properties/]
  high:     [/pom\.xml/, /build\.gradle/, /settings\.gradle/]
  medium:   [/src\/main\/java\/.*\/(Auth|Security|Payment)/]
```

#### RustAdapter

```ts
typecheck: { command: 'cargo', args: ['check'], timeout_ms: 60000 }
lint:      { command: 'cargo', args: ['clippy', '--', '-D', 'warnings'], timeout_ms: 90000 }
build:     { command: 'cargo', args: ['build'], timeout_ms: 180000 }
test:      { command: 'cargo', args: ['test'], timeout_ms: 180000 }

classifyFile:
  *.rs, *.toml → text
  *.so, *.dylib, *.dll → binary
  target/**, Cargo.lock → ignored (Cargo.lock 通常 gitignore 但实际是 text，分类为 ignored 让 diff 不显示)

high_risk_paths:
  critical: [/.env/]
  high:     [/Cargo\.toml/, /Cargo\.lock/]
  medium:   [/src\/main\.rs/, /src\/lib\.rs/]
```

#### GoAdapter

```ts
typecheck: { command: 'go', args: ['vet', './...'], timeout_ms: 30000 }
lint:      { command: 'golangci-lint', args: ['run'], timeout_ms: 60000 }
build:     { command: 'go', args: ['build', './...'], timeout_ms: 90000 }
test:      { command: 'go', args: ['test', './...'], timeout_ms: 120000 }

classifyFile:
  *.go, *.mod, *.sum → text
  vendor/**, bin/**, *.exe → ignored / binary

high_risk_paths:
  critical: [/.env/]
  high:     [/go\.mod/, /go\.sum/]
```

### 2.5 Toolchain Registry

**文件**：`apps/a2a-console/server/src/toolchain/registry.ts`

```ts
export class ToolchainRegistry {
  private adapters: Map<string, IToolchainAdapter> = new Map();

  constructor() {
    this.adapters.set('nodejs', new NodejsAdapter());
    this.adapters.set('python', new PythonAdapter());
    this.adapters.set('java', new JavaAdapter());
    // ... 按优先级注册
  }

  resolve(project: Project): IToolchainAdapter {
    const profile = project.runtime_profile ?? 'unknown';
    const adapter = this.adapters.get(profile);
    if (adapter) return adapter;
    // 兜底：尝试 detect 一次
    return this.adapters.get('nodejs')!;  // 默认 nodejs 保证 OS-2026-007 行为
  }

  list(): string[] {
    return Array.from(this.adapters.keys());
  }
}

export const toolchainRegistry = new ToolchainRegistry();
```

### 2.6 Detector：自动识别 runtime_profile

**文件**：`apps/a2a-console/server/src/toolchain/detector.ts`

```ts
export interface DetectionResult {
  runtime_profile: RuntimeProfile;
  toolchain: ToolchainConfig;
  confidence: 'high' | 'medium' | 'low';
  evidence: string[];  // 命中规则的人类可读说明
}

export async function detectProject(project_root: string): Promise<DetectionResult> {
  const files = await fs.readdir(project_root);
  const evidence: string[] = [];

  // 规则按特异性排序，第一个命中即返回
  if (files.includes('pyproject.toml')) {
    const content = await fs.readFile(`${project_root}/pyproject.toml`, 'utf-8');
    if (content.includes('[tool.poetry]')) {
      evidence.push('发现 pyproject.toml [tool.poetry] 段');
      return {
        runtime_profile: 'python',
        toolchain: { package_manager: 'poetry', ... },
        confidence: 'high',
        evidence,
      };
    }
    if (content.includes('[tool.uv]')) { ... }
  }

  if (files.includes('requirements.txt')) {
    evidence.push('发现 requirements.txt');
    return { runtime_profile: 'python', toolchain: { package_manager: 'pip' }, confidence: 'medium', evidence };
  }

  if (files.includes('package.json')) {
    if (files.includes('pnpm-lock.yaml')) {
      return { ..., toolchain: { package_manager: 'pnpm' } };
    }
    if (files.includes('yarn.lock')) {
      return { ..., toolchain: { package_manager: 'yarn' } };
    }
    return { ..., toolchain: { package_manager: 'npm' } };
  }

  if (files.includes('pom.xml')) {
    return { runtime_profile: 'java', toolchain: { package_manager: 'maven' }, ... };
  }
  if (files.includes('build.gradle') || files.includes('build.gradle.kts')) {
    return { runtime_profile: 'java', toolchain: { package_manager: 'gradle' }, ... };
  }

  if (files.includes('Cargo.toml')) {
    return { runtime_profile: 'rust', toolchain: { package_manager: 'cargo' }, ... };
  }

  if (files.includes('go.mod')) {
    return { runtime_profile: 'go', toolchain: { package_manager: 'go' }, ... };
  }

  // 检测 monorepo / mixed
  const detected_profiles = [...];
  if (detected_profiles.length > 1) {
    return { runtime_profile: 'mixed', ... };
  }

  return { runtime_profile: 'unknown', toolchain: null, confidence: 'low', evidence };
}
```

### 2.7 各模块的改造点

#### 2.7.1 Test Runner（迁移）

**当前**（OS-2026-007）：

```ts
const PACKAGE_MANAGER = 'npm';
const command = PACKAGE_MANAGER;
const args = ['run', suite];
spawn(command, args, ...);
```

**迁移后**（OS-2026-009）：

```ts
const project = await projectRegistry.get(project_id);
const adapter = toolchainRegistry.resolve(project);
const cmd = adapter.getCommand(suite);
if (!cmd) return { ok: false, error: 'SUITE_NOT_SUPPORTED', toolchain: adapter.name };
spawn(cmd.command, cmd.args, { cwd: project.project_root, timeout: cmd.timeout_ms });
```

#### 2.7.2 Sandbox diff（增强）

**当前**：

```ts
function generateUnifiedDiff(oldText, newText, path) { ... }
```

**迁移后**：

```ts
function generateDiff(oldContent: Buffer, newContent: Buffer, path: string, adapter: IToolchainAdapter) {
  const classification = adapter.classifyFile(path);
  if (classification === 'ignored') return null;  // 跳过 lockfile 等
  if (classification === 'binary' || classification === 'generated') {
    return {
      type: 'binary_diff',
      old_hash: hash(oldContent),
      new_hash: hash(newContent),
      size_delta: newContent.length - oldContent.length,
    };
  }
  return { type: 'unified_text_diff', diff: generateUnifiedDiff(oldContent.toString(), newContent.toString(), path) };
}
```

#### 2.7.3 Risk Scorer（按 toolchain 扩展）

**当前**：

```ts
export const HIGH = [/package\.json/, /vite\.config\.ts/];
```

**迁移后**：

```ts
export function scorePath(path: string, adapter: IToolchainAdapter): RiskLevel {
  const { critical, high, medium } = adapter.getHighRiskPaths();
  if (critical.some(re => re.test(path))) return 'critical';
  if (high.some(re => re.test(path))) return 'high';
  if (medium.some(re => re.test(path))) return 'medium';
  return 'low';
}
```

#### 2.7.4 Context Pack（追加 toolchain item）

新增 item type：

```ts
items: z.array(z.object({
  type: z.enum([
    'requirement','prd','file_path','file_summary',
    'log_summary','diff','artifact_summary',
    'toolchain_summary',  // ← OS-2026-009 追加
  ]),
  ...
}))
```

PythonAdapter.getToolchainSummary 实现示例：

```ts
async getToolchainSummary(project_root) {
  const pyproject = await fs.readFile(`${project_root}/pyproject.toml`, 'utf-8');
  const main_deps = countDeps(pyproject, 'dependencies');
  return {
    package_manager: 'poetry',
    main_deps_count: main_deps,
    dev_deps_count: ...,
    lockfile_hash: await hash(`${project_root}/poetry.lock`),
    notes: [
      `Python 项目，poetry 管理`,
      `主依赖 ${main_deps} 个`,
      `本期 Test Runner 默认运行 mypy + ruff + pytest`,
    ],
  };
}
```

---

## 3. 实施顺序（推荐分 4 个 OS）

### OS-2026-009：抽象层 + Nodejs 迁移（P0）

**目标**：建立 ToolchainAdapter 接口，把 Nodejs 逻辑从 Test Runner / Sandbox / risk-scorer 抽出来，零回归。

| 模块 | 改动 | 文件数估算 |
|---|---|---|
| contract/projects.ts | Project schema append 3 字段 | 1 |
| contract/test.ts | TestResult append toolchain 字段 | 1 |
| server/toolchain/base.ts | IToolchainAdapter interface | 1 (new) |
| server/toolchain/registry.ts | Registry 单例 | 1 (new) |
| server/toolchain/detector.ts | 自动检测 | 1 (new) |
| server/toolchain/nodejs-toolchain.ts | 从现有逻辑迁移 | 1 (new) |
| server/store/test-runner.ts | 改为通过 adapter 调用 | 1 (modify) |
| server/store/sandbox-store.ts | 改为通过 adapter 分类文件 | 1 (modify) |
| server/store/risk-scorer.ts | 接收 adapter 参数 | 1 (modify) |
| server/routes/projects.ts | POST 时调 detector | 1 (modify) |
| client/Projects.tsx | 展示 runtime_profile 列 | 1 (modify) |

**总计**：~11 个文件，1 轮 Codex 可完成。

**验收**：所有 nodejs 项目继续按 OS-2026-007 行为工作；新增"运行时"列在 Projects 页面展示 'nodejs'；POST /api/a2a/projects 自动 detect。

### OS-2026-010：Python Adapter 实接（P0）

**目标**：让 AgentMesh 能改 a2a_runtime 的 Python 代码。

| 模块 | 改动 | 文件数估算 |
|---|---|---|
| server/toolchain/python-toolchain.ts | PythonAdapter 实现 | 1 (new) |
| server/toolchain/registry.ts | 注册 PythonAdapter | 1 (modify) |
| contract/test.ts | TestSuite 追加 'pytest' | 1 (modify) |
| server/store/test-runner.ts | 超时配置按 suite | 1 (modify) |
| server/store/risk-scorer.ts | Python 路径常量集中 | 1 (modify) |
| server/store/sandbox-store.ts | 处理 *.pyc 二进制 | 1 (modify) |
| 测试 | 用 a2a_runtime 跑一次 sandbox + test | 0 |

**总计**：~6 个文件，1 轮 Codex 可完成。

**验收**：Project 注册 `/path/to/a2a_runtime/` 后，runtime_profile=python 自动识别；POST /test/run suite=typecheck 跑 mypy；Sandbox init 复制 .py 文件，忽略 __pycache__。

**这一步完成后，AgentMesh 第一次能用 A2A 流程升级自身 Python Runtime。**

### OS-2026-011：Java Adapter（P1，按需）

参考 PythonAdapter 模式，新增 JavaAdapter。**前提**：你确实有 Java 项目要升级。

### OS-2026-012：Rust + Go Adapter（P2）

合并到一个 OS，因为两者实现相似。

### OS-2026-013（可选）：MixedAdapter + Monorepo 支持

让一个 project_root 下同时存在 Python 后端 + Nodejs 前端的项目能被正确处理。**最复杂**，建议有真实需求再做。

---

## 4. 关键设计决策

### 4.1 为什么 Adapter 在 server 而不在 contract

- contract 只放数据 schema（zod），不放执行逻辑
- Adapter 涉及 child_process / fs / 路径计算，必须在 server
- 未来如果要在 a2a_runtime (Python) 里也用，重新实现一份即可，contract 保持单一真相源

### 4.2 为什么 Detector 在 server 而不在前端

- 前端无法读用户文件系统
- POST /api/a2a/projects 时 server 已经知道 project_root，detect 一次写入 Registry
- 前端可以提供"重新检测"按钮（调 PATCH /projects/:id/redetect）

### 4.3 为什么 toolchain 字段是 optional

- 旧 Project（OS-2026-007 时注册的）没有这个字段，必须能继续工作
- runtime_profile=unknown 时 fallback 到 NodejsAdapter（向下兼容）
- 用户可以手动指定（覆盖 Detector 结果）

### 4.4 为什么不直接用 LangChain / autogen 现成框架

- 它们假设你能调真实 LLM，AgentMesh 现阶段 Runner 是 stub
- 它们的 Tool 抽象是给 LLM 用的，AgentMesh 的 Adapter 是给执行层用的
- 引入大依赖违反 OS §15 "不要做清单"第 7 条
- 自己写 ~600 行接口 + 5 个 Adapter 实现可控、可审计

### 4.5 为什么 classify 文件分 4 类（text/binary/generated/ignored）

- text：unified diff 友好，全文比对
- binary：用 hash 对比，不展示内容
- generated：编译产物（如 *.class），diff 时跳过（即使存在也不算"真实改动"）
- ignored：lockfile、cache，apply 时不写回

### 4.6 安全：spawn 注入防御

每个 Adapter 的 `getCommand` 返回值是**纯结构化数据**：

```ts
{ command: 'mypy', args: ['.', '--ignore-missing-imports'] }
```

spawn 时**不允许 shell**：

```ts
spawn(cmd.command, cmd.args, { shell: false, ... });
```

这样即使 Adapter 实现有 bug，也无法通过 args 注入任意 shell 命令。

---

## 5. 风险与缓解

| Risk | 概率 | 影响 | 缓解 |
|---|---|---|---|
| Detector 误识别 | 中 | 跑错命令 | 提供"手动覆盖" UI；confidence=low 时 Console 提示用户确认 |
| Python 项目没装 mypy/ruff | 高 | spawn 报 ENOENT | Adapter 校验命令存在性 → 返回 TOOL_NOT_INSTALLED 友好提示 |
| Java 命令耗时长（mvn 90s+） | 高 | 30s 超时不够 | 各 suite 独立 timeout，Java build 默认 180s |
| Detector 触发文件系统漫游 | 低 | 大目录扫描慢 | 只读 project_root 第一层文件，不递归 |
| poetry/uv 命令包装 | 中 | 命令前缀不对 | Adapter 内部根据 package_manager 自动加 'poetry run' 前缀 |
| 多语言并存 (monorepo) | 中 | runtime_profile=mixed 不知道用哪个 | MixedAdapter 支持 cwd_subpath，可以让 sub-toolchain 局部生效 |
| Spawn 防注入 | 低 | 命令注入风险 | shell: false 强制；args 必须来自 Adapter 静态返回 |

---

## 6. 验收标准（OS-2026-009 主任务）

| AC | 验收点 | 验收方式 |
|---|---|---|
| AC-01 | NodejsAdapter 实现 IToolchainAdapter 全部方法 | typecheck |
| AC-02 | Detector 识别 package.json + pnpm-lock → nodejs/pnpm | unit test |
| AC-03 | Detector 识别 pyproject.toml [tool.poetry] → python/poetry | unit test |
| AC-04 | Detector 识别 pom.xml → java/maven | unit test |
| AC-05 | Project schema 含 runtime_profile/toolchain（optional） | typecheck |
| AC-06 | POST /projects 自动调 detector 并写入 runtime_profile | curl |
| AC-07 | PATCH /projects/:id/redetect 可强制重新检测 | curl |
| AC-08 | Test Runner 通过 adapter.getCommand 取命令，不再硬编码 npm | grep + curl |
| AC-09 | OS-2026-007 已交付的 typecheck/lint/build 行为零回归 | npm test 主项目 |
| AC-10 | Sandbox.classifyFile 对 *.pyc 返回 'ignored'，*.ts 返回 'text' | unit test |
| AC-11 | RiskScorer 接受 adapter 参数，未传时 fallback 到 NodejsAdapter | unit test |
| AC-12 | Projects.tsx 展示 runtime_profile 列；rerefresh 按钮可触发 redetect | 浏览器手测 |
| AC-13 | 不引入新 npm dependency | package.json diff |

---

## 7. 与已有任务的关系

### 依赖

- **OS-2026-007**：Test Runner / Sandbox / risk-scorer 必须先存在，OS-2026-009 是抽象重构
- **OS-2026-008**（Runner 实接）：完成后，Auto Orchestrator 可以根据 toolchain 给 Agent 不同的 Prompt

### 解锁

- **OS-2026-010**：Python Adapter 实接 → AgentMesh 第一次能用 A2A 改自身 Runtime
- **OS-2026-011/12**：按需扩展 Java/Rust/Go
- **OS-2026-014**（潜在）：Multi-Project Auto Upgrade — 用 AgentMesh 同时升级多个不同语言项目

### 不阻塞

- 任何业务任务（生成新前端项目、客户项目维护）
- 当前 nodejs 项目继续按 OS-2026-007 工作

---

## 8. 战略意义

完成 OS-2026-009 + OS-2026-010 后，AgentMesh 真正成为：

> **跨语言的 A2A 自动编程操作系统**

意味着：

1. **第一次能升级自身 Python Runtime**（演进文档 Phase 6 自升级闭环的前提）
2. **第一次能服务非前端客户项目**（Python 后端、Java 应用等）
3. **第一次能跑 monorepo 多语言任务**（前端 + 后端协同改动）
4. **第一次能用 AgentMesh 改 AgentMesh**（自升级 = self-eating dogfood）

这一步完成前，AgentMesh 永远是"前端任务编排工具"；完成后，才是真正的"自动编程平台"。

---

## 9. 不要做清单（OS-2026-009 范围内）

- 不要试图一次实现所有 5 个 Adapter（按 P0/P1/P2 分 OS）
- 不要让 Adapter 调真实 LLM（Adapter 只负责命令解析和文件分类）
- 不要把 Detector 写成"递归扫描整个项目"（只读第一层）
- 不要在 contract 里塞执行逻辑（Adapter 是 server 的事）
- 不要让前端有"修改 toolchain"的复杂表单（只暴露"重新检测"和"runtime_profile 下拉框"）
- 不要为了支持 mixed/monorepo 把抽象搞得过于复杂（留到 OS-2026-013）
- 不要让 Adapter 自己 decide 用哪个模型（那是 Runner 的事）
- 不要在 OS-2026-009 实现 Python 实接（留 OS-2026-010）

---

## 10. 给未来的自己的提醒

如果你打开这份文档时已经在做 OS-2026-009：

1. **先读 OS-2026-007 的交付状态**：确认 Test Runner / Sandbox / risk-scorer 三个模块的代码组织符合"多语言前瞻"的 4+1 条约束（OS-2026-007 Architect Prompt 末尾追加的内容）
2. **不要从 OS-2026-009 开始就追求完美**：先迁移 NodejsAdapter 跑通，再扩 Python，再扩其他
3. **Detector 的规则一定会随时间变化**：preuv 全部、conda、bazel、nx monorepo 等都可能要加；保持规则集中在一个文件，便于扩展
4. **Adapter 测试要用真实项目**：建议在仓库里维护 `tests/fixtures/{nodejs,python,java}/` 各放一个最小项目，CI 跑 Adapter 测试
5. **如果你想跳过 OS-2026-009 直接做 Python 实接**：不行。抽象层不先做，Python 实接会写得乱七八糟，未来加 Java/Rust 时又要重做一次。

---

**文档结束。这份 Plan 应在 OS-2026-007 + OS-2026-008 交付完成后，作为 OS-2026-009 的唯一权威输入。**
