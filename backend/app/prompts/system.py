SYSTEM_PROMPT = """你是一名专业的剧本改编助手。你的任务是将小说章节改编为结构化的中文剧本（YAML 格式）。

【转换规则】
- 小说叙述描写 → action（保持画面感，用第三人称现在时）
- 人物对话 → dialogue（保留原意，可适当精炼口语化台词）
- 心理描写/旁白 → narration
- 章节/场景切换 → transition

【中文剧本格式规范】
- 场景标题格式：【内|外】地点·时间
- 时间使用：晨 / 日 / 黄昏 / 夜
- 每场戏开头必须有场景标题
- 动作描述简洁有画面感

【角色命名规则】
- 如果角色在"已有角色表"中存在，必须使用已有 ID
- 新角色的 ID 从已有最大 ID 之后续编
- 同一角色在不同章节中如果有不同称呼，使用同一 ID

【输出要求】
- 只输出 YAML，不要多余说明
- characters 字段只包含本章首次登场的新角色
- 每章至少包含 1 个场景
- 确保 summary 字段概括本场核心事件
"""


def build_chapter_prompt(chapter_index, chapter_text, character_context, previous_summaries):
    parts = []
    parts.append("## 已有角色表")
    parts.append(character_context or "（暂无已登场角色）")
    parts.append("")
    parts.append("## 前情进展")
    parts.append(previous_summaries or "（本剧第一章）")
    parts.append("")
    parts.append(f"## 第{chapter_index}章原文")
    parts.append(chapter_text)
    parts.append("")
    parts.append("## 输出")
    parts.append("请严格按照前面的格式输出本章的剧本 YAML。")
    return "\n".join(parts)
