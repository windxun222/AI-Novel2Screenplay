<!-- ScreenplayResult.vue — 剧本结果展示，支持场景/内容块增删改 -->
<template>
  <div class="result">
    <div v-if="error" class="result-error card">
      <h3 class="section-title">转换出错</h3>
      <p class="error-message">{{ error }}</p>
    </div>

    <div v-if="screenplay" class="result-success">
      <!-- ── 警告（含筛选）── -->
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
        <div v-for="(w, i) in filteredWarnings" :key="i" class="warning-item" :class="'warn-' + w.level">
          <span class="warn-level">{{ warnLabel(w.level) }}</span>
          <span class="warn-msg">{{ w.message }}</span>
          <span v-if="w.locations?.length" class="warn-locs">场景：{{ w.locations.join(", ") }}</span>
        </div>
      </div>

      <!-- ── 元数据 ── -->
      <div class="result-meta card">
        <h3 class="section-title">剧本元数据</h3>
        <div class="meta-grid">
          <div class="meta-item"><label>标题</label><EditableField :value="screenplay.metadata?.title" @change="(v) => updateMeta('title', v)" /></div>
          <div class="meta-item"><label>来源</label><EditableField :value="screenplay.metadata?.source" @change="(v) => updateMeta('source', v)" /></div>
          <div class="meta-item"><label>作者</label><EditableField :value="screenplay.metadata?.author" @change="(v) => updateMeta('author', v)" /></div>
          <div class="meta-item"><label>章节数</label><span>{{ screenplay.metadata?.chapter_count }}</span></div>
          <div class="meta-item"><label>类型</label><span>{{ screenplay.metadata?.adapter }}</span></div>
          <div class="meta-item"><label>版本</label><span>{{ screenplay.metadata?.version }}</span></div>
        </div>
      </div>

      <!-- ── 角色表 ── -->
      <div class="result-chars card">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
          <h3 class="section-title" style="margin:0">角色表（{{ screenplay.characters?.length || 0 }}）</h3>
          <button class="btn btn-sm btn-secondary" @click="addResultChar">+ 添加角色</button>
          <button class="btn btn-sm" :class="mergeMode ? 'btn-primary' : 'btn-secondary'" @click="toggleMerge">
            {{ mergeMode ? '取消合并' : '合并角色' }}
          </button>
          <span v-if="mergeMode && mergeSelected.length === 1" style="font-size:12px;color:#a0b4ff;padding:2px 8px;background:#1a1a3a;border-radius:4px">
            已选「{{ mergeSelected[0].name }}」，请点击第二个角色
          </span>
        </div>
        <div v-if="!screenplay.characters?.length" style="font-size:13px;color:#6a6a8a;padding:8px 0">暂无角色，点击上方「+ 添加角色」创建</div>
        <div class="char-grid" v-if="screenplay.characters?.length">
          <div v-for="c in screenplay.characters" :key="c.id" class="char-card" :class="{ 'char-merge-selected': mergeSelected.includes(c) }" @click="mergeMode ? onMergeSelect(c) : null" :style="mergeMode ? 'cursor:pointer' : ''">
            <div class="char-name"><EditableField :value="c.name" @change="(v) => updateChar(c, 'name', v)" /></div>
            <button class="btn-char-delete" @click="deleteResultChar(c)" title="删除角色">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
                <path d="M2 4h10M5 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4M11 4v7a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4"/>
              </svg>
            </button>
            <div class="char-id">{{ c.id }}</div>
            <div v-if="c.role || isCharEditing(c, 'role')" class="char-role"><EditableField label="角色" :value="c.role" @change="(v) => updateChar(c, 'role', v)" /></div>
            <div v-if="c.personality || isCharEditing(c, 'personality')" class="char-trait"><EditableField label="性格" :value="c.personality" @change="(v) => updateChar(c, 'personality', v)" /></div>
            <div v-if="c.aliases?.length || isCharEditing(c, 'aliases')" class="char-aliases">别名：<EditableField :value="c.aliases?.join(', ')" @change="(v) => updateCharAliases(c, v)" /></div>
          </div>
        </div>
      </div>

      <!-- ── 剧本内容（场景可增/删）── -->
      <div class="result-scenes card">
        <h3 class="section-title">剧本内容</h3>
        <div v-for="act in screenplay.acts" :key="act.id" class="act-block">
          <h4 class="act-title"><EditableField :value="act.title" @change="(v) => updateAct(act, 'title', v)" /></h4>

          <div v-for="(scene, sIdx) in act.scenes" :key="scene.id" class="scene-block">
            <button class="btn-scene-delete" @click="deleteScene(act, sIdx)" title="删除场景">&times;</button>
            <div class="scene-heading"><EditableField :value="scene.heading" @change="(v) => updateScene(scene, 'heading', v)" /></div>
            <div class="scene-meta">
              {{ scene.interior ? "内景" : "外景" }}
              | <EditableField :value="scene.location" @change="(v) => updateScene(scene, 'location', v)" />
              | <EditableField :value="scene.time" @change="(v) => updateScene(scene, 'time', v)" />
            </div>
            <div v-if="scene.summary || isSceneEditing(scene, 'summary')" class="scene-summary">
              <EditableField :value="scene.summary" @change="(v) => updateScene(scene, 'summary', v)" />
            </div>

            <!-- 内容块列表（每个可删） -->
            <div v-if="scene.content?.length" class="scene-content">
              <div v-for="(block, bi) in scene.content" :key="bi" class="content-block-wrap">
                <button class="btn-block-delete" @click="deleteBlock(scene, bi)" title="删除">&times;</button>
                <div class="content-block" :class="'block-' + block.type">
                  <div v-if="block.type === 'action'" class="block-action">
                    <EditableField :value="block.description || ''" @change="(v) => updateBlock(screenplay, block, 'description', v)" />
                  </div>
                  <div v-if="block.type === 'dialogue'" class="block-dialogue">
                    <span class="dialogue-char">{{ getCharName(block.character_id) }} (<EditableField :value="block.character_id || ''" @change="(v) => updateBlock(screenplay, block, 'character_id', v)" />)</span>
                    <div class="dialogue-line"><EditableField :value="block.line || ''" @change="(v) => updateBlock(screenplay, block, 'line', v)" /></div>
                    <div v-if="block.delivery || isBlockEditing(block, 'delivery')" class="dialogue-delivery">
                      （<EditableField :value="block.delivery || ''" @change="(v) => updateBlock(screenplay, block, 'delivery', v)" />）
                    </div>
                  </div>
                  <div v-if="block.type === 'narration'" class="block-narration">
                    V.O. <EditableField :value="block.description || ''" @change="(v) => updateBlock(screenplay, block, 'description', v)" />
                  </div>
                  <div v-if="block.type === 'transition'" class="block-transition">
                    <EditableField :value="block.description || ''" @change="(v) => updateBlock(screenplay, block, 'description', v)" />
                  </div>
                </div>
              </div>
            </div>

            <!-- 无内容块时提示 -->
            <div v-if="!scene.content?.length" style="font-size:12px;color:#5a5a7a;padding:4px 0">暂无内容块</div>

            <!-- 添加内容块按钮 -->
            <div class="add-block-row">
              <button class="btn btn-sm btn-secondary" @click="addBlock(scene, 'action')">+ 动作</button>
              <button class="btn btn-sm btn-secondary" @click="addBlock(scene, 'dialogue')">+ 对白</button>
              <button class="btn btn-sm btn-secondary" @click="addBlock(scene, 'narration')">+ 旁白</button>
              <button class="btn btn-sm btn-secondary" @click="addBlock(scene, 'transition')">+ 转场</button>
            </div>
          </div>

          <!-- 添加场景按钮（带智能建议） -->
          <div class="add-scene-row">
            <button class="btn btn-sm btn-secondary" @click="toggleAddScene(act)">+ 添加场景</button>
            <div v-if="addSceneTarget === act" class="add-scene-form">
              <select v-model="newScene.location" class="compact-input" style="width:160px">
                <option value="" disabled>-- 选择地点 --</option>
                <option v-for="loc in existingLocations" :key="loc" :value="loc">{{ loc }}</option>
                <option value="__new__">+ 添加新地点...</option>
              </select>
              <input v-if="newScene.location === '__new__'" v-model="newScene.locationCustom" placeholder="输入新地点" class="compact-input" />
              <select v-model="newScene.time" class="compact-input" style="width:120px">
                <option value="" disabled>-- 时间 --</option>
                <option v-for="t in existingTimes" :key="t" :value="t">{{ t }}</option>
                <option value="__new__">+ 添加新时间...</option>
              </select>
              <input v-if="newScene.time === '__new__'" v-model="newScene.timeCustom" placeholder="输入新时间" class="compact-input" />
              <label class="compact-check"><input type="checkbox" v-model="newScene.interior" checked /> 内景</label>
              <button class="btn btn-sm btn-primary" @click="doAddScene(act)">确定</button>
              <button class="btn btn-sm btn-secondary" @click="addSceneTarget = null">取消</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ── 合并确认弹窗 ── -->
      <div v-if="mergeConfirmVisible" class="modal-overlay" @click.self="mergeConfirmVisible = false">
        <div class="modal card">
          <p style="margin-bottom:8px">确定要将「{{ mergeSelected[1]?.name }}」合并到「{{ mergeSelected[0]?.name }}」吗？</p>
          <p style="font-size:12px;color:#8a8aaa;margin-bottom:16px">被合并角色的别名、性格等属性将合并到目标角色中，被合并角色将被删除。</p>
          <div class="modal-actions">
            <button class="btn btn-secondary" @click="mergeConfirmVisible = false">取消</button>
            <button class="btn btn-primary" @click="doMerge">确认合并</button>
          </div>
        </div>
      </div>

      <!-- ── 导出 ── -->
      <div class="result-export card">
        <h3 class="section-title">导出</h3>
        <div class="export-actions">
          <button class="btn btn-primary" @click="copyYAML">{{ copied ? "已复制" : "复制 YAML" }}</button>
          <button class="btn btn-secondary" @click="downloadYAML">下载 YAML 文件</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from "vue";
