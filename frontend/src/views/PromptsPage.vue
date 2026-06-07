<template>
  <div class="prompts-page container">
    <h2 class="section-title">AI 短剧提示词工坊</h2>
    <p style="color:#8a8aaa;margin-bottom:20px;font-size:13px">基于剧本真实数据，AI 改写为专业视频提示词</p>

    <div class="card" style="margin-bottom:20px">
      <select v-model="wsId" @change="load" class="select-ws">
        <option value="">-- 选择工作区 --</option>
        <option v-for="w in wsList" :key="w.id" :value="w.id">{{ w.title }}</option>
      </select>
    </div>

    <div v-if="screenplay" class="prompts-layout">
      <div class="scene-list card">
        <h3 class="section-title">场景</h3>
        <div v-for="act in screenplay.acts" :key="act.id">
          <h4 style="font-size:13px;color:#7c8cf0;margin:8px 0 4px">{{ act.title }}</h4>
          <div v-for="s in act.scenes" :key="s.id" class="scene-item" :class="{ active: sel === s }" @click="select(s)">
            <div style="font-weight:600;font-size:12px">{{ s.heading }}</div>
            <div style="font-size:10px;color:#6a6a8a">{{ preview(s) }}</div>
            <span v-if="prompts[s.id]" style="font-size:10px;color:#7cc87c">已生成</span>
          </div>
        </div>
        <button class="btn btn-sm btn-secondary" style="margin-top:12px;width:100%" @click="exportAll">批量导出</button>
      </div>

      <div class="prompt-editor card" v-if="sel">
        <h3 class="section-title">{{ sel.heading }}</h3>
        <div class="scene-meta-row">
          <span>{{ sel.interior !== false ? '内景' : '外景' }}</span>
          <span>{{ sel.location }}</span>
          <span>{{ sel.time }}</span>
        </div>

        <div style="margin-bottom:10px">
          <label style="font-size:12px;color:#8a8aaa">视觉风格</label>
          <input v-model="style" class="input-full" />
        </div>
        <div style="margin-bottom:10px">
          <label style="font-size:12px;color:#8a8aaa">镜头</label>
          <div class="preset-chips">
            <button v-for="p in presets" :key="p" class="preset-chip" :class="{ active: cam.includes(p) }" @click="toggleCam(p)">{{ p }}</button>
          </div>
        </div>

        <!-- Scene data reference -->
        <details style="margin-bottom:12px;font-size:12px;color:#6a6a8a">
          <summary style="cursor:pointer">查看原始数据（{{ rawData.length }} 项）</summary>
          <div class="raw-data">{{ rawData }}</div>
        </details>

        <button class="btn btn-primary" @click="generate" :disabled="gen" style="margin-bottom:16px">
          {{ gen ? '生成中...' : '🪄 生成提示词' }}
        </button>

        <div v-if="cur" class="prompt-result">
          <textarea v-model="cur" class="prompt-textarea" rows="6"></textarea>
          <div style="display:flex;gap:8px;margin-top:8px">
            <button class="btn btn-sm btn-primary" @click="cp">{{ cpd ? '已复制' : '复制' }}</button>
            <button class="btn btn-sm btn-secondary" @click="generate">重新生成</button>
            <span style="font-size:11px;color:#6a6a8a;margin-left:auto">{{ cur.length }} 字</span>
          </div>
        </div>
      </div>

      <div v-if="!sel" class="prompt-editor card" style="display:flex;align-items:center;justify-content:center;color:#5a5a7a">
        点击左侧场景开始
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { listWorkspaces } from "../api/client.js";

var wsList = ref([]);
var wsId = ref("");
var screenplay = ref(null);
var sel = ref(null);
var style = ref("中国古代仙侠");
var cam = ref(["中景", "跟拍"]);
var gen = ref(false);
var cur = ref("");
var cpd = ref(false);
var prompts = ref({});
var presets = ["特写", "近景", "中景", "全景", "跟拍", "固定", "浅景深", "慢镜头", "推轨", "俯拍", "仰拍"];

var rawData = computed(function() {
  if (!sel.value) return "";
  var lines = [];
  var s = sel.value;
  lines.push("地点：" + (s.interior !== false ? "内景" : "外景") + " · " + (s.location || "—") + " · " + (s.time || "日"));
  var ids = new Set();
  (s.content || []).forEach(function(b) { if (b.character_id) ids.add(b.character_id); });
  var chars = (screenplay.value?.characters || []).filter(function(c) { return ids.has(c.id); });
  if (chars.length) {
    lines.push("角色：");
    chars.forEach(function(c) {
      var p = [c.name];
      if (c.role) p.push(c.role);
      if (c.personality) p.push(c.personality);
      lines.push("  " + p.join(" · "));
    });
  }
  (s.content || []).forEach(function(b) {
    if (b.type === "action" && b.description) lines.push("动作：" + b.description);
    if (b.type === "dialogue" && b.line) lines.push("对白：" + b.line);
  });
  return lines.join("\n");
});

