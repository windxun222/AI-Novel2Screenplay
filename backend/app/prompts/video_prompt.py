VIDEO_SYSTEM_PROMPT = """
你是一位顶尖的 AI 视频导演兼提示词工程师（Prompt Engineer），精通 Sora、Kling、Runway Gen-3 等主流视频大模型的底层逻辑。
你的任务是将输入的剧本场景数据，转化为极具电影感、物理规律严谨的【纯英文视频提示词】。

### ⚠️ 绝对核心约束（必须严格遵守）：
1. **忠于原著，拒绝幻觉**：只能使用输入数据中的地点、角色、动作和情节。你可以补充光影、材质、摄影参数来增强画面，但**严禁**捏造新角色、新事件或改变原有动作逻辑。
2. **视觉化转译**：将抽象的"性格/情绪"转化为具体的"微表情/肢体动作"。
3. **对白处理陷阱**：AI 视频模型无法准确生成字幕。请**不要**在画面中描述具体的字幕文字，而是将"对白"转化为描述人物说话时的**口型动态、面部肌肉牵引、眼神交流和肢体互动**。
4. **语言要求**：最终输出的 Prompt 必须是**高质量、流畅的英文自然语言长句**（段落式描述，拒绝生硬的标签堆砌）。

### 🎬 视频提示词构建公式（请在脑海中按此顺序构建画面）：
- **[Subject & Details]**: 人物外形、服装材质、面部细节。
- **[Action & Physics]**: 动作的发力点、衣物/头发的物理飘动、与环境的真实交互（如踩踏水花、触碰灰尘）。
- **[Environment & Lighting]**: 空间纵深、环境细节、电影级布光（如 Volumetric lighting, Chiaroscuro）、色彩调色（Color grading）。
- **[Camera & Cinematography]**: 运镜方式（Tracking shot, Pan, Dolly in）、焦段（35mm, 85mm）、景深（Shallow depth of field）、镜头质感（Film grain, Anamorphic lens flare）。

### 📝 输出格式要求：
请严格按照以下结构输出，不要包含任何多余的寒暄语：

【导演思路拆解】(用中文简述：1. 核心视觉焦点 2. 运镜设计 3. 光影氛围)
【英文 Prompt】(直接可复制的纯英文长段落，要求细节丰富、画面感极强)
【负面提示词 Negative Prompt】(提供一组英文反向提示词，排除画面崩坏、形变、低画质等问题)
"""


def build_video_prompt_data(req):
    """Build the scene data string for video prompt generation."""
    NL = "\n"
    char_lines = []
    for c in req.characters:
        name = c.get("name", "")
        parts = [name]
        if c.get("age"): parts.append(c.get("age"))
        if c.get("gender"): parts.append({"男": "男性", "女": "女性"}.get(c.get("gender"), ""))
        if c.get("role"): parts.append(c.get("role"))
        if c.get("personality"): parts.append("性格：" + c.get("personality"))
        char_lines.append("  " + "，".join(p for p in parts if p))

    interior = "内景" if req.interior else "外景"
    time_map = {"晨": "清晨", "日": "白天", "黄昏": "黄昏", "夜": "夜晚"}
    time_label = time_map.get(req.time, req.time)

    return f"""【场景基本信息】
视觉风格：{req.style}
地点：{interior} · {req.location} · {time_label}
概要：{req.summary or "无"}

【以下数据直接来自剧本原文，你必须基于这些数据撰写提示词，不得编造任何原文中不存在的内容】

【出场角色】
{NL.join(char_lines) if char_lines else "  无角色信息"}

【动作描写】
{NL.join("  " + a for a in req.actions) if req.actions else "  无"}

【对白台词】
{NL.join("  " + d for d in req.dialogue_lines) if req.dialogue_lines else "  无"}"""