import EditableField from "./EditableField.vue";
import { useWorkspace } from "../composables/useWorkspace.js";

const props = defineProps({ screenplay: Object, error: String, warnings: Array });
const ws = useWorkspace();
const copied = ref(false);

const charMap = computed(() => {
  const map = {};
  if (props.screenplay?.characters) props.screenplay.characters.forEach(c => { map[c.id] = c.name; });
  return map;
});
function getCharName(id) { return charMap.value[id] || id || "未知"; }

// ── Warning filter ──
const warnFilter = ref("all");
const warnCounts = computed(() => {
  var all = (props.warnings || []).length, info = 0, warning = 0, error = 0;
  (props.warnings || []).forEach(w => { if (w.level === 'info') info++; else if (w.level === 'warning') warning++; else error++; });
  return { all, info, warning, error };
});
const filteredWarnings = computed(() => {
  if (warnFilter.value === 'all') return props.warnings || [];
  return (props.warnings || []).filter(w => w.level === warnFilter.value);
});
function warnLabel(level) {
  const labels = { info: "提示", warning: "警告", error: "错误" };
  return labels[level] || level;
}

// ── Auto-save ──
async function scheduleSave() {
  if (!ws.state.currentId) return;
  try {
    var payload = {
      id: ws.state.currentId,
      title: ws.state.title,
      author: ws.state.author,
      status: ws.state.status,
      raw_text: ws.state.rawText,
      chapters: ws.state.chapters,
      screenplay: JSON.parse(JSON.stringify(props.screenplay)),
      step_results: ws.state.stepResults || {},
    };
    var putResp = await fetch("/api/workspaces/" + ws.state.currentId, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!putResp.ok) throw new Error("PUT failed: " + putResp.status);
    ws.state.isDirty = false;
  } catch(e) {
    console.error('Save failed:', e);
  }
}

