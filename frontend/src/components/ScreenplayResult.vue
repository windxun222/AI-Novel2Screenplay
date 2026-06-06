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
        <br />3. 小说文本是否包含至少 1 章内容，且章节标记正确（如 "第一章"、"第1章"）
      </p>
    </div>

    <!-- Success state -->
    <div v-if="screenplay" class="result-success">
      <!-- Warnings -->
      <div v-if="warnings.length" class="result-warnings card">
        <h3 class="section-title" style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
          <span>连续性警告</span>
          <span class="filter-chips">
            <button class="filter-chip" :class="{ active: warnFilter === 'all' }" @click="warnFilter = 'all'">全部 {{ warnCounts.all }}</button>
            <button class="filter-chip info" :class="{ active: warnFilter === 'info' }" @click="warnFilter = 'info'">提示 {{ warnCounts.info }}</button>
            <button class="filter-chip warning" :class="{ active: warnFilter === 'warning' }" @click="warnFilter = 'warning'">警告 {{ warnCounts.warning }}</button>
            <button class="filter-chip error" :class="{ active: warnFilter === 'error' }" @click="warnFilter = 'error'">错误 {{ warnCounts.error }}</button>
          </span>
        </h3>
        <div
          v-for="(w, i) in filteredWarnings"
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
            <EditableField :value="screenplay.metadata?.title" @change="(v) => updateMeta('title', v)" />
          </div>
          <div class="meta-item">
            <label>来源</label>
            <EditableField :value="screenplay.metadata?.source" @change="(v) => updateMeta('source', v)" />
          </div>
          <div class="meta-item">
            <label>作者</label>
            <EditableField :value="screenplay.metadata?.author" @change="(v) => updateMeta('author', v)" />
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
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
        <h3 class="section-title" style="margin-bottom:0">角色表（{{ screenplay.characters.length }}）</h3>
        <button class="btn btn-sm btn-secondary" @click="addCharacter">+ 添加角色</button>
        <button class="btn btn-sm" :class="mergeMode ? 'btn-primary' : 'btn-secondary'" @click="toggleMerge">
          {{ mergeMode ? '取消合并' : '合并角色' }}
        </button>
        <span v-if="mergeMode && mergeSelected.length === 1" class="warn-info" style="font-size:12px;padding:2px 8px;border-radius:4px">
          请选择第二个角色合并到「{{ mergeSelected[0].name }}」
        </span>
      </div>
        <div class="char-grid">
          <div v-for="c in screenplay.characters" :key="c.id" class="char-card"
            :class="{ 'char-selected': mergeSelected.includes(c), 'char-mergeable': mergeMode }"
            @click="mergeMode ? onMergeSelect(c) : null">
            <div class="char-name">
              <EditableField :value="c.name" @change="(v) => updateChar(c, 'name', v)" />
            </div>
            <button class="btn-char-delete" @click.stop="deleteCharacter(c)" title="删除角色">&times;</button>
            <div class="char-id">{{ c.id }}</div>
            <div v-if="c.role || isCharEditing(c, 'role')" class="char-role">
              <EditableField label="角色" :value="c.role" @change="(v) => updateChar(c, 'role', v)" />
            </div>
            <div v-if="c.personality || isCharEditing(c, 'personality')" class="char-trait">
              <EditableField label="性格" :value="c.personality" @change="(v) => updateChar(c, 'personality', v)" />
            </div>
            <div v-if="c.aliases?.length || isCharEditing(c, 'aliases')" class="char-aliases">
              别名：
              <EditableField :value="c.aliases?.join(', ')" @change="(v) => updateCharAliases(c, v)" />
            </div>
          </div>
        </div>
      </div>

      <!-- Scenes -->
      <div class="result-scenes card">
        <h3 class="section-title">剧本内容</h3>
        <div v-for="act in screenplay.acts" :key="act.id" class="act-block">
          <h4 class="act-title">
            <EditableField :value="act.title" @change="(v) => updateAct(act, 'title', v)" />
          </h4>
          <div v-for="scene in act.scenes" :key="scene.id" class="scene-block">
            <div class="scene-heading">
              <EditableField :value="scene.heading" @change="(v) => updateScene(scene, 'heading', v)" />
            </div>
            <div class="scene-meta">
              {{ scene.interior ? "内景" : "外景" }} |
              <EditableField :value="scene.location" @change="(v) => updateScene(scene, 'location', v)" /> |
              <EditableField :value="scene.time" @change="(v) => updateScene(scene, 'time', v)" />
            </div>
            <div v-if="scene.summary || isSceneEditing(scene, 'summary')" class="scene-summary">
              <EditableField :value="scene.summary" @change="(v) => updateScene(scene, 'summary', v)" />
            </div>
            <div class="scene-content">
              <div
                v-for="(block, bi) in scene.content"
                :key="bi"
                class="content-block"
                :class="'block-' + block.type"
              >
                <!-- Action -->
                <div v-if="block.type === 'action'" class="block-action">
                  <EditableField :value="block.description" @change="(v) => updateBlock(screenplay, block, 'description', v)" />
                </div>
                <!-- Dialogue -->
                <div v-if="block.type === 'dialogue'" class="block-dialogue">
                  <span class="dialogue-char">{{ getCharName(block.character_id) }}</span>
                  <div class="dialogue-line">
                    <EditableField :value="block.line" @change="(v) => updateBlock(screenplay, block, 'line', v)" />
                  </div>
                  <div v-if="block.delivery || isBlockEditing(block, 'delivery')" class="dialogue-delivery">
                    （<EditableField :value="block.delivery" @change="(v) => updateBlock(screenplay, block, 'delivery', v)" />）
                  </div>
                </div>
                <!-- Narration -->
                <div v-if="block.type === 'narration'" class="block-narration">
                  V.O. <EditableField :value="block.description" @change="(v) => updateBlock(screenplay, block, 'description', v)" />
                </div>
                <!-- Transition -->
                <div v-if="block.type === 'transition'" class="block-transition">
                  <EditableField :value="block.description" @change="(v) => updateBlock(screenplay, block, 'description', v)" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Merge confirm modal -->
      <div v-if="mergeConfirmVisible" class="modal-overlay" @click.self="mergeConfirmVisible = false">
        <div class="modal card">
          <p>确定要将「{{ mergeSelected[1]?.name }}」合并到「{{ mergeSelected[0]?.name }}」吗？</p>
          <p style="font-size:12px;color:#8a8aaa">被合并角色的别名、性格等属性将合并到目标角色中，被合并角色将被删除。</p>
          <div class="modal-actions">
            <button class="btn btn-secondary" @click="mergeConfirmVisible = false">取消</button>
            <button class="btn btn-primary" @click="doMerge">确认合并</button>
          </div>
        </div>
      </div>
      
      <!-- Export -->
      <div class="result-export card">
        <h3 class="section-title">导出</h3>
        <div class="export-actions">
          <button class="btn btn-primary" @click="copyYAML">
            {{ copied ? "已复制" : "复制 YAML" }}
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
import { ref, computed, watch, reactive } from "vue";
import { useWorkspace } from "../composables/useWorkspace.js";
import EditableField from "./EditableField.vue";

