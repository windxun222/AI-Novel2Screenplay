# 剧本 YAML Schema 定义与设计说明

## 一、概述

本文档定义 AI Novel2Screenplay 工具的剧本输出格式（YAML Schema），并说明其设计原理。该 Schema 是小说文本自动转换为结构化剧本的标准数据模型。

- **Schema 版本**：1.0
- **格式**：YAML 1.2
- **目标用途**：剧本初稿的存储、编辑、版本管理及进一步人工打磨

---

## 二、Schema 完整定义

```yaml
screenplay:
  # ── 元数据 ──
  metadata:
    title:       string       # 剧本标题（必填）
    source:      string|null  # 原著小说名
    author:      string|null  # 原著作者
    adapter:     string       # 转换工具标识，固定值为 "AI Novel2Screenplay"
    created_at:  date         # 转换日期，格式 YYYY-MM-DD
    chapter_count: int        # 输入的章节数（>= 1）
    version:     string       # Schema 版本号

  # ── 角色表 ──
  characters:
    - id:         string       # 角色唯一 ID，格式 char_XXX
      name:       string       # 角色姓名（必填）
      aliases:    string[]     # 别名列表，如昵称、化名、称号
      role:       string|null  # 剧情角色分类：主角 / 配角 / 反派 / 龙套
      gender:     string|null  # 性别
      age:        string|null  # 年龄（允许模糊表述如 "20岁"、"中年"）
      personality: string|null # 性格关键词或一句话描述
      background: string|null  # 角色背景
      notes:      string|null  # 其他备注

  # ── 幕次 / 章节 ──
  acts:
    - id:          string      # 幕次 ID，格式 act_X
      title:       string|null # 幕次标题
      summary:     string|null # 本幕内容概要
      scenes:
        - id:         string    # 场景唯一 ID，格式 scene_XXX
          number:     int       # 场景序号（从 1 开始，全局递增）
          heading:    string    # 场景标题，格式：【内|外】地点·时间
          location:   string    # 拍摄地点
          time:       string    # 时间标识：晨 / 日 / 黄昏 / 夜
          interior:   bool      # true=内景，false=外景
          summary:    string    # 本场戏概要
          content:
            - type:       string  # 内容类型（见 2.1 节）
              description:string  # type=action|narration 时使用
              character_id: string # type=dialogue 时使用，引用 characters[].id
              line:       string # type=dialogue 时使用，台词正文
              delivery:   string # type=dialogue 时可选，语气/动作指示
              transition_type: string # type=transition 时使用

  # ── 连续性警告 ──
  warnings:
    - level:     string    # 严重级别：info / warning / error
      type:      string    # 警告类型标识
      message:   string    # 人类可读的描述
      locations: string[]  # 关联的场景 ID 列表
```

### 2.1 内容类型枚举

| 类型 | 含义 | 必填字段 | 示例 |
|------|------|---------|------|
| `action` | 动作描写 | description | "林墨推门走进茶馆" |
| `dialogue` | 角色对白 | character_id, line | 林墨说："还是老样子。" |
| `narration` | 旁白/画外音 | description | "他不知道，一场风暴正在逼近" |
| `transition` | 转场提示 | description | "切至" / "淡入" / "闪回" |

---

## 三、设计原理

### 3.1 为什么使用 YAML 而非 JSON 或 XML

| 维度 | YAML | JSON | XML |
|------|------|------|-----|
| 人类可读性 | ★★★★★ | ★★★ | ★★ |
| 注释支持 | 是（#） | 否 | 否 |
| 剧本编辑场景 | 可直接手写/修改 | 需要括号匹配工具 | 过于冗长 |
| 多行文本支持 | 原生支持（\| 块） | 需转义 \n | CDATA |
| Python 生态 | PyYAML 成熟 | 原生支持 | ElementTree |

**结论**：剧本初稿最核心的需求是**作者能直接阅读和修改**。YAML 的缩进结构天然映射剧本的层级关系（幕→场→内容），作者可以用任何文本编辑器打开修改，无需学习额外工具。

### 3.2 角色表独立于场景（全局定义 → ID 引用）

**设计**：角色在顶层 `characters` 数组中一次性定义，后续场景中的对话通过 `character_id` 引用。

**原因**：
- **消除冗余**：一个角色可能出现在数十场戏中，每次都携带完整属性会膨胀文件
- **一致性**：角色属性（年龄、性格）只需维护一份，避免多个副本间漂移
- **便于角色管理**：作者可以集中查看所有角色，而非在场景间分散查找
- **AI 连续性**：全局角色 ID 是跨章节追踪同一角色的锚点，从根本上解决逐章转换中的命名冲突

### 3.3 内容层为何使用带 type 标签的数组而非固定字段

**设计**：`content` 是一个 `ContentBlock[]` 数组，每个 block 通过 `type` 字段区分 action/dialogue/narration/transition。

**替代方案**：为每种类型定义独立字段（如 `actions: [], dialogues: []`）。

**选择原因**：
- **时间顺序是剧本的核心**：动作 - 对白 - 动作 - 转场是一个线性序列。分开字段会丢失顺序信息，或需要额外的 index 字段来排序。
- **弹性扩展**：新内容类型（如 `sound_effect`、`montage`）只需新增一个 type 值，不改变 Schema 结构。
- **解析统一**：不管前端还是后端，遍历一个 `content` 数组比合并多个数组更简单。