function updateMeta(field, value) { if (props.screenplay?.metadata) { props.screenplay.metadata[field] = value; scheduleSave(); } }
function updateChar(c, field, value) { c[field] = value || null; scheduleSave(); }
function updateCharAliases(c, value) { c.aliases = value ? value.split(/[,，]s*/).filter(Boolean) : []; scheduleSave(); }
function addResultChar() {
  if (!props.screenplay?.characters) return;
  var usedIds = new Set();
  props.screenplay.characters.forEach(function(c) { if (c.id) usedIds.add(c.id); });
  var newId = '';
  for (var n = 1; n <= 999; n++) {
    var candidate = 'char_' + String(n).padStart(3, '0');
    if (!usedIds.has(candidate)) { newId = candidate; break; }
  }
  if (!newId) newId = 'char_' + String(props.screenplay.characters.length + 1).padStart(3, '0');
  props.screenplay.characters.push({ id: newId, name: '新角色', aliases: [], role: '', personality: '' });
  scheduleSave();
}

function deleteResultChar(c) {
  if (!props.screenplay?.characters) return;
  var usedIn = [];
  if (props.screenplay.acts) {
    props.screenplay.acts.forEach(function(act) {
      if (act.scenes) act.scenes.forEach(function(scene) {
        if (scene.content) scene.content.forEach(function(block) {
          if (block.character_id && block.character_id === c.id) {
            usedIn.push(scene.heading || scene.id);
          }
        });
      });
    });
  }
  if (usedIn.length > 0) {
    alert('角色「' + c.name + '」在 ' + usedIn.length + ' 处场景对白中被引用，无法删除。可以编辑该角色的信息。');
    return;
  }
  var idx = props.screenplay.characters.indexOf(c);
  if (idx >= 0) {
    props.screenplay.characters.splice(idx, 1);
    scheduleSave();
  }
}