const props = defineProps({
  screenplay: Object,
  error: String,
  warnings: Array,
});

const ws = useWorkspace();
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

// ── Warning filtering ──
const warnFilter = ref("all");

const warnCounts = computed(() => {
  var all = (props.warnings || []).length;
  var info = 0, warning = 0, error = 0;
  (props.warnings || []).forEach(w => { if (w.level === 'info') info++; else if (w.level === 'warning') warning++; else if (w.level === 'error') error++; });
  return { all, info, warning, error };
});

const filteredWarnings = computed(() => {
  if (warnFilter.value === 'all') return props.warnings || [];
  return (props.warnings || []).filter(w => w.level === warnFilter.value);
});

// ── Inline editing ──
let saveTimer = null;
// ── Character CRUD ──
const mergeMode = ref(false);
const mergeSelected = reactive([]);
const mergeConfirmVisible = ref(false);

function toggleMerge() {
  if (mergeMode.value) {
    mergeSelected.splice(0);
  }
  mergeMode.value = !mergeMode.value;
}

function onMergeSelect(c) {
  if (!mergeMode.value) return;
  if (mergeSelected.includes(c)) {
    mergeSelected.splice(mergeSelected.indexOf(c), 1);
  } else if (mergeSelected.length < 2) {
    mergeSelected.push(c);
  }
  if (mergeSelected.length === 2) {
    mergeConfirmVisible.value = true;
  }
}

function doMerge() {
  if (mergeSelected.length !== 2 || !props.screenplay?.characters) return;
  const [target, source] = mergeSelected;
  // Merge aliases
  if (source.aliases?.length) {
    target.aliases = [...(target.aliases || []), ...source.aliases.filter(a => !(target.aliases || []).includes(a))];
  }
  // Merge fields (target takes priority)
  if (!target.role && source.role) target.role = source.role;
  if (!target.gender && source.gender) target.gender = source.gender;
  if (!target.age && source.age) target.age = source.age;
  if (!target.personality && source.personality) target.personality = source.personality;
  if (!target.background && source.background) target.background = source.background;
  if (!target.notes && source.notes) target.notes = source.notes;
  if (source.name && !(target.aliases || []).includes(source.name)) {
    target.aliases = [...(target.aliases || []), source.name];
  }
  // Remove source character
  var idx = props.screenplay.characters.indexOf(source);
  if (idx >= 0) props.screenplay.characters.splice(idx, 1);
  mergeSelected.splice(0);
  mergeMode.value = false;
  mergeConfirmVisible.value = false;
  scheduleSave();
}

