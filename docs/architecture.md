# 架构说明

## 一、系统概览

```
前端 (Vue 3 + Vite)
  /api/* 代理 → 后端 (FastAPI + Uvicorn)
    routes.py → converter.py → assembler.py → ai_service.py → DeepSeek API
```

## 二、转换管线

### 两种工作模式

| 模式 | 流程 | 适用场景 |
|------|------|---------|
| 一次性全量 | 预扫描 → 所有章节 → 组装 | 快速生成初稿 |
| 逐章审查 | 预扫描 → 角色审核 → 逐章转换 → 组装 | 精细控制质量 |

### Phase 0：预扫描（Pre-Scan）

一次轻量 AI 调用，构建全局上下文。

- 发送每章完整文本，不再截断
- AI 返回：角色列表（姓名、别名、角色定位、性格、首次出场章节）+ 每章概要
- 代码强制分配稳定 ID：char_001、char_002...
- 角色外貌由性格关键词推断（如"沉稳"→"深色长袍，神色平静"）

### Phase 1：逐章转换

- 每章独立调用 DeepSeek
- 上下文注入：已有角色表（含 ID）+ 前情概要
- **温度 0.1**：最小化幻觉
- **反幻觉规则**：系统提示词要求严格忠于原文，示例用占位符
- **ID 后处理**：按名字匹配，将 AI 自创的 character_id 重映射为 pre-scan 稳定 ID

### Phase 2：组装（Assembler）

- 按名字合并角色（pre-scan ID 优先于章节 YAML ID）
- 从章节 YAML 解析场景
- 全局场景重编号
- 组装后 ID 重映射：遍历所有对白，对齐 character_id 到角色表
- 运行 4 项连续性检查
- ID 去重：不同角色共享同一 ID 时自动 renumber
- 角色排序：主角 → 配角 → 反派 → 龙套

### 逐章模式完整流程

```
用户输入文本
  → parseChapters（解析章节）
  → preScan（预扫描 + 分配稳定 ID）
  → 角色审核页面（可增删改合并，ID 补位递增）
  → 确认角色表
  → convertChapter（逐章转换，每章可折叠、内容可编辑）
  → assembleStep（生成剧本，支持部分完成）
  → 进度自动持久化到工作区 JSON
```

### 部分完成 & 断点续转

- 任意数量章节转换后即可生成剧本，未转换章节自动跳过
- 后续可通过"追加新章节"导入更多内容
- Workspace 模型含 step_results 字段，每章转换后自动保存
- 重新打开工作区自动恢复逐章状态

## 三、角色 ID 管理系统

**核心原则**：角色 ID 由系统层保证一致性，不依赖 AI 的随机行为。

| 阶段 | 操作 | 文件 |
|------|------|------|
| 预扫描后 | 强制分配 char_001~char_N | converter.py |
| 上下文注入 | get_character_context_yaml() 输出含 id 字段 | converter.py |
| 逐章转换后 | 按名字匹配，将 AI 自创 ID 重映射为 pre-scan ID | routes.py |
| 角色更新 | update_characters() 遇到已有角色跳过 ID | converter.py |
| Assembler 合并 | pre-scan 角色优先于章节 YAML 角色 | assembler.py |
| Assembler 去重 | 不同名字共享同一 ID 时重新编号 | assembler.py |
| 前端合并 | doMerge() 自动重映射场景中所有对白引用 | ScreenplayResult.vue |

## 四、动态连续性警告

4 项检查：orphan_character、location_consistency、scene_gaps、character_description_changed。

| 功能 | 说明 |
|------|------|
| 刷新重检 | 编辑剧本后重新运行全部检查（POST /api/convert/recheck） |
| 点击定位 | 点击警告消息平滑滚动到对应场景，高亮闪烁 1.5 秒 |
| 一键修复 | missing_transition（补"切至"）、orphan_character（加入角色表）、inconsistent_location（统一内外景） |

## 五、API 端点（11 个）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / | 健康检查 |
| POST | /api/chapters/parse | 本地章节分割 |
| POST | /api/convert | 一次性全量转换（JSON） |
| POST | /api/convert/yaml | 一次性全量转换（YAML 下载） |
| POST | /api/convert/pre-scan | 预扫描：提取角色 + 章概要 |
| POST | /api/convert/chapter | 逐章转换（含上下文 + ID 重映射） |
| POST | /api/convert/assemble | 组装各章 YAML → 完整剧本 |
| POST | /api/convert/recheck | 重新运行连续性检查 |
| POST | /api/prompts/generate | AI 视频提示词生成 |
| GET | /api/schema | 剧本 YAML Schema |
| CRUD | /api/workspaces/* | 工作区管理 |

## 六、前端架构

### 页面

| 页面 | 路由 | 功能 |
|------|------|------|
| HomePage | / | 产品介绍 + 功能卡片 |
| ConvertPage | /convert | 核心转换控制器（全量 & 逐章） |
| WorkspacesPage | /workspaces | 工作区列表 + 导出/导入 JSON |
| PromptsPage | /prompts | AI 视频提示词工坊 |

### 核心组件

| 组件 | 用途 |
|------|------|
| NovelInput | 文本输入 + 文件上传 |
| ConversionProgress | 全量模式进度条 |
| ScreenplayResult | 完整结果展示 + 场景/对白增删 + 角色增删合并 + 内联编辑 |
| EditableField | 点击编辑字段（读取 DOM 真实值） |

### 数据流

父子组件通过 props / emit 通信。逐章状态通过 useWorkspace 单例跨组件共享。

## 七、工作区持久化

- JSON 文件存储在 /workspaces/ 目录
- Workspace 模型字段：raw_text、chapters、screenplay、step_results、status
- step_results 支持跨会话断点续转
- 导出/导入通过 JSON 文件下载/上传

## 八、幻觉预防措施

| 措施 | 说明 |
|------|------|
| 系统提示词 | 明确要求严格忠于原文 + 反幻觉检查清单 |
| 示例 YAML | 使用"[主角名]"等占位符，不出现具体名称 |
| 温度 | 逐章转换 0.3 → 0.1 |
| 后处理 | 逐章 API 和组装 API 均含 ID 重映射 |
| 字符串清洗 | _sanitize_str / _sanitize_char_dict 处理 AI 返回的非字符串值 |

## 九、项目目录结构

```
7Cow/
├── docs/
│   ├── architecture.md
│   └── screenplay-schema.md
├── backend/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── models/
│       ├── services/
│       ├── prompts/
│       └── api/
├── frontend/
│   └── src/
│       ├── views/
│       ├── components/
│       ├── composables/
│       ├── api/client.js
│       └── router/index.js
└── workspaces/
```