// ── Merge characters ──
var mergeMode = ref(false);
var mergeSelected = reactive([]);
var mergeConfirmVisible = ref(false);

function toggleMerge() {
  if (mergeMode.value) { mergeSelected.splice(0); }
  mergeMode.value = !mergeMode.value;
}

function onMergeSelect(c) {
  if (!mergeMode.value) return;
  if (mergeSelected.includes(c)) {
    var idx = mergeSelected.indexOf(c);
    if (idx >= 0) mergeSelected.splice(idx, 1);
  } else if (mergeSelected.length < 2) {
    mergeSelected.push(c);
  }
  if (mergeSelected.length === 2) {
    mergeConfirmVisible.value = true;
  }
}

function doMerge() {
  if (mergeSelected.length !== 2 || !props.screenplay?.characters) return;
  var target = mergeSelected[0];
  var source = mergeSelected[1];
  // Merge aliases
  if (source.aliases && source.aliases.length) {
    if (!target.aliases) target.aliases = [];
    source.aliases.forEach(function(a) { if (!target.aliases.includes(a)) target.aliases.push(a); });
  }
  // Add source name as alias
  if (source.name && !(target.aliases || []).includes(source.name)) {
    if (!target.aliases) target.aliases = [];
    target.aliases.push(source.name);
  }
  // Fill empty fields
  if (!target.role && source.role) target.role = source.role;
  if (!target.gender && source.gender) target.gender = source.gender;
  if (!target.age && source.age) target.age = source.age;
  if (!target.personality && source.personality) target.personality = source.personality;
  if (!target.background && source.background) target.background = source.background;
  if (!target.notes && source.notes) target.notes = source.notes;
  // Remove source
  var idx = props.screenplay.characters.indexOf(source);
  if (idx >= 0) props.screenplay.characters.splice(idx, 1);
  mergeSelected.splice(0);
  mergeMode.value = false;
  mergeConfirmVisible.value = false;
  scheduleSave();
}

function updateAct(act, field, value) { act[field] = value; scheduleSave(); }
function updateScene(scene, field, value) { scene[field] = value; scheduleSave(); }
function updateBlock(_, block, field, value) { block[field] = value; scheduleSave(); }
function isCharEditing(c, field) { return c[field] !== undefined && c[field] !== null; }
function isSceneEditing(scene, field) { return scene[field] !== undefined && scene[field] !== null && scene[field] !== ""; }
function isBlockEditing(block, field) { return block[field] !== undefined && block[field] !== null && block[field] !== ""; }

// ── Scene / Block CRUD ──
function addBlock(scene, type) {
  if (!scene.content) scene.content = [];
  const block = { type };
  if (type === 'action' || type === 'narration' || type === 'transition') block.description = '';
  if (type === 'dialogue') { block.character_id = ''; block.line = ''; }
  scene.content.push(block);
  scheduleSave();
}

function deleteBlock(scene, bi) {
  if (!scene.content) return;
  scene.content.splice(bi, 1);
  scheduleSave();
}