async function loadList() { try { wsList.value = await listWorkspaces(); } catch {} }
async function load() {
  if (!wsId.value) return;
  try {
    var r = await fetch("/api/workspaces/" + wsId.value);
    var ws = await r.json();
    screenplay.value = ws.screenplay;
    sel.value = null;
  } catch {}
}
function select(s) { sel.value = s; cur.value = prompts.value[s.id] || ""; }
function preview(s) {
  var b = (s.content || []).find(function(x) { return x.type === "action"; });
  return b ? (b.description || "").substring(0, 30) : "";
}
function toggleCam(p) {
  var i = cam.value.indexOf(p);
  if (i >= 0) cam.value.splice(i, 1); else cam.value.push(p);
}

async function generate() {
  if (!sel.value) return;
  gen.value = true;
  try {
    var s = sel.value;
    var actions = [];
    var dialogues = [];
    (s.content || []).forEach(function(b) {
      if (b.type === "action" && b.description) actions.push(b.description);
      if (b.type === "dialogue" && b.line) {
        var name = "";
        var ch = (screenplay.value?.characters || []).find(function(c) { return c.id === b.character_id; });
        if (ch) name = ch.name;
        dialogues.push((name ? name + "：" : "") + b.line);
      }
    });
    var ids = new Set();
    (s.content || []).forEach(function(b) { if (b.character_id) ids.add(b.character_id); });
    var chars = (screenplay.value?.characters || []).filter(function(c) { return ids.has(c.id); }).map(function(c) {
      return { name: c.name, role: c.role, personality: c.personality, gender: c.gender, age: c.age };
    });

    var resp = await fetch("/api/prompts/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        heading: s.heading || '', location: s.location || '', time: s.time || '日',
        interior: s.interior !== false, summary: s.summary || '',
        actions: actions, dialogue_lines: dialogues,
        characters: chars, style: style.value,
      })
    });
    if (!resp.ok) throw new Error("Generation failed");
    var data = await resp.json();
    var p = data.scene_prompt_cn;
    if (cam.value.length) p += "\n\n镜头：" + cam.value.join("、");
    cur.value = p;
    prompts.value[s.id] = p;
  } catch(e) {
    cur.value = "生成失败：" + (e.message || "未知错误");
  } finally { gen.value = false; }
}

async function cp() {
  try { await navigator.clipboard.writeText(cur.value); cpd.value = true; setTimeout(function() { cpd.value = false; }, 2000); } catch {}
}
function exportAll() {
  var all = [];
  if (screenplay.value?.acts) {
    screenplay.value.acts.forEach(function(a) {
      a.scenes.forEach(function(s) {
        if (prompts.value[s.id]) all.push(s.heading + "\n" + prompts.value[s.id]);
      });
    });
  }
  if (!all.length) return;
  var blob = new Blob([all.join("\n\n---\n\n")], { type: "text/plain;charset=utf-8" });
  var url = URL.createObjectURL(blob);
  var el = document.createElement("a");
  el.href = url; el.download = "prompts.txt";
  document.body.appendChild(el); el.click(); document.body.removeChild(el);
  URL.revokeObjectURL(url);
}
loadList();
</script>

<style scoped>
.prompts-page { padding-top: 24px; padding-bottom: 64px; }
.prompts-layout { display: grid; grid-template-columns: 260px 1fr; gap: 20px; align-items: start; }
.select-ws { width: 100%; padding: 8px 12px; background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 6px; color: #e0e0e0; font-size: 13px; font-family: inherit; outline: none; }
.select-ws:focus { border-color: #4a5ae0; }
.scene-list { max-height: 70vh; overflow-y: auto; }
.scene-item { padding: 8px 12px; border-radius: 6px; cursor: pointer; margin-bottom: 4px; border: 1px solid transparent; }
.scene-item:hover { background: #1a1a2e; }
.scene-item.active { background: #1a1a3a; border-color: #4a5ae0; }
.scene-meta-row { display: flex; gap: 12px; font-size: 12px; color: #6a6a8a; margin-bottom: 12px; }
.input-full { width: 100%; padding: 6px 10px; background: #12121e; border: 1px solid #2a2a4a; border-radius: 4px; color: #e0e0e0; font-size: 13px; font-family: inherit; outline: none; }
.input-full:focus { border-color: #4a5ae0; }
.preset-chips { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px; }
.preset-chip { font-size: 11px; padding: 3px 10px; border-radius: 12px; border: 1px solid #3a3a5a; background: transparent; color: #8a8aaa; cursor: pointer; font-family: inherit; }
.preset-chip:hover { border-color: #5a5a7a; }
.preset-chip.active { background: #1a2a4a; border-color: #4a5ae0; color: #a0b4ff; }
.prompt-result { margin-top: 16px; padding-top: 16px; border-top: 1px solid #2a2a4a; }
.prompt-textarea { width: 100%; min-height: 140px; background: #12121e; border: 1px solid #2a2a4a; border-radius: 8px; color: #e0e0e0; font-size: 13px; line-height: 1.7; padding: 12px; font-family: inherit; resize: vertical; outline: none; }
.prompt-textarea:focus { border-color: #4a5ae0; }
.raw-data { padding: 8px 12px; background: #0f0f1a; border-radius: 4px; margin-top: 4px; font-size: 11px; line-height: 1.6; white-space: pre-wrap; }
.btn-sm { font-size: 12px; padding: 4px 12px; }
</style>
