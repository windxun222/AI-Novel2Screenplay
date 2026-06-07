# 架构说明

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3 + Vite)                       │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ HomePage │  │ NovelInput │  │ConvertProgress│  │ScreenplayRes│ │
│  │          │  │            │  │               │  │ ult        │ │
│  └──────────┘  └───────────┘  └──────────────┘  └────────────┘ │
│                      │                                           │
│              ┌───────┴───────┐                                   │
│              │  ConvertPage  │  ← 控制器，管理状态与流程             │
│              └───────┬───────┘                                   │
│                      │  /api/* （Vite 代理至 localhost:8000）       │
└──────────────────────┼──────────────────────────────────────────┘
                       │
┌──────────────────────┼──────────────────────────────────────────┐
│                后端 (FastAPI + Uvicorn)                          │
│              ┌───────┴───────┐                                   │
│              │   routes.py   │  ← API 路由层                      │
│              └───────┬───────┘                                   │
│        ┌─────────────┼─────────────┐                             │
│  ┌─────┴─────┐ ┌─────┴─────┐ ┌─────┴─────┐                      │
│  │ converter │ │ assembler │ │ai_service│                       │
│  │   .py     │ │   .py     │ │   .py    │                       │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘                      │
│        │             │             │                              │
│  ┌─────┴─────┐ ┌─────┴─────┐ ┌─────┴─────┐                      │
│  │ ContextHub│ │ 角色合并   │ │ DeepSeek │                       │
│  │ 上下文共享 │ │ 场景拼接   │ │   API    │                       │
│  │           │ │ 连续性校验 │ │          │                       │
│  └───────────┘ └───────────┘ └──────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

## 二、转换管线详解

### Phase 0：Pre-Scan（预扫描）

**目标**：用一次轻量级 AI 调用，构建全局上下文。

```
输入：小说标题 + 所有章节的前 2000 字摘要
  │
  ▼
AI 调用（temperature=0.1，max_tokens=2048）
  │
  ▼
输出：全局角色清单 + 每章概要
  │
  ▼
存储到 ContextHub：
  - characters[]      (全局角色列表)
  - chapter_summaries{} (章节索引 → 概要)
```

**设计原因**：只发送一次预扫描请求（而非每章都扫），减少 API 调用次数和成本。

### Phase 1：逐章转换

**目标**：每章独立调用 DeepSeek，注入累积的上下文。

```
对于每一章：
  │
  ├── 构造提示词：
  │   ├── 系统提示词（剧本格式规范）
  │   ├── 已有角色表（ContextHub.characters → YAML）
  │   ├── 前情概要（ContextHub.get_summary_context(chapter.index)）
  │   └── 本章正文
  │
  ▼
  AI 调用（temperature=0.3，max_tokens=4096）
  │
  ▼
  YAML 响应清洗（去除 markdown 代码块）
  │
  ▼
  更新 ContextHub：
  ├── 新增角色追加到 characters[]
  └── 原始 YAML 存入 chapter_yamls{}
```

**超长章节处理**：如果章节超过 `MAX_CHAPTER_CHARS`（默认 8000），`chunk_chapter()` 按段落边界分割为多段，每段独立转换后拼接。

### Phase 2：Assembler（组装与校验）

**目标**：合并所有逐章产出，重编号，运行连续性检查。

```
输入：所有章节的原始 YAML + ContextHub
  │
  ├── ① 角色合并（_merge_characters）
  │   ├── Step 1: 精确姓名匹配
  │   ├── Step 2: 别名匹配（迭代解析）
  │   └── Step 3: 模糊匹配（委托 UI 层）
  │
  ├── ② 场景解析（_parse_scenes）
  │   └── 每章 YAML → ContentBlock[] → Scene 列表
  │
  ├── ③ 全局重编号（scene.number = 1, 2, 3...）
  │
  ├── ④ 连续性检查
  │   ├── 孤立角色检查
  │   ├── 地点内外景一致性
  │   ├── 场景间转场标记
  │   └── 角色性格描述一致性
  │
  ├── ⑤ 构建 Act（按章节分组场景）
  │
  ▼
输出：完整的 Screenplay Pydantic 模型
```

## 三、数据模型设计

```
Screenplay
├── metadata: ScreenplayMeta
│   ├── title, source, author
│   ├── adapter ("AI Novel2Screenplay")
│   ├── created_at
│   ├── chapter_count
│   └── version
├── characters: CharacterRef[]
│   ├── id (char_XXX)
│   ├── name
│   ├── aliases[]
│   ├── role, gender, age
│   ├── personality, background
│   └── notes
├── acts: Act[]
│   ├── id (act_X)
│   ├── title, summary
│   └── scenes: Scene[]
│       ├── id (scene_XXX)
│       ├── number (全局递增)
│       ├── heading, location, time, interior
│       ├── summary
│       ├── chapter_index
│       └── content: ContentBlock[]
│           ├── type (action|dialogue|narration|transition)
│           ├── description
│           ├── character_id (对白时引用 CharacterRef.id)
│           ├── line (对白台词)
│           ├── delivery (语气指示)
│           └── transition_type
└── warnings: ContinuityWarning[]
    ├── level (info|warning|error)
    ├── type
    ├── message
    └── locations[]
```

## 四、ContextHub 设计

`ContextHub` 是跨章节共享状态的容器，作为 `Converter` 的状态属性存在：

| 字段 | 类型 | 用途 |
|------|------|------|
| `characters` | `List[dict]` | 累积的全局角色表 |
| `chapter_summaries` | `Dict[int, str]` | 章节索引 → AI 生成的概要 |
| `chapter_yamls` | `Dict[int, str]` | 章节索引 → 原始 AI 输出 YAML |
| `continuity_warnings` | `List[ContinuityWarning]` | 转换过程中收集的警告 |

**设计原因**：逐章转换需要前几章的角色和剧情信息。ContextHub 是临时的内存状态，最终由 Assembler 消费并清零。

## 五、AI 服务封装

`AIService` 是对 DeepSeek API 的薄封装：

- 使用 OpenAI Python SDK（兼容协议）
- `chat(system_prompt, user_prompt, temperature, max_tokens)` → 返回原始文本
- `is_available()` → 检查 API Key 是否已配置
- 错误处理：`APIError` → `RuntimeError`（统一异常类型）

**可替换性**：只需修改 `base_url` + `api_key` + `model` 三个配置即可切换到任何兼容 OpenAI 协议的 API（如 OpenAI、Moonshot、Zhipu 等）。

## 六、前端组件通信

```
App.vue
├── Header（导航栏）
├── router-view
│   ├── HomePage.vue    （静态内容，无状态管理）
│   └── ConvertPage.vue （唯一有状态的控制器视图）
│       ├── NovelInput.vue
│       │   └── emit("submit", {title, author, text})
│       ├── ConversionProgress.vue
│       │   └── props: {phase, chapters, chapterResults}
│       └── ScreenplayResult.vue
│           └── props: {screenplay, error, warnings, novel}
└── Footer
```

**数据流**：单向数据流，父组件通过 props 向子组件传递数据，子组件通过 emit 向父组件通知事件。不使用集中式状态管理（如 Pinia），因为当前只有 ConvertPage 一个页面需要管理复杂状态。

## 七、API 接口设计

| 方法 | 路径 | 说明 | 返回类型 |
|------|------|------|---------|
| GET | `/` | 健康检查 | JSON |
| POST | `/api/chapters/parse` | 本地分割章节 | JSON |
| POST | `/api/convert` | 完整转换管线（JSON 输出）| JSON（Screenplay） |
| POST | `/api/convert/yaml` | 完整转换管线（YAML 输出）| text/yaml |
| GET | `/api/schema` | 剧本 Schema 定义 | JSON |

## 八、关键技术决策

| 决策 | 理由 |
|------|------|
| FastAPI 而非 Flask | 原生异步支持、自动 OpenAPI 文档、Pydantic 集成 |
| Vue 3 Composition API | 更好的 TypeScript 支持、逻辑复用、Tree-shaking |
| Vite 而非 Webpack | 更快的冷启动和 HMR，原生 ESM |
| YAML 作为中间格式 | AI 原生支持 YAML 输出，人类可读，无需 JSON 转义 |
| Pydantic v2 | 更快的验证速度，更好的 discriminated union 支持 |
| 逐章而非全文转换 | 避免上下文窗口溢出，支持超长小说 |
| 视频提示词 AI 格式化 | 基于真实数据改写，零幻觉 |

## 九、目录结构

```
7Cow/
├── docs/
│   ├── screenplay-schema.md   # YAML Schema 定义 + 设计原理
│   └── architecture.md        # 本文档
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 入口 + CORS
│   │   ├── config.py          # 环境配置（pydantic-settings）
│   │   ├── models/            # Pydantic 数据模型
│   │   │   ├── novel.py       # NovelInput, ChapterInput
│   │   │   └── screenplay.py  # Screenplay + 子模型
│   │   ├── services/          # 业务逻辑
│   │   │   ├── parser.py      # 章节分割
│   │   │   ├── ai_service.py  # AI API 封装
│   │   │   ├── converter.py   # 转换编排 + ContextHub
│   │   │   └── assembler.py   # 组装 + 校验
│   │   ├── prompts/           # AI 提示词模板
│   │   │   ├── pre_scan.py
│   │   │   └── system.py
│   │   ├── api/
│   │   │   └── routes.py      # API 路由
│   │   └── schemas/
│   │       └── screenplay_example.yaml
│   ├── tests/
│   │   ├── test_parser.py
│   │   ├── test_assembler.py
│   │   └── fixtures/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/
│   │   ├── views/
│   │   ├── components/
│   │   ├── api/client.js
│   │   └── styles/main.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── .github/
│   ├── pull_request_template.md
│   └── workflows/ci.yml
├── .env.example
├── .gitignore
├── .editorconfig
└── README.md
```
