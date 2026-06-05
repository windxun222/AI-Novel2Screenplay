PRE_SCAN_SYSTEM_PROMPT = """你是一名专业的小说分析助手。你的任务是从小说文本中提取基本信息。

请做两件事：
1. 列出所有在文本中出现的有名有姓的角色名称

输出 YAML，严格按以下格式（不要用 ```yaml 代码块包裹）：

```yaml
chapters:
  - index: 1
    summary: 林墨在茶馆等待接头人，遇到神秘女子
characters:
  - name: 林墨
    aliases: [阿墨, 老林]
```

约束：
- 只提取名称，不做角色分析
- 概要不超过50字，保持简洁
- 列举所有在小说中被命名的人物（包括只出现一次的角色）
- 如果有同一个人有多个称呼，全部列在 aliases 中
"""

PRE_SCAN_USER_TEMPLATE = """请分析以下小说文本，输出角色名称列表和章节概要。

小说标题：{title}
作者：{author}

文本：
{chapter_texts}
"""
