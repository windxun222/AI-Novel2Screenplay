# AI Novel2Screenplay — AI 小说转剧本工具

将小说文本自动转换为结构化中文剧本（YAML 格式），降低小说改编剧本的门槛。

## 功能

- **多章处理**：支持 1 章以上的小说文本，按章节逐章调用 DeepSeek API 转换
- **上下文衔接**：Pre-scan 预扫描角色 + 前情概要注入，确保跨章节连续性
- **中文剧本规范**：输出符合中文影视行业通用格式的结构化剧本
- **连续性校验**：自动检测角色命名冲突、场景逻辑矛盾，输出警告
- **可编辑输出**：YAML 格式，可在任何文本编辑器中修改，也支持 Web 编辑器浏览
- **YAML Schema**：明确定义的剧本数据模型，附带完整设计文档

## 项目结构

```
7Cow/
├── docs/
│   ├── screenplay-schema.md       # YAML Schema 定义 + 设计原理说明
│   └── architecture.md            # 架构说明（待补充）
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI 入口
│   │   ├── config.py              # 配置管理
│   │   ├── models/                # Pydantic 数据模型
│   │   │   ├── novel.py           # 小说输入模型
│   │   │   └── screenplay.py      # 剧本输出模型
│   │   ├── services/
│   │   │   ├── parser.py          # 章节分割与文本预处理
│   │   │   ├── ai_service.py      # DeepSeek API 封装
│   │   │   ├── converter.py       # 转换编排 + Context Hub
│   │   │   └── assembler.py       # 角色合并 + 场景拼接 + 连续性校验
│   │   ├── prompts/
│   │   │   ├── pre_scan.py        # Pre-scan 提示词
│   │   │   └── system.py          # 逐章转换提示词
│   │   ├── api/
│   │   │   └── routes.py          # FastAPI 路由
│   │   └── schemas/
│   │       └── screenplay_example.yaml  # 示例 YAML 输出
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
│   │   │   └── ConvertPage.vue    # 转换页面
│   │   ├── components/
│   │   │   ├── NovelInput.vue         # 文本输入/文件上传
│   │   │   ├── ConversionProgress.vue # 转换进度
│   │   │   └── ScreenplayResult.vue   # 结果展示
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

### 4. 转换流程

1. 在浏览器中打开 http://localhost:5173
2. 点击「开始转换」
3. 粘贴小说文本，至少 1 章（或上传 .txt 文件）
4. 点击「开始转换」按钮
5. 等待 AI 逐章处理（每章约 5-15 秒）
6. 查看生成的剧本，审阅连续性警告
7. 复制 YAML 或下载文件

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chapters/parse` | 本地分割章节（不调用 API）|
| POST | `/api/convert` | 完整转换管线（Pre-scan → 逐章转换 → Assembler）|
| GET  | `/api/schema` | 返回 YAML Schema 定义 |

## YAML Schema

详见 [docs/screenplay-schema.md](docs/screenplay-schema.md)

## 转换管线

```
用户输入 (1章+)
    │
    ▼
Phase 0: Pre-scan (DeepSeek 轻量调用)
    │  输出：全局角色清单 + 每章概要
    │
    ▼
Phase 1: 逐章转换 (DeepSeek + 上下文注入)
    │  每章输入：角色表 + 前情进展 + 本章正文
    │  每章输出：本章新增角色 + 场景 YAML
    │
    ▼
Phase 2: Assembler (本地处理)
    │  ① 角色合并（精确→别名→模糊）
    │  ② 场景拼接与重编号
    │  ③ 连续性校验
    │
    ▼
Phase 3: AI 一致性润色 (可选)
        输出：完整剧本 YAML
```

## 开发规范

- **分支策略**：`main`（稳定）← `dev`（开发）← `feature/*`（功能分支）
- **提交规范**：Conventional Commits（`feat:`、`fix:`、`docs:`、`test:`、`ci:`）
- **PR 流程**：所有合并到 `main` 的变更必须通过 Pull Request
- **代码风格**：Python 遵循 PEP 8（ruff 检查），Vue 3 Composition API + `<script setup>`

## License

MIT