const addSceneTarget = ref(null);
const newScene = ref({ location: '', time: '日', interior: true });

const existingLocations = computed(() => {
  const set = new Set();
  if (props.screenplay?.acts) {
    props.screenplay.acts.forEach(act => {
      act.scenes?.forEach(s => { if (s.location) set.add(s.location); });
    });
  }
  return [...set];
});

const existingTimes = computed(() => {
  const set = new Set(['晨','日','黄昏','夜']);
  if (props.screenplay?.acts) {
    props.screenplay.acts.forEach(function(act) {
      if (act.scenes) act.scenes.forEach(function(s) { if (s.time) set.add(s.time); });
    });
  }
  return Array.from(set);
});

function toggleAddScene(act) {
  if (addSceneTarget.value === act) { addSceneTarget.value = null; return; }
  addSceneTarget.value = act;
  newScene.value = { location: existingLocations.value[0] || '', locationCustom: '', time: '日', timeCustom: '', interior: true };
}

function doAddScene(act) {
  if (!act.scenes) act.scenes = [];
  const maxNum = act.scenes.reduce((m, s) => Math.max(m, s.number || 0), 0);
  var loc = newScene.value.location === '__new__' ? (newScene.value.locationCustom || '未命名地点') : (newScene.value.location || '未命名地点');
  var tm = newScene.value.time === '__new__' ? (newScene.value.timeCustom || '日') : (newScene.value.time || '日');
  const heading = (newScene.value.interior ? '【内】' : '【外】') + loc + '·' + tm;
  act.scenes.push({
    id: 'scene_' + String(maxNum + 1).padStart(3, '0'),
    number: maxNum + 1,
    heading,
    location: loc,
    time: tm,
    interior: newScene.value.interior,
    summary: '',
    content: [],
    chapter_index: act.scenes[0]?.chapter_index || 1,
  });
  addSceneTarget.value = null;
  scheduleSave();
}

function deleteScene(act, sIdx) {
  if (!act.scenes) return;
  if (!confirm('确定要删除场景「' + (act.scenes[sIdx]?.heading || '') + '」吗？')) return;
  act.scenes.splice(sIdx, 1);
  scheduleSave();
}