function addCharacter() {
  if (!props.screenplay?.characters) return;
  var maxId = 0;
  props.screenplay.characters.forEach(c => {
    var m = c.id?.match(/char_(\d+)/);
    if (m) maxId = Math.max(maxId, parseInt(m[1]));
  });
  var newChar = {
    id: `char_${String(maxId + 1).padStart(3, "0")}`,
    name: "新角色",
    aliases: [],
    role: "",
    gender: "",
    age: "",
    personality: "",
    background: "",
    notes: "",
  };
  props.screenplay.characters.push(newChar);
  scheduleSave();
}

function deleteCharacter(c) {
  if (!props.screenplay?.characters) return;
  var idx = props.screenplay.characters.indexOf(c);
  if (idx >= 0) {
    props.screenplay.characters.splice(idx, 1);
    scheduleSave();
  }
}

function scheduleSave() {
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    ws.state.screenplay = props.screenplay;
    ws.touch();
    ws.save().catch(() => {});
  }, 1000);
}

function updateMeta(field, value) {
  if (props.screenplay?.metadata) {
    props.screenplay.metadata[field] = value;
    scheduleSave();
  }
}

function updateChar(c, field, value) {
  c[field] = value || null;
  scheduleSave();
}

function updateCharAliases(c, value) {
  c.aliases = value ? value.split(/[,，]s*/) : [];
  scheduleSave();
}

function updateAct(act, field, value) {
  act[field] = value;
  scheduleSave();
}

function updateScene(scene, field, value) {
  scene[field] = value;
  scheduleSave();
}

function updateBlock(_, block, field, value) {
  block[field] = value;
  scheduleSave();
}

// Helpers for conditional display
function isCharEditing(c, field) {
  return c[field] !== undefined && c[field] !== null;
}
function isSceneEditing(scene, field) {
  return scene[field] !== undefined && scene[field] !== null && scene[field] !== "";
}
function isBlockEditing(block, field) {
  return block[field] !== undefined && block[field] !== null && block[field] !== "";
}

// ── YAML export ──
async function copyYAML() {
  try {
    const yaml = toYAML(props.screenplay);
    await navigator.clipboard.writeText(yaml);
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
  } catch {}
}

