# AI Novel2Screenplay —— AI 小说转剧本工具

将小说文本自动转换为结构化中文剧本（YAML 格式），降低小说改编剧本的门槛。

## 功能

- **多章处理**：支持 1 章以上的小说文本，按章节逐章调用 DeepSeek API 转换
- **上下文衔接**：Pre-scan 预扫描角色 + 前情概要注入，确保跨章节连续性
- **中文剧本规范**：输出符合中文影视行业通用格式的结构化剧本
- **连续性校验**：自动检测角色命名冲突、场景逻辑矛盾，输出警告
- **逐章审查模式**：分步转换，每章独立审查编辑后再继续，支持断点续转
- **角色管理**：角色表增删改合并，ID 自动分配和一致性保护，补位递增
- **场景/对白编辑**：Web 端直接增删改场景和对白，自动保存到工作区
- **连续性警告**：动态刷新、一键修复、点击定位到问题场景
- **AI 视频提示词工坊**：从剧本生成镜头级视频提示词，可自定义提示词模板
- **工作区管理**：JSON 格式持久化，支持导出/导入，多项目切换

## 项目结构

```
7Cow/
├── docs/
│   ├── screenplay-schema.md       # YAML Schema 定义 + 设计原理
│   └── architecture.md            # 架构说明
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI 入口
│   │   ├── config.py              # 配置管理
│   │   ├── models/                # Pydantic 数据模型
│   │   │   ├── novel.py           # 小说输入模型
│   │   │   ├── screenplay.py      # 剧本输出模型
│   │   │   └── workspace.py       # 工作区持久化模型
│   │   ├── services/              # 业务逻辑
│   │   │   ├── parser.py          # 章节分割与文本预处理
│   │   │   ├── ai_service.py      # DeepSeek API 封装
│   │   │   ├── converter.py       # 转换编排 + ContextHub + ID 管理
│   │   │   ├── assembler.py       # 角色合并 + 场景拼接 + 连续性校验 + ID 去重
│   │   │   └── workspace_store.py # 工作区 JSON 持久化
│   │   ├── prompts/               # AI 提示词
│   │   │   ├── pre_scan.py        # 预扫描提示词
│   │   │   ├── system.py          # 逐章转换提示词
│   │   │   └── video_prompt.py    # 视频提示词模板
│   │   └── api/
│   │       └── routes.py          # 全部 API 路由（11 个端点）
│   ├── tests/
│   │   ├── test_parser.py
│   │   ├── test_assembler.py
│   │   └── fixtures/              # 示例小说文本
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.vue                # 根组件
│   │   ├── router/index.js        # 路由配置
│   │   ├── views/
│   │   │   ├── HomePage.vue       # 首页
│   │   │   ├── ConvertPage.vue    # 转换页面（全量 + 逐章）
│   │   │   ├── WorkspacesPage.vue # 工作区列表
│   │   │   └── PromptsPage.vue    # AI 视频提示词工坊
│   │   ├── components/
│   │   │   ├── NovelInput.vue         # 文本输入 / 文件上传
│   │   │   ├── ConversionProgress.vue # 转换进度
│   │   │   ├── ScreenplayResult.vue   # 结果展示 + 编辑
│   │   │   └── EditableField.vue      # 内联编辑组件
│   │   ├── composables/
│   │   │   └── useWorkspace.js    # 工作区状态管理
│   │   ├── api/client.js          # API 调用封装
│   │   └── styles/main.css        # 全局样式
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

## 快速开始

### 前提

- Python 3.12+
- Node.js 20+
- DeepSeek API Key

### 1. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入你的 DEEPSEEK_API_KEY
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

后端运行在 http://localhost:8000

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:5173

### 4. 使用方式

**一次性转换**：
1. 打开 http://localhost:5173
2. 点击"开始转换"
3. 粘贴小说文本，至少 1 章
4. 点击"开始转换"，等待 AI 处理
5. 查看生成的剧本，审阅连续性警告
6. 复制 YAML 或下载文件

**逐章审查转换**（推荐）：
1. 勾选"逐章转换"复选框
2. 粘贴小说文本后点击"开始转换"
3. 在角色审核页面确认/修改 AI 提取的角色表
4. 逐章点击"转换本章"，每章结果可折叠查看
5. 随时可追加新章节（点击"+ 追加新章节"）
6. 点击"完成转换"生成完整剧本

**视频提示词生成**：
1. 点击导航栏"提示词"
2. 选择工作区加载剧本
3. 点击场景 → 设置风格和镜头 → 一键生成

## API 接口（11 个）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / | 健康检查 |
| POST | /api/chapters/parse | 本地分割章节 |
| POST | /api/convert | 一次性完整转换 |
| POST | /api/convert/yaml | 一次性完整转换（YAML 下载） |
| POST | /api/convert/pre-scan | 预扫描：提取角色 + 章概要 |
| POST | /api/convert/chapter | 逐章转换：单章带上下文 + ID 重映射 |
| POST | /api/convert/assemble | 组装各章 YAML → 完整剧本 |
| POST | /api/convert/recheck | 动态重检连续性警告 |
| POST | /api/prompts/generate | AI 视频提示词生成 |
| GET | /api/schema | 返回 YAML Schema 定义 |
| CRUD | /api/workspaces/* | 工作区管理 |

## 转换管线

```
用户输入 (1章+)
    │
    ▼
Phase 0: Pre-scan (DeepSeek 轻量调用)
    │  输出：全局角色清单 + 每章概要（含稳定 ID）
    │
    ▼
🆕 角色审核（可选，逐章模式）
    │  增删改合并角色，确认后开始转换
    │
    ▼
Phase 1: 逐章转换 (DeepSeek + 上下文注入)
    │  每章输入：角色表 + 前情进展 + 本章正文
    │  每章输出：本章新增角色 + 场景 YAML
    │  🆕 后处理：ID 重映射对齐 pre-scan
    │
    ▼
Phase 2: Assembler (本地处理)
    │  ① 角色合并（pre-scan ID 优先）
    │  ② 场景拼接与重编号
    │  ③ 连续性校验（4 项检查）
    │  ④ ID 去重 + 角色排序
    │  🆕 组装后 ID 重映射
    │
    ▼
输出：完整剧本 YAML
```

## YAML Schema

详见 [docs/screenplay-schema.md](docs/screenplay-schema.md)

## 角色 ID 管理

系统层保证角色 ID 全局一致：

1. Pre-scan 后强制分配 char_001~char_N
2. 上下文注入时包含 id 字段
3. 逐章转换后按名字重映射 AI 自创 ID
4. Assembler 中 pre-scan ID 优先 + 最终去重
5. 前端合并角色时自动更新所有场景引用

## 开发规范

- **分支策略**：main（稳定）← dev（开发）← feature/*（功能分支）
- **提交规范**：Conventional Commits（feat:、fix:、docs:、test:、ci:、chore:）
- **PR 流程**：所有合并到 main 的变更必须通过 Pull Request
- **代码风格**：Python 遵循 PEP 8（ruff 检查），Vue 3 Composition API + `<script setup>`
- **CI**：GitHub Actions（ruff lint + pytest + vite build）

## License

MIT