// ── YAML export ──
async function copyYAML() {
  try { const y = toYAML(props.screenplay); await navigator.clipboard.writeText(y); copied.value = true; setTimeout(() => copied.value = false, 2000); } catch {}
}
function downloadYAML() {
  const y = toYAML(props.screenplay);
  const blob = new Blob([y], { type: "text/yaml;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = (props.screenplay?.metadata?.title || "screenplay") + ".yaml";
  document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url);
}
function toYAML(s) {
  if (!s) return "";
  var NL = String.fromCharCode(10);
  var out = [];
  var I = function(n, t) { var prefix = ""; for (var i = 0; i < n; i++) prefix += "  "; return prefix + t; };
  var esc = function(v) {
    if (v == null) return "";
    return JSON.stringify(String(v));
  };
  out.push("screenplay:");
  var m = s.metadata;
  if (m) {
    out.push(I(1, "metadata:"));
    out.push(I(2, "title: " + esc(m.title)));
    if (m.source) out.push(I(2, "source: " + esc(m.source)));
    if (m.author) out.push(I(2, "author: " + esc(m.author)));
    out.push(I(2, "adapter: " + esc(m.adapter || "AI Novel2Screenplay")));
    out.push(I(2, "created_at: " + esc(m.created_at)));
    out.push(I(2, "chapter_count: " + (m.chapter_count != null ? m.chapter_count : 0)));
    out.push(I(2, "version: " + esc(m.version || "1.0")));
  }
  var chars = s.characters || [];
  out.push(I(1, "characters:"));
  if (!chars.length) { out.push(I(2, "[]")); }
  else chars.forEach(function(c) {
    out.push(I(2, "- id: " + esc(c.id)));
    out.push(I(3, "name: " + esc(c.name)));
    if (c.aliases && c.aliases.length) out.push(I(3, "aliases: [" + c.aliases.map(esc).join(", ") + "]"));
    if (c.role) out.push(I(3, "role: " + esc(c.role)));
    if (c.gender) out.push(I(3, "gender: " + esc(c.gender)));
    if (c.age) out.push(I(3, "age: " + esc(c.age)));
    if (c.personality) out.push(I(3, "personality: " + esc(c.personality)));
    if (c.background) out.push(I(3, "background: " + esc(c.background)));
    if (c.notes) out.push(I(3, "notes: " + esc(c.notes)));
  });
  var acts = s.acts || [];
  out.push(I(1, "acts:"));
  if (!acts.length) { out.push(I(2, "[]")); }
  else acts.forEach(function(act) {
    out.push(I(2, "- id: " + esc(act.id)));
    if (act.title) out.push(I(3, "title: " + esc(act.title)));
    if (act.summary) out.push(I(3, "summary: " + esc(act.summary)));
    out.push(I(3, "scenes:"));
    if (!act.scenes || !act.scenes.length) { out.push(I(4, "[]")); }
    else act.scenes.forEach(function(sc) {
      out.push(I(4, "- id: " + esc(sc.id)));
      out.push(I(5, "number: " + (sc.number != null ? sc.number : 0)));
      out.push(I(5, "heading: " + esc(sc.heading)));
      out.push(I(5, "location: " + esc(sc.location)));
      out.push(I(5, "time: " + esc(sc.time)));
      out.push(I(5, "interior: " + (sc.interior ? "true" : "false")));
      if (sc.summary) out.push(I(5, "summary: " + esc(sc.summary)));
      out.push(I(5, "chapter_index: " + (sc.chapter_index != null ? sc.chapter_index : 0)));
      out.push(I(5, "content:"));
      if (!sc.content || !sc.content.length) { out.push(I(6, "[]")); }
      else sc.content.forEach(function(b) {
        out.push(I(6, "- type: " + esc(b.type)));
        if (b.description) out.push(I(7, "description: " + esc(b.description)));
        if (b.character_id) out.push(I(7, "character_id: " + esc(b.character_id)));
        if (b.line) out.push(I(7, "line: " + esc(b.line)));
        if (b.delivery) out.push(I(7, "delivery: " + esc(b.delivery)));
        if (b.transition_type) out.push(I(7, "transition_type: " + esc(b.transition_type)));
      });
    });
  });
  var warns = s.warnings || [];
  out.push(I(1, "warnings:"));
  if (!warns.length) { out.push(I(2, "[]")); }
  else warns.forEach(function(w) {
    out.push(I(2, "- level: " + esc(w.level)));
    out.push(I(3, "type: " + esc(w.type)));
    out.push(I(3, "message: " + esc(w.message)));
    if (w.locations && w.locations.length) out.push(I(3, "locations: [" + w.locations.map(esc).join(", ") + "]"));
  });
  return out.join(NL) + NL;
}
</script>

<style scoped>
.result { margin-top: 24px; display: flex; flex-direction: column; gap: 20px; }
.result-error { border-color: #5a2a2a; }
.error-message { color: #e07070; margin-bottom: 12px; }

/* ── 警告 ── */
.result-warnings { border-color: #5a4a2a; }
.filter-chips { display: flex; gap: 4px; }
.filter-chip { font-size: 11px; padding: 2px 10px; border-radius: 10px; border: 1px solid #3a3a5a; background: transparent; color: #8a8aaa; cursor: pointer; font-family: inherit; transition: all 0.15s; }
.filter-chip:hover { border-color: #5a5a7a; color: #c0c0d0; }
.filter-chip.active { border-color: #4a5ae0; color: #a0b4ff; background: #1a1a3a; }
.filter-chip.info.active { border-color: #4a8ad0; color: #6a9ad0; background: #1a2a3a; }
.filter-chip.warning.active { border-color: #c0a040; color: #d0b06a; background: #2a2a1a; }
.filter-chip.error.active { border-color: #c04040; color: #d06a6a; background: #3a1a1a; }
.warning-item { padding: 8px 12px; border-radius: 6px; margin-bottom: 6px; font-size: 13px; display: flex; gap: 8px; align-items: flex-start; }
.warn-info { background: #1a2a3a; } .warn-warning { background: #2a2a1a; } .warn-error { background: #3a1a1a; }
.warn-level { font-weight: 600; flex-shrink: 0; min-width: 32px; }
.warn-info .warn-level { color: #6a9ad0; } .warn-warning .warn-level { color: #d0b06a; } .warn-error .warn-level { color: #d06a6a; }
.warn-msg { flex: 1; } .warn-locs { font-size: 11px; color: #6a6a8a; flex-shrink: 0; }

/* ── 元数据 ── */
.meta-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }
.meta-item label { display: block; font-size: 11px; color: #6a6a8a; margin-bottom: 2px; }

/* ── 角色 ── */
.char-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }
.char-card { padding: 12px; background: #12121e; border-radius: 6px; font-size: 13px; position: relative; }
.char-name { font-weight: 600; margin-bottom: 4px; }
.char-id { font-size: 11px; color: #5a5a7a; margin-bottom: 4px; }
.char-role { font-size: 12px; color: #7c8cf0; margin-bottom: 4px; }
.char-trait { font-size: 12px; color: #a0a0b0; }
.char-aliases { font-size: 11px; color: #6a6a8a; margin-top: 4px; }

/* ── 场景 ── */
.act-block { margin-bottom: 24px; }
.act-title { font-size: 16px; font-weight: 600; padding-bottom: 8px; border-bottom: 1px solid #2a2a4a; margin-bottom: 16px; color: #7c8cf0; }
.scene-block { margin-bottom: 16px; padding: 12px; background: #12121e; border-radius: 6px; border: 1px solid #1a1a3a; position: relative; }
.scene-heading { font-weight: 600; margin-bottom: 4px; margin-right: 24px; }
.scene-meta { font-size: 12px; color: #6a6a8a; margin-bottom: 6px; }
.scene-summary { font-size: 13px; color: #a0a0b0; margin-bottom: 8px; font-style: italic; }
.scene-content { display: flex; flex-direction: column; gap: 6px; margin-bottom: 8px; }
.content-block-wrap { position: relative; padding-right: 22px; }
.content-block { font-size: 13px; line-height: 1.6; }
.block-action { color: #e0e0e0; }
.block-dialogue { margin-left: 16px; }
.dialogue-char { font-weight: 600; color: #7cc87c; }
.dialogue-line { margin-left: 16px; }
.dialogue-delivery { margin-left: 16px; font-size: 12px; color: #8a8aaa; }
.block-narration { color: #8a8aaa; font-style: italic; }
.block-transition { text-align: right; color: #6a6a8a; font-size: 12px; }

/* ── Delete buttons ── */
.btn-scene-delete { position: absolute; top: 8px; right: 10px; background: none; border: none; color: #6a6a8a; font-size: 16px; cursor: pointer; padding: 0 4px; line-height: 1; z-index: 2; }
.btn-scene-delete:hover { color: #e07070; }
.btn-block-delete { position: absolute; right: 0; top: 2px; background: none; border: none; color: #4a4a6a; font-size: 12px; cursor: pointer; padding: 0 3px; line-height: 1; }
.btn-block-delete:hover { color: #d06a6a; }

/* ── Add buttons ── */
.add-block-row { display: flex; gap: 6px; margin-top: 8px; padding-top: 8px; border-top: 1px dashed #2a2a4a; }
.add-scene-row { margin-top: 10px; }
.add-scene-form { display: flex; align-items: center; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
.compact-input { font-size: 12px; padding: 4px 8px; background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 4px; color: #e0e0e0; font-family: inherit; outline: none; width: 140px; }
.compact-input:focus { border-color: #4a5ae0; }
.compact-check { font-size: 12px; color: #a0a0b0; display: flex; align-items: center; gap: 4px; cursor: pointer; }

/* ── 导出 ── */
.export-actions { display: flex; gap: 12px; }

/* ── Merge mode ── */
.char-merge-selected { border: 2px solid #4a5ae0 !important; background: #1a1a3a !important; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { max-width: 420px; }
.modal-actions { display: flex; gap: 12px; justify-content: center; margin-top: 8px; }

/* ── Delete button ── */
.btn-char-delete { position: absolute; top: 6px; right: 6px; background: none; border: none; color: #5a5a7a; cursor: pointer; padding: 4px; border-radius: 4px; display: flex; align-items: center; justify-content: center; }
.btn-char-delete:hover { background: #3a1a1a; color: #e07070; }
</style>