function downloadYAML() {
  const yaml = toYAML(props.screenplay);
  const blob = new Blob([yaml], { type: "text/yaml;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = (props.screenplay?.metadata?.title || "screenplay") + ".yaml";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function toYAML(screenplay) {
  if (!screenplay) return "";
  const lines = [];
  const I = (n, s) => "  ".repeat(n) + s;
  const esc = (v) => {
    if (v == null) return "";
    const s = String(v);
    if (/[:#{}[\]&*!|>'\"@`,\-]/.test(s) || s.includes("\n") || /^\s/.test(s) || /\s$/.test(s)) {
      return JSON.stringify(s);
    }
    return s;
  };

  lines.push("screenplay:");
  const m = screenplay.metadata;
  if (m) {
    lines.push(I(1, "metadata:"));
    lines.push(I(2, `title: ${esc(m.title)}`));
    if (m.source) lines.push(I(2, `source: ${esc(m.source)}`));
    if (m.author) lines.push(I(2, `author: ${esc(m.author)}`));
    lines.push(I(2, `adapter: ${esc(m.adapter || "AI Novel2Screenplay")}`));
    lines.push(I(2, `created_at: ${esc(m.created_at)}`));
    lines.push(I(2, `chapter_count: ${m.chapter_count ?? 0}`));
    lines.push(I(2, `version: ${esc(m.version || "1.0")}`));
  }

  const chars = screenplay.characters || [];
  lines.push(I(1, "characters:"));
  if (chars.length === 0) {
    lines.push(I(2, "[]"));
  } else {
    for (const c of chars) {
      lines.push(I(2, `- id: ${esc(c.id)}`));
      lines.push(I(3, `name: ${esc(c.name)}`));
      if (c.aliases?.length) {
        lines.push(I(3, `aliases: [${c.aliases.map(esc).join(", ")}]`));
      }
      if (c.role) lines.push(I(3, `role: ${esc(c.role)}`));
      if (c.gender) lines.push(I(3, `gender: ${esc(c.gender)}`));
      if (c.age) lines.push(I(3, `age: ${esc(c.age)}`));
      if (c.personality) lines.push(I(3, `personality: ${esc(c.personality)}`));
      if (c.background) lines.push(I(3, `background: ${esc(c.background)}`));
      if (c.notes) lines.push(I(3, `notes: ${esc(c.notes)}`));
    }
  }

  const acts = screenplay.acts || [];
  lines.push(I(1, "acts:"));
  if (acts.length === 0) {
    lines.push(I(2, "[]"));
  } else {
    for (const act of acts) {
      lines.push(I(2, `- id: ${esc(act.id)}`));
      if (act.title) lines.push(I(3, `title: ${esc(act.title)}`));
      if (act.summary) lines.push(I(3, `summary: ${esc(act.summary)}`));
      lines.push(I(3, "scenes:"));
      if (!act.scenes?.length) {
        lines.push(I(4, "[]"));
      } else {
        for (const scene of act.scenes) {
          lines.push(I(4, `- id: ${esc(scene.id)}`));
          lines.push(I(5, `number: ${scene.number}`));
          lines.push(I(5, `heading: ${esc(scene.heading)}`));
          lines.push(I(5, `location: ${esc(scene.location)}`));
          lines.push(I(5, `time: ${esc(scene.time)}`));
          lines.push(I(5, `interior: ${scene.interior ? "true" : "false"}`));
          if (scene.summary) lines.push(I(5, `summary: ${esc(scene.summary)}`));
          lines.push(I(5, `chapter_index: ${scene.chapter_index ?? 0}`));
          lines.push(I(5, "content:"));
          if (!scene.content?.length) {
            lines.push(I(6, "[]"));
          } else {
            for (const block of scene.content) {
              lines.push(I(6, `- type: ${esc(block.type)}`));
              if (block.description) lines.push(I(7, `description: ${esc(block.description)}`));
              if (block.character_id) lines.push(I(7, `character_id: ${esc(block.character_id)}`));
              if (block.line) lines.push(I(7, `line: ${esc(block.line)}`));
              if (block.delivery) lines.push(I(7, `delivery: ${esc(block.delivery)}`));
              if (block.transition_type) lines.push(I(7, `transition_type: ${esc(block.transition_type)}`));
            }
          }
        }
      }
    }
  }

  const warnings = screenplay.warnings || [];
  lines.push(I(1, "warnings:"));
  if (warnings.length === 0) {
    lines.push(I(2, "[]"));
  } else {
    for (const w of warnings) {
      lines.push(I(2, `- level: ${esc(w.level)}`));
      lines.push(I(3, `type: ${esc(w.type)}`));
      lines.push(I(3, `message: ${esc(w.message)}`));
      if (w.locations?.length) {
        lines.push(I(3, `locations: [${w.locations.map(esc).join(", ")}]`));
      }
    }
  }

  return lines.join("\n") + "\n";
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

.char-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}
.char-card {
  position: relative;
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

/* ── EditableField ── */
.editable {
  cursor: pointer;
  padding: 1px 4px;
  border-radius: 4px;
  transition: background 0.15s;
  display: inline-block;
  min-width: 1em;
  border: 1px solid transparent;
}
.editable:hover {
  background: #2a2a4a;
  border-color: #3a3a5a;
}
.editable.empty {
  color: #5a5a7a;
  font-style: italic;
}
.editable-input {
  background: #1a1a2e;
  color: #e0e0e0;
  border: 1px solid #4a5ae0;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: inherit;
  font-family: inherit;
  width: 100%;
  min-width: 100px;
  outline: none;
}
.char-selected {
  border: 2px solid #4a5ae0 !important;
  background: #1a1a4a !important;
}
.char-mergeable {
  cursor: pointer;
}
.char-mergeable:hover {
  border-color: #5a6af0;
}
.btn-char-delete {
  position: absolute;
  top: 6px;
  right: 8px;
  background: none;
  border: none;
  color: #6a6a8a;
  font-size: 16px;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}
.btn-char-delete:hover {
  color: #e07070;
}
.btn-sm {
  font-size: 12px;
  padding: 4px 12px;
}
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.modal {
  max-width: 420px;
  text-align: center;
}
.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 16px;
}

/* ── Warning filter chips ── */
.filter-chips { display: flex; gap: 4px; }
.filter-chip { font-size: 11px; padding: 2px 10px; border-radius: 10px; border: 1px solid #3a3a5a; background: transparent; color: #8a8aaa; cursor: pointer; font-family: inherit; transition: all 0.15s; }
.filter-chip:hover { border-color: #5a5a7a; color: #c0c0d0; }
.filter-chip.active { border-color: #4a5ae0; color: #a0b4ff; background: #1a1a3a; }
.filter-chip.info.active { border-color: #4a8ad0; color: #6a9ad0; background: #1a2a3a; }
.filter-chip.warning.active { border-color: #c0a040; color: #d0b06a; background: #2a2a1a; }
.filter-chip.error.active { border-color: #c04040; color: #d06a6a; background: #3a1a1a; }
</style>