### 3.4 场景标题格式：【内|外】地点·时间

这是中文影视行业的约定格式，与好莱坞的 `INT./EXT. LOCATION - DAY/NIGHT` 等价，但更符合中文编剧习惯。

**为什么不在 Schema 中拆成 3 个字段**：`heading` 是一个整体字符串，因为在实际使用中，编剧需要在标题上快速定位场景，而非逐个字段查阅。`location`、`time`、`interior` 作为结构化字段保留，用于程序化检索和校验。

### 3.5 为什么保留 narration（旁白）类型

小说中有大量心理描写和环境渲染，这些内容在剧本中通常被转化为动作或对话。但在剧本初稿阶段，保留部分旁白有助于：
- 理解角色内心动机
- 保留小说的文学性
- 导演和演员在准备阶段可参考

TypeScript 式的严格约束（只允许 action/dialogue）会丢失这些信息。narration 是一个过渡类型，在后续人工打磨中可逐步转化为 action 或删除。

### 3.6 三层嵌套结构（act → scene → content）

**设计**：剧本按 act（幕/章）→ scene（场景）→ content（内容块）三级组织。

**替代方案**：
- **扁平场景列表**：失去章节组织，长剧本难以导航
- **四层（act → sequence → scene → content）**：对初稿过于复杂

**选择原因**：三层结构在**组织能力和简洁性**之间取得平衡。act 层对应原始小说的章节划分，scene 层对应时空变化，content 层是实际的剧本内容。作者可以按章节浏览，也可以全局搜索场景。

### 3.7 `warnings` 段的存在理由

`warnings` 不属于剧本内容，但作为 AI 转换的产物，首次转换不可能完美。将这些校验结果嵌入 YAML 而非独立日志文件的原因：
- **上下文绑定**：警告紧邻它所描述的内容，作者看到场景时立刻知道问题
- **版本追踪**：警告随剧本一起版本化，可以追踪修改历史
- **工具链集成**：编辑器（如我们的 Vue 前端）可以直接解析 warnings 并高亮对应场景



### 3.9 角色 ID 的稳定性与系统层管理

**设计背景**：AI 逐章转换时可能为同一角色在不同章节分配不同的 character_id（如第一章用 char_001、第二章用 char_005），导致角色表膨胀、对白引用错乱。

**决策**：character_id 不依赖 AI 自行维护，而是在系统层通过以下机制保证全局唯一性和一致性：

- **预扫描后强制分配**：Pre-scan 完成后，代码遍历角色列表分配 char_001、char_002...，覆盖 AI 可能返回的空 ID 或 None
- **上下文注入含 ID**：将角色表注入逐章转换的提示词时，明确包含 id 字段，引导 AI 复用已有 ID
- **逐章后处理重映射**：每章转换完成后，按角色名字匹配，将 AI 自创的 character_id 重写为 pre-scan 分配的稳定 ID
- **Assembler 去重**：组装阶段检测不同角色共享同一 ID 的情况，自动 renumber 解决冲突
- **前端合并联动**：用户在 Web 界面合并两个角色时，自动遍历所有场景对白，将被合并角色的 ID 全部替换为目标角色 ID

这一设计将 character_id 从"AI 的输出"转变为"系统的标识符"，从根本上消除了 ID 漂移和重复问题。

### 3.10 连续性警告的动态化

**设计背景**：原始设计中 warnings 是一次性生成的静态数据，用户修改剧本后警告不会自动更新。

**决策**：将警告从静态快照改为可动态刷新的系统：

- **服务端重检**：提供 POST /api/convert/recheck 端点，接收当前剧本 JSON，重新运行全部 4 项校验，返回最新警告列表
- **前端可交互**：Web 界面提供刷新按钮、点击警告定位到场景（平滑滚动 + 高亮闪烁）、一键自动修复常见警告（补转场、加角色、统内外景）
- **保留嵌入结构**：警告仍然嵌入剧本 YAML，便于版本追踪和工具链集成，同时支持动态更新覆盖

这一设计保持了"警告与内容绑定"的原有理念，同时赋予了实时响应用户编辑的能力。

### 3.8 字段约束与开放性

Schema 中有少数必填字段（`id`、`name`、`heading` 等），其余大多可选。这反映了不同质量等级的 AI 输出——一次转换可能只提取到角色名称，缺少背景描述。工具的定位是**降低改编门槛**，而非要求一次完美输出。可选字段的存在允许渐进式完善，作者可以在编辑器中逐步填充缺失信息。

---

## 四、与剧本写作规范的对照

| 剧本元素 | Schema 对应 | 备注 |
|---------|------------|------|
| 场景标题 | `scene.heading` | 格式：【内|外】地点·时间 |
| 动作描述 | `type=action` | 第三人称现在时 |
| 角色出场 | `character_id` | 首次出现时在 characters 中注册 |
| 对白 | `type=dialogue` | 含可选的 delivery 指示 |
| 旁白/OS | `type=narration` | 对应画外音、内心独白 |
| 转场 | `type=transition` | 切至/淡入/淡出/叠化 |
| 角色表 | `characters[]` | 独立于场景的集中管理 |
| 场号 | `scene.number` | 全局顺序编号，便于排练引用 |

---

## 五、版本记录

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| 1.0 | 2026-06-05 | 初始版本 |
