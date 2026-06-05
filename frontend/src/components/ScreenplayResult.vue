<template>
  <div class="result">
    <!-- Error state -->
    <div v-if="error" class="result-error card">
      <h3 class="section-title">转换出错</h3>
      <p class="error-message">{{ error }}</p>
      <p class="error-hint">
        请检查：
        <br />1. DeepSeek API Key 是否已配置
        <br />2. 网络连接是否正常
        <br />3. 小说文本是否包含至少 1 章内容
      </p>
    </div>

    <!-- Success state -->
    <div v-if="screenplay" class="result-success">
      <!-- Warnings -->
      <div v-if="warnings.length" class="result-warnings card">
        <h3 class="section-title">
          连续性警告
          <span class="warn-count">({{ warnings.length }})</span>
        </h3>
        <div
          v-for="(w, i) in warnings"
          :key="i"
          class="warning-item"
          :class="'warn-' + w.level"
        >
          <span class="warn-level">{{ warnLabel(w.level) }}</span>
          <span class="warn-msg">{{ w.message }}</span>
          <span v-if="w.locations?.length" class="warn-locs">
            场景：{{ w.locations.join(", ") }}
          </span>
        </div>
      </div>

      <!-- Metadata -->
      <div class="result-meta card">
        <h3 class="section-title">剧本元数据</h3>
        <div class="meta-grid">
          <div class="meta-item">
            <label>标题</label>
            <span>{{ screenplay.metadata?.title }}</span>
          </div>
          <div class="meta-item">
            <label>来源</label>
            <span>{{ screenplay.metadata?.source }}</span>
          </div>
          <div class="meta-item">
            <label>作者</label>
            <span>{{ screenplay.metadata?.author }}</span>
          </div>
          <div class="meta-item">
            <label>章节数</label>
            <span>{{ screenplay.metadata?.chapter_count }}</span>
          </div>
          <div class="meta-item">
            <label>类型</label>
            <span>{{ screenplay.metadata?.adapter }}</span>
          </div>
          <div class="meta-item">
            <label>版本</label>
            <span>{{ screenplay.metadata?.version }}</span>
          </div>
        </div>
      </div>

      <!-- Characters -->
      <div v-if="screenplay.characters?.length" class="result-chars card">
        <h3 class="section-title">角色表（{{ screenplay.characters.length }}）</h3>
        <div class="char-grid">
          <div v-for="c in screenplay.characters" :key="c.id" class="char-card">
            <div class="char-name">{{ c.name }}</div>
            <div class="char-id">{{ c.id }}</div>
            <div v-if="c.role" class="char-role">{{ c.role }}</div>
            <div v-if="c.personality" class="char-trait">{{ c.personality }}</div>
            <div v-if="c.aliases?.length" class="char-aliases">
              别名：{{ c.aliases.join(", ") }}
            </div>
          </div>
        </div>
      </div>

      <!-- Scenes -->
      <div class="result-scenes card">
        <h3 class="section-title">剧本内容</h3>
        <div v-for="act in screenplay.acts" :key="act.id" class="act-block">
          <h4 class="act-title">{{ act.title }}</h4>
          <div v-for="scene in act.scenes" :key="scene.id" class="scene-block">
            <div class="scene-heading">{{ scene.heading }}</div>
            <div class="scene-meta">
              {{ scene.interior ? "内景" : "外景" }} | {{ scene.location }} | {{ scene.time }}
            </div>
            <div v-if="scene.summary" class="scene-summary">{{ scene.summary }}</div>
            <div class="scene-content">
              <div
                v-for="(block, bi) in scene.content"
                :key="bi"
                class="content-block"
                :class="'block-' + block.type"
              >
                <!-- Action -->
                <div v-if="block.type === 'action'" class="block-action">
                  {{ block.description }}
                </div>
                <!-- Dialogue -->
                <div v-if="block.type === 'dialogue'" class="block-dialogue">
                  <span class="dialogue-char">{{ getCharName(block.character_id) }}</span>
                  <div class="dialogue-line">{{ block.line }}</div>
                  <div v-if="block.delivery" class="dialogue-delivery">
                    （{{ block.delivery }}）
                  </div>
                </div>
                <!-- Narration -->
                <div v-if="block.type === 'narration'" class="block-narration">
                  V.O. {{ block.description }}
                </div>
                <!-- Transition -->
                <div v-if="block.type === 'transition'" class="block-transition">
                  {{ block.description }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Export -->
      <div class="result-export card">
        <h3 class="section-title">导出</h3>
        <div class="export-actions">
          <button class="btn btn-primary" @click="copyJSON">
            {{ copied ? "已复制" : "复制 JSON" }}
          </button>
          <button class="btn btn-secondary" @click="downloadJSON">
            下载 JSON 文件
          </button>
          <button class="btn btn-secondary" @click="downloadYAML">
            下载 YAML 文件
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

const props = defineProps({
  screenplay: Object,
  error: String,
  warnings: Array,
});

const copied = ref(false);

const charMap = computed(() => {
  const map = {};
  if (props.screenplay?.characters) {
    for (const c of props.screenplay.characters) {
      map[c.id] = c.name;
    }
  }
  return map;
});

function getCharName(id) {
  return charMap.value[id] || id || "未知";
}

function warnLabel(level) {
  const labels = { info: "提示", warning: "警告", error: "错误" };
  return labels[level] || level;
}

async function copyJSON() {
  try {
    const json = JSON.stringify(props.screenplay, null, 2);
    await navigator.clipboard.writeText(json);
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
  } catch {
    // fallback
  }
}

function downloadJSON() {
  const json = JSON.stringify(props.screenplay, null, 2);
  const blob = new Blob([json], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = (props.screenplay?.metadata?.title || "screenplay") + ".json";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function downloadYAML() {
  try {
    // Build YAML payload from the existing screenplay data directly,
    // avoiding a second full API conversion
    const screenplay = props.screenplay;
    if (!screenplay) return;

    // Simple YAML serializer for the screenplay structure
    const lines = [];
    const indent = (n, s) => "  ".repeat(n) + s;

    lines.push("screenplay:");
    // metadata
    if (screenplay.metadata) {
      lines.push(indent(1, "metadata:"));
      const m = screenplay.metadata;
      lines.push(indent(2, `title: ${m.title || ""}`));
      if (m.source) lines.push(indent(2, `source: ${m.source}`));
      if (m.author) lines.push(indent(2, `author: ${m.author}`));
      lines.push(indent(2, `adapter: ${m.adapter || "AI Novel2Screenplay"}`));
      lines.push(indent(2, `created_at: ${m.created_at || ""}`));
      lines.push(indent(2, `chapter_count: ${m.chapter_count || 0}`));
      lines.push(indent(2, `version: ${m.version || "1.0"}`));
    }

    // characters
    lines.push(indent(1, "characters:"));
    for (const c of (screenplay.characters || [])) {
      lines.push(indent(2, `- id: ${c.id}`));
      lines.push(indent(3, `name: ${c.name}`));
      if (c.aliases?.length) lines.push(indent(3, `aliases: [${c.aliases.join(", ")}]`));
      if (c.role) lines.push(indent(3, `role: ${c.role}`));
      if (c.gender) lines.push(indent(3, `gender: ${c.gender}`));
      if (c.age) lines.push(indent(3, `age: ${c.age}`));
      if (c.personality) lines.push(indent(3, `personality: ${c.personality}`));
      if (c.background) lines.push(indent(3, `background: ${c.background}`));
      if (c.notes) lines.push(indent(3, `notes: ${c.notes}`));
    }

    // acts
    lines.push(indent(1, "acts:"));
    for (const act of (screenplay.acts || [])) {
      lines.push(indent(2, `- id: ${act.id}`));
      if (act.title) lines.push(indent(3, `title: ${act.title}`));
      if (act.summary) lines.push(indent(3, `summary: ${act.summary}`));
      lines.push(indent(3, "scenes:"));
      for (const scene of (act.scenes || [])) {
        lines.push(indent(4, `- id: ${scene.id}`));
        lines.push(indent(5, `number: ${scene.number}`));
        lines.push(indent(5, `heading: ${JSON.stringify(scene.heading)}`));
        lines.push(indent(5, `location: ${JSON.stringify(scene.location)}`));
        lines.push(indent(5, `time: ${scene.time}`));
        lines.push(indent(5, `interior: ${scene.interior}`));
        if (scene.summary) lines.push(indent(5, `summary: ${JSON.stringify(scene.summary)}`));
        lines.push(indent(5, `chapter_index: ${scene.chapter_index}`));
        lines.push(indent(5, "content:"));
        for (const block of (scene.content || [])) {
          lines.push(indent(6, `- type: ${block.type}`));
          if (block.description) lines.push(indent(7, `description: ${JSON.stringify(block.description)}`));
          if (block.character_id) lines.push(indent(7, `character_id: ${block.character_id}`));
          if (block.line) lines.push(indent(7, `line: ${JSON.stringify(block.line)}`));
          if (block.delivery) lines.push(indent(7, `delivery: ${JSON.stringify(block.delivery)}`));
          if (block.transition_type) lines.push(indent(7, `transition_type: ${block.transition_type}`));
        }
      }
    }

    // warnings
    if (screenplay.warnings?.length) {
      lines.push(indent(1, "warnings:"));
      for (const w of screenplay.warnings) {
        lines.push(indent(2, `- level: ${w.level}`));
        lines.push(indent(3, `type: ${w.type}`));
        lines.push(indent(3, `message: ${JSON.stringify(w.message)}`));
        if (w.locations?.length) lines.push(indent(3, `locations: [${w.locations.join(", ")}]`));
      }
    }

    const yamlContent = lines.join("\n") + "\n";
    const blob = new Blob([yamlContent], { type: "text/yaml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = (screenplay.metadata?.title || "screenplay") + ".yaml";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (e) {
    alert("YAML 下载失败：" + e.message);
  }
}
</script>

<style scoped>
.result {
  margin-top: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.result-error {
  border-color: #5a2a2a;
}
.error-message {
  color: #e07070;
  margin-bottom: 12px;
}
.error-hint {
  font-size: 13px;
  color: #8a6a6a;
  line-height: 1.8;
}

.result-warnings {
  border-color: #5a4a2a;
}
.warn-count {
  font-size: 14px;
  color: #a08050;
}
.warning-item {
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 6px;
  font-size: 13px;
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
.warn-info {
  background: #1a2a3a;
}
.warn-warning {
  background: #2a2a1a;
}
.warn-error {
  background: #3a1a1a;
}
.warn-level {
  font-weight: 600;
  flex-shrink: 0;
  min-width: 32px;
}
.warn-info .warn-level { color: #6a9ad0; }
.warn-warning .warn-level { color: #d0b06a; }
.warn-error .warn-level { color: #d06a6a; }
.warn-msg { flex: 1; }
.warn-locs {
  font-size: 11px;
  color: #6a6a8a;
  flex-shrink: 0;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}
.meta-item label {
  display: block;
  font-size: 11px;
  color: #6a6a8a;
  margin-bottom: 2px;
}
.meta-item span {
  font-size: 14px;
}

.char-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}
.char-card {
  padding: 12px;
  background: #12121e;
  border-radius: 6px;
  font-size: 13px;
}
.char-name {
  font-weight: 600;
  margin-bottom: 4px;
}
.char-id {
  font-size: 11px;
  color: #5a5a7a;
  margin-bottom: 4px;
}
.char-role {
  font-size: 12px;
  color: #7c8cf0;
  margin-bottom: 4px;
}
.char-trait {
  font-size: 12px;
  color: #a0a0b0;
}
.char-aliases {
  font-size: 11px;
  color: #6a6a8a;
  margin-top: 4px;
}

.act-block {
  margin-bottom: 24px;
}
.act-title {
  font-size: 16px;
  font-weight: 600;
  padding-bottom: 8px;
  border-bottom: 1px solid #2a2a4a;
  margin-bottom: 16px;
  color: #7c8cf0;
}
.scene-block {
  margin-bottom: 20px;
  padding: 12px;
  background: #12121e;
  border-radius: 6px;
}
.scene-heading {
  font-weight: 600;
  margin-bottom: 4px;
}
.scene-meta {
  font-size: 12px;
  color: #6a6a8a;
  margin-bottom: 6px;
}
.scene-summary {
  font-size: 13px;
  color: #a0a0b0;
  margin-bottom: 8px;
  font-style: italic;
}
.scene-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.content-block {
  font-size: 13px;
  line-height: 1.6;
}
.block-action {
  color: #e0e0e0;
}
.block-dialogue {
  margin-left: 16px;
}
.dialogue-char {
  font-weight: 600;
  color: #7cc87c;
}
.dialogue-line {
  margin-left: 16px;
}
.dialogue-delivery {
  margin-left: 16px;
  font-size: 12px;
  color: #8a8aaa;
}
.block-narration {
  color: #8a8aaa;
  font-style: italic;
}
.block-transition {
  text-align: right;
  color: #6a6a8a;
  font-size: 12px;
}

.export-actions {
  display: flex;
  gap: 12px;
}
</style>
