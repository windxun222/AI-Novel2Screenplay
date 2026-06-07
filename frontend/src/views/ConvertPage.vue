/** 7Cow — 小说转剧本工具 — ConvertPage.vue
 * 
 * 功能说明（动态更新）：
 * - 支持逐章转换模式（可逐章审查），或一口气全部转换模式。
 * - 逐章转换流程下，在 pre-scan 之后增加角色审核步骤：可对角色表进行增、删、改，并验证删除角色是否已在章节中出现。
 * - 逐章转换结果按章节流式展示，每章可折叠。
 * - 逐章转换进度自动保存到工作区，支持断点续转。
 */

/** @format **/

<template>
  <div class="convert-page container">
    <!-- ── 工作区头部（标题可编辑）── -->
    <div class="ws-header" v-if="ws.state.currentId">
      <input class="ws-title-input" v-model="editableTitle" @change="onTitleChange" @keyup.enter="$event.target.blur()" />
      <span class="ws-badge" :class="ws.state.isDirty ? 'dirty' : 'saved'">
        {{ ws.state.isDirty ? '未保存' : '已保存' }}
      </span>
      <button class="btn btn-sm btn-secondary" @click="handleSave" :disabled="converting">保存</button>
    </div>

    <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
      <h2 class="section-title" style="margin-bottom:0">开始转换</h2>
      <label class="mode-toggle">
        <input type="checkbox" v-model="stepMode" :disabled="converting" />
        <span>逐章转换（可逐章审查）</span>
      </label>
    </div>

    <NovelInput
      @submit="handleSubmit"
      :disabled="converting"
    />

    <!-- ── 一口气全部转换的进度条 ── -->
    <ConversionProgress
      v-if="converting && !stepMode"
      :phase="phase"
      :chapters="chapters"
      :chapterResults="chapterResults"
    />

    <!-- ══════════════════════════════════════════════════════════════ -->
    <!-- 逐章转换面板                                                      -->
    <!-- ══════════════════════════════════════════════════════════════ -->
    <div v-if="stepMode && stepPhase !== 'idle'" class="step-panel card">
      <h3 class="section-title">逐章转换</h3>

      <!-- ── 预扫描结果（仅在审核阶段外显示）── -->
      <div v-if="preScanChars.length && stepPhase !== 'review-chars'" class="step-info">
        <p style="color:#7cc87c;margin-bottom:8px">✅ 预扫描完成，发现 {{ preScanChars.length }} 个角色</p>
      </div>

      <!-- ── 角色审核 Panels ── -->
      <div v-if="stepPhase === 'review-chars'" class="char-review">
        <h4 style="font-size:15px;margin-bottom:14px;color:#a0b4ff">角色审核 — 请确认或修改角色表后继续</h4>
        <div class="char-grid">
          <div v-for="(c, ci) in preScanChars" :key="ci" class="char-card">
            <div class="char-name">
              <EditableField :value="c.name" @change="(v) => { c.name = v; onCharChanged(); }" />
            </div>
            <div class="char-id">{{ c.id || '(待分配)' }}</div>
            <div v-if="c.role || isReviewEditing(c, 'role')" class="char-role">
              <EditableField label="角色" :value="c.role || ''" @change="(v) => { c.role = v; onCharChanged(); }" />
            </div>
            <div v-if="c.personality || isReviewEditing(c, 'personality')" class="char-trait">
              <EditableField label="性格" :value="c.personality || ''" @change="(v) => { c.personality = v; onCharChanged(); }" />
            </div>
            <div v-if="(c.aliases && c.aliases.length) || isReviewEditing(c, 'aliases')" class="char-aliases">
              别名：
              <EditableField :value="(c.aliases || []).join(', ')" @change="(v) => updateCharReviewAliases(c, v)" />
            </div>
            <button class="btn-char-delete" @click="removeReviewChar(ci, c)" title="删除角色">&times;</button>
          </div>
        </div>
        <div class="char-review-actions" style="margin-top:16px">
          <button class="btn btn-sm btn-secondary" @click="addReviewChar">+ 添加新角色</button>
          <button class="btn btn-primary btn-lg" @click="confirmCharacters" style="margin-left:auto">
            确认角色表 · 开始逐章转换
          </button>
        </div>
      </div>

      <!-- ── 章节流式展示（仅确认角色表后显示）── -->
      <div v-if="stepPhase === 'prescan-done' || stepPhase === 'converting'" class="chapter-stack">
        <div v-for="(ch, i) in stepChapters" :key="ch.index" class="chapter-section" :class="{ 'chapter-done': stepResults[i] }">

          <!-- 章节标题栏（始终可见） -->
          <div class="chapter-header" @click="toggleChapter(i)" style="cursor:pointer">
            <span class="ch-toggle">{{ expandedChapters[i] ? '▼' : '▶' }}</span>
            <span class="ch-num">第{{ ch.index || i + 1 }}章</span>
            <span class="ch-title">{{ ch.title }}</span>
            <span class="ch-status">{{ getStepChapterStatus(i) }}</span>
            <button
              v-if="!stepResults[i] && canConvert(i)"
              class="btn btn-sm btn-primary"
              @click.stop="convertCurrentChapter(i)"
              :disabled="converting"
            >
              转换本章
            </button>
          </div>

          <!-- 已折叠但已有结果 ── 显示摘要 -->
          <div v-if="!expandedChapters[i] && stepResults[i]" class="chapter-body-collapsed" @click="toggleChapter(i)" style="cursor:pointer">
            <span style="font-size:12px;color:#6a6a8a">{{ getSceneCount(stepResults[i]) }} 场 — 点击展开查看详情</span>
          </div>

          <!-- 展开后每场戏完整展示（可编辑） -->
          <div v-if="expandedChapters[i] && stepResults[i]" class="chapter-body">
            <div class="chapter-scenes">
              <div v-for="(scene, si) in getStepScenes(stepResults[i])" :key="si" class="step-scene-block">
                <div class="scene-hd">
                  <EditableField :value="scene.heading" @change="(v) => updateSceneField(i, si, 'heading', v)" />
                </div>
                <div class="scene-meta">
                  {{ scene.interior !== false ? '内景' : '外景' }}
                  | <EditableField :value="scene.location || ''" @change="(v) => updateSceneField(i, si, 'location', v)" />
                  | <EditableField :value="scene.time || '日'" @change="(v) => updateSceneField(i, si, 'time', v)" />
                </div>
                <div v-if="scene.summary || isEditingScene(i, si, 'summary')" class="scene-sm">
                  <EditableField :value="scene.summary || ''" @change="(v) => updateSceneField(i, si, 'summary', v)" />
                </div>
                <div class="scene-content">
                  <div v-for="(block, bi) in (scene.content || [])" :key="bi" class="content-block" :class="'block-' + block.type">
                    <div v-if="block.type === 'action'" class="block-action">
                      <EditableField :value="block.description || ''" @change="(v) => updateBlockField(i, si, bi, 'description', v)" />
                    </div>
                    <div v-if="block.type === 'dialogue'" class="block-dialogue">
                      <span class="dialogue-char">{{ resolveCharName(block.character_id) }}</span>
                      <div class="dialogue-line">
                        <EditableField :value="block.line || ''" @change="(v) => updateBlockField(i, si, bi, 'line', v)" />
                      </div>
                      <div v-if="block.delivery || isEditingBlock(i, si, bi, 'delivery')" class="dialogue-delivery">
                        （<EditableField :value="block.delivery || ''" @change="(v) => updateBlockField(i, si, bi, 'delivery', v)" />）
                      </div>
                    </div>
                    <div v-if="block.type === 'narration'" class="block-narration">
                      V.O. <EditableField :value="block.description || ''" @change="(v) => updateBlockField(i, si, bi, 'description', v)" />
                    </div>
                    <div v-if="block.type === 'transition'" class="block-transition">
                      <EditableField :value="block.description || ''" @change="(v) => updateBlockField(i, si, bi, 'description', v)" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── 角色表（确认后始终显示，方便随时调整）── -->
      <div v-if="(stepPhase === 'prescan-done' || stepPhase === 'converting') && preScanChars.length" class="result-chars card" style="margin-top:20px">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
          <h3 class="section-title" style="margin:0">角色表（{{ preScanChars.length }}）</h3>
          <button class="btn btn-sm btn-secondary" @click="addReviewChar">+ 添加新角色</button>
        </div>
        <div class="char-grid">
          <div v-for="(c, ci) in preScanChars" :key="ci" class="char-card">
            <div class="char-name">
              <EditableField :value="c.name" @change="(v) => { c.name = v; onCharChanged(); }" />
            </div>
            <div class="char-id">{{ c.id || '(待分配)' }}</div>
            <div v-if="c.role || isReviewEditing(c, 'role')" class="char-role">
              <EditableField label="角色" :value="c.role || ''" @change="(v) => { c.role = v; onCharChanged(); }" />
            </div>
            <div v-if="c.personality || isReviewEditing(c, 'personality')" class="char-trait">
              <EditableField label="性格" :value="c.personality || ''" @change="(v) => { c.personality = v; onCharChanged(); }" />
            </div>
            <div v-if="(c.aliases && c.aliases.length) || isReviewEditing(c, 'aliases')" class="char-aliases">
              别名：
              <EditableField :value="(c.aliases || []).join(', ')" @change="(v) => updateCharReviewAliases(c, v)" />
            </div>
            <button class="btn-char-delete" @click="removeReviewChar(ci, c)" title="删除角色">&times;</button>
          </div>
        </div>
      </div>

      <!-- ── 追加新章节 ── -->
      <div v-if="(stepPhase === 'prescan-done' || stepPhase === 'converting') && stepChapters.length > 0" class="append-section" style="margin-top:20px;padding-top:16px;border-top:1px dashed #2a2a4a">
        <button class="btn btn-sm btn-secondary" @click="showAppendInput = !showAppendInput">
          {{ showAppendInput ? '取消追加' : '+ 追加新章节' }}
        </button>
        <div v-if="showAppendInput" style="margin-top:12px">
          <textarea
            v-model="appendText"
            class="append-textarea"
            placeholder="在此粘贴新的章节内容（例如第4-5章）……&#10;&#10;支持与初始输入相同的章节标题格式：第X章 / 第一章 / Chapter X"
            rows="8"
          ></textarea>
          <div style="display:flex;align-items:center;gap:12px;margin-top:8px">
            <button class="btn btn-primary" @click="doAppendChapters" :disabled="!appendText.trim()">
              解析并追加到项目
            </button>
            <span style="font-size:12px;color:#6a6a8a">{{ appendText.length }} 字</span>
          </div>
        </div>
      </div>

      <!-- ── 完成按钮（至少一章转换完毕即可生成当前进度剧本）── -->
      <div v-if="anyChapterDone" class="step-finish" style="margin-top:20px;text-align:center">
        <button class="btn btn-primary btn-lg" @click="finishStepConversion" :disabled="converting">
          {{ allChaptersDone ? '完成转换 · 生成完整剧本' : '生成当前进度剧本（' + doneChapterCount + '/' + stepChapters.length + ' 章）' }}
        </button>
        <p v-if="!allChaptersDone" style="font-size:12px;color:#6a6a8a;margin-top:8px">
          未转换的章节将跳过，您可以随时回来继续处理
        </p>
      </div>
    </div>

    <!-- ── 最终结果（通用）── -->
    <ScreenplayResult
      v-if="result || error"
      :screenplay="result"
      :error="error"
      :warnings="warnings"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import NovelInput from "../components/NovelInput.vue";
import ConversionProgress from "../components/ConversionProgress.vue";
import ScreenplayResult from "../components/ScreenplayResult.vue";
import EditableField from "../components/EditableField.vue";
import { parseChapters, convertNovel, preScan, convertChapter, assembleStep } from "../api/client.js";
import { useWorkspace } from "../composables/useWorkspace.js";

const ws = useWorkspace();

const converting = ref(false);
const phase = ref("idle");
const chapters = ref([]);
const chapterResults = ref({});
const result = ref(null);
const error = ref(null);

// ── 可编辑的工作区标题 ──
const editableTitle = ref(ws.state.title);
watch(() => ws.state.title, (v) => { editableTitle.value = v; });
function onTitleChange() { ws.state.title = editableTitle.value; ws.touch(); ws.save().catch(() => {}); }

const warnings = computed(() => {
  if (!result.value || !result.value.warnings) return [];
  return result.value.warnings;
});

// ══════════════════════════════════════════════════════════════
// 逐章转换模式状态
// ══════════════════════════════════════════════════════════════
const stepMode = ref(false);
const stepPhase = ref("idle");
const stepChapters = ref([]);
const stepResults = ref({});          // { chapterIndex: { raw_yaml, scenes, new_characters } }
const preScanChars = ref([]);          // 审核中的角色表
const preScanSummaries = ref({});      // AI 生成的章概要
const expandedChapters = ref({});
const showAppendInput = ref(false);
const appendText = ref("");
function isReviewEditing(c, field) { return c[field] !== undefined && c[field] !== null && c[field] !== ''; }      // 展开/折叠状态

const allChaptersDone = computed(() => {
  var ch = stepChapters.value;
  return ch.length > 0 && ch.every((_, i) => stepResults.value[i]);
});

const anyChapterDone = computed(() => {
  return stepChapters.value.some((_, i) => stepResults.value[i]);
});

const doneChapterCount = computed(() => {
  var count = 0;
  for (var i = 0; i < stepChapters.value.length; i++) {
    if (stepResults.value[i]) count++;
  }
  return count;
});

function toggleChapter(i) {
  expandedChapters.value[i] = !expandedChapters.value[i];
}

function canConvert(i) {
  // Any chapter can be converted at any time (partial completion support)
  return true;
}

function getStepChapterStatus(i) {
  if (stepResults.value[i]) return '✅ 已完成';
  if (canConvert(i)) return '▶ 待转换';
  return '○ 待处理';
}

function getStepScenes(result) {
  return result && result.scenes ? result.scenes : [];
}

function getSceneCount(result) {
  return getStepScenes(result).length;
}

// ── 用角色表把 char_XXX 解析为人名 ──
function resolveCharName(id) {
  if (!id) return '?';
  var found = preScanChars.value.find(c => (c.id || '').toLowerCase() === id.toLowerCase());
  if (found) return found.name;
  return id;
}

// ── 判断某个字段是否正在编辑中（用于条件显示）──
function isEditingScene(ci, si, field) {
  var s = getStepScenes(stepResults.value[ci])[si];
  return s && s[field] !== undefined && s[field] !== null && s[field] !== '';
}
function isEditingBlock(ci, si, bi, field) {
  var s = getStepScenes(stepResults.value[ci])[si];
  var b = s && s.content && s.content[bi];
  return b && b[field] !== undefined && b[field] !== null && b[field] !== '';
}

// ── 编辑场景 / 内容块字段（修改后自动保存）──
function updateSceneField(i, si, field, value) {
  var scenes = getStepScenes(stepResults.value[i]);
  if (scenes[si]) { scenes[si][field] = value; }
  scheduleStepSave();
}
function updateBlockField(i, si, bi, field, value) {
  var scenes = getStepScenes(stepResults.value[i]);
  var block = scenes[si] && scenes[si].content && scenes[si].content[bi];
  if (block) { block[field] = value; }
  scheduleStepSave();
}

var _saveTimer = null;
function scheduleStepSave() {
  if (_saveTimer) clearTimeout(_saveTimer);
  _saveTimer = setTimeout(() => {
    ws.state.stepResults = { ...stepResults.value };
    ws.state.stepPhase = stepPhase.value;
    ws.touch();
    ws.save().catch(() => {});
  }, 1000);
}

// ══════════════════════════════════════════════════════════════
// 提交入口：区分全量 / 逐章
// ══════════════════════════════════════════════════════════════
async function handleSubmit(data) {
  if (stepMode.value) { await startStepByStep(data); return; }

  converting.value = true; error.value = null; result.value = null; chapterResults.value = {};

  try {
    ws.state.rawText = data.text; ws.state.title = data.title || '未命名作品'; ws.state.author = data.author || '';
    ws.state.status = 'converting'; ws.state.isDirty = true;

    phase.value = 'prescan';
    const parsed = await parseChapters(data.text, data.title, data.author);
    chapters.value = parsed.chapters || [];
    ws.state.chapters = chapters.value; ws.state.status = 'converting'; await ws.save().catch(() => {});

    phase.value = 'converting';
    const novel = {
      title: data.title || '未命名作品', author: data.author || '',
      chapters: (parsed.chapters || []).map((ch, i) => ({
        index: ch.index || i + 1, title: ch.title || '第' + (i + 1) + '章', text: ch.text || data.text,
      })),
    };
    if (!novel.chapters.length) novel.chapters = [{ index: 1, title: '全文', text: data.text }];

    phase.value = 'assembling';
    const screenplay = await convertNovel(novel);
    result.value = screenplay;
    ws.state.screenplay = screenplay; ws.state.status = 'completed'; await ws.save().catch(() => {});
    phase.value = 'done';
  } catch (e) {
    error.value = e.message || '转换过程出错'; phase.value = 'error'; ws.state.status = 'error'; await ws.save().catch(() => {});
  } finally { converting.value = false; }
}

// ── Append new chapters ──
async function doAppendChapters() {
  var raw = appendText.value.trim();
  if (!raw) return;
  
  try {
    // Parse the new text
    var parsed = await parseChapters(raw, ws.state.title, ws.state.author);
    var newChapters = parsed.chapters || [];
    if (!newChapters.length) {
      error.value = '未能从文本中解析出章节，请确保使用正确的章节标题格式（如"第X章"）';
      return;
    }
    
    // Find the next chapter index
    var maxIdx = 0;
    stepChapters.value.forEach(function(ch) {
      var idx = ch.index || 0;
      if (idx > maxIdx) maxIdx = idx;
    });
    
    // Append new chapters with adjusted indices
    newChapters.forEach(function(ch, i) {
      stepChapters.value.push({
        index: maxIdx + i + 1,
        title: ch.title || ('第' + (maxIdx + i + 1) + '章'),
        text: ch.text || '',
      });
    });
    
    // Clear input
    appendText.value = '';
    showAppendInput.value = false;
    
    // Save to workspace
    ws.state.chapters = stepChapters.value;
    ws.touch();
    await ws.save().catch(function() {});
  } catch(e) {
    error.value = e.message || '章节解析失败';
  }
}

// ══════════════════════════════════════════════════════════════
// 逐章转换 — Pre-scan + 角色审核 + 逐章转换
// ══════════════════════════════════════════════════════════════
async function startStepByStep(data) {
  converting.value = true; error.value = null; result.value = null; stepResults.value = {};

  try {
    ws.state.rawText = data.text; ws.state.title = data.title || '未命名作品'; ws.state.author = data.author || ''; ws.touch();

    const parsed = await parseChapters(data.text, data.title, data.author);
    stepChapters.value = parsed.chapters || [];
    if (!stepChapters.value.length) stepChapters.value = [{ index: 1, title: '全文', text: data.text }];
    ws.state.chapters = stepChapters.value; await ws.save().catch(() => {});

    phase.value = 'prescan';
    const novel = {
      title: data.title || '未命名作品', author: data.author || '',
      chapters: stepChapters.value.map((ch, i) => ({
        index: ch.index || i + 1, title: ch.title || '第' + (i + 1) + '章', text: ch.text || data.text,
      })),
    };

    const scanResult = await preScan(novel);
    preScanChars.value = scanResult.characters || [];
    preScanSummaries.value = scanResult.chapter_summaries || {};
    // 进入角色审核阶段
    stepPhase.value = 'review-chars';
  } catch (e) {
    error.value = e.message || '预扫描失败'; stepPhase.value = 'idle';
  } finally { converting.value = false; }
}

// ── 角色审核阶段的增 / 删 / 改 ──
function onCharChanged() {
  ws.touch(); ws.save().catch(() => {});
}

function updateCharReviewAliases(c, value) {
  c.aliases = value ? value.split(/[,，]\s*/).filter(Boolean) : [];
  onCharChanged();
}

function addReviewChar() {
  // Find the smallest unused char_XXX ID (gap-filling)
  var usedIds = new Set();
  preScanChars.value.forEach(c => {
    if (c.id) usedIds.add(c.id);
  });
  var newId = '';
  for (var n = 1; n <= 999; n++) {
    var candidate = 'char_' + String(n).padStart(3, '0');
    if (!usedIds.has(candidate)) { newId = candidate; break; }
  }
  if (!newId) newId = 'char_' + String(preScanChars.value.length + 1).padStart(3, '0');
  preScanChars.value.push({ id: newId, name: '新角色', aliases: [], role: '', personality: '' });
  onCharChanged();
}

function removeReviewChar(ci, c) {
  // 检查角色是否已在已转换章节的场景中出现
  if (!c.name || c.name === '新角色') {
    preScanChars.value.splice(ci, 1);
    onCharChanged();
    return;
  }
  // 根据角色姓名（name）查找所有已转换章节中引用的 character_id
  var nameLower = c.name.toLowerCase();
  var usedIn = [];
  for (var key in stepResults.value) {
    var scenes = getStepScenes(stepResults.value[key]);
    for (var si = 0; si < scenes.length; si++) {
      for (var bi = 0; bi < (scenes[si].content || []).length; bi++) {
        if (scenes[si].content[bi].character_id &&
            scenes[si].content[bi].character_id.toLowerCase().indexOf(nameLower) >= 0) {
          usedIn.push('第' + (Number(key) + 1) + '章');
          break;
        }
      }
    }
  }
  if (usedIn.length > 0) {
    alert('角色「' + c.name + '」已在以下章节的对白中出现：\n' + usedIn.join('、') + '\n无法删除，但你可以编辑它的信息。');
    return;
  }
  preScanChars.value.splice(ci, 1);
  onCharChanged();
}

function confirmCharacters() {
  // 保存当前角色表到工作区，方便后续 reopen 恢复
  ws.state.stepPhase = 'prescan-done';
  ws.touch(); ws.save().catch(() => {});
  stepPhase.value = 'prescan-done';
}

// ── 逐章转换当前选中章节 ──
async function convertCurrentChapter(i) {
  if (i >= stepChapters.value.length) return;
  converting.value = true; phase.value = 'converting';
  var ch = stepChapters.value[i];

  try {
    var prevSummaries = {};
    var chIdx = ch.index || i + 1;
    for (var k in preScanSummaries.value) {
      if (Number(k) < chIdx) prevSummaries[k] = preScanSummaries.value[k];
    }

    var res = await convertChapter(chIdx, ch.text || '', preScanChars.value, prevSummaries);
    stepResults.value[i] = res;
    expandedChapters.value[i] = true;

    // 持久化进度
    ws.state.stepResults = { ...stepResults.value };
    ws.state.stepPhase = stepPhase.value;
    ws.touch(); await ws.save().catch(() => {});
  } catch (e) {
    error.value = e.message || '第' + (ch.index || i + 1) + '章转换失败';
  } finally {
    converting.value = false; phase.value = 'prescan-done';
  }
}

// ── 完成逐章转换 → 组装剧本（跳过未转换章节）──
async function finishStepConversion() {
  converting.value = true; phase.value = 'assembling';

  try {
    // Only include chapters that have been converted
    var convertedChapters = stepChapters.value
      .map((ch, i) => ({
        index: ch.index || i + 1,
        title: ch.title || '第' + (i + 1) + '章',
        text: (stepResults.value[i] && stepResults.value[i].raw_yaml) || '',
      }))
      .filter(ch => ch.text);  // Skip empty (unconverted) chapters

    if (convertedChapters.length === 0) {
      error.value = '请先转换至少一章后再生成剧本';
      converting.value = false; phase.value = 'prescan-done';
      return;
    }

    var novel = {
      title: ws.state.title, author: ws.state.author,
      chapters: convertedChapters,
      characters: preScanChars.value,
    };

    var screenplay = await assembleStep(novel);
    result.value = screenplay;
    ws.state.screenplay = screenplay; ws.state.status = 'completed'; await ws.save().catch(() => {});
    // Don't exit step mode — user can continue converting more chapters
    stepPhase.value = 'done'; phase.value = 'done';
  } catch (e) {
    error.value = e.message || '组装失败'; phase.value = 'error';
  } finally { converting.value = false; }
}

// ══════════════════════════════════════════════════════════════
// 工作区恢复：支持断点续转
// ══════════════════════════════════════════════════════════════
function restoreFromWorkspace() {
  // Always reset step-by-step state first to prevent cross-workspace leakage
  stepMode.value = false;
  stepPhase.value = 'idle';
  stepResults.value = {};
  stepChapters.value = [];
  preScanChars.value = [];
  preScanSummaries.value = {};
  expandedChapters.value = {};
  
  if (ws.state.currentId && ws.state.chapters?.length) {
    chapters.value = ws.state.chapters;
    if (ws.state.stepResults && Object.keys(ws.state.stepResults).length > 0) {
      stepResults.value = ws.state.stepResults;
      stepChapters.value = ws.state.chapters;
      if (ws.state.stepPhase) stepPhase.value = ws.state.stepPhase;
      stepMode.value = true;
      phase.value = 'done';
    } else if (ws.state.screenplay) {
      result.value = ws.state.screenplay; phase.value = 'done';
    } else {
      phase.value = 'done';
    }
  }
}
onMounted(() => restoreFromWorkspace());
watch(() => ws.state.currentId, () => restoreFromWorkspace());

async function handleSave() {
  try {
    ws.state.status = result.value ? 'completed' : (converting.value ? 'converting' : 'draft');
    // Only persist step data if actually in step-by-step mode
    if (stepMode.value) {
      ws.state.stepResults = { ...stepResults.value };
      ws.state.stepPhase = stepPhase.value;
    } else {
      ws.state.stepResults = {};
      ws.state.stepPhase = 'idle';
    }
    await ws.save();
  } catch (e) {}
}
</script>

<style scoped>
.convert-page { padding-top: 32px; padding-bottom: 64px; }
.ws-header { display: flex; align-items: center; gap: 12px; padding: 10px 16px; background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 8px; margin-bottom: 20px; }
.ws-title-input { font-weight: 600; font-size: 14px; background: transparent; border: 1px solid transparent; color: #e0e0e0; padding: 2px 8px; border-radius: 4px; outline: none; min-width: 120px; }
.ws-title-input:hover { border-color: #3a3a5a; }
.ws-title-input:focus { border-color: #4a5ae0; background: #12121e; }
.ws-badge { font-size: 11px; padding: 2px 8px; border-radius: 4px; }
.ws-badge.saved { color: #7cc87c; background: #1a2a1a; }
.ws-badge.dirty { color: #d0b06a; background: #2a2a1a; }
.btn-sm { font-size: 12px; padding: 4px 12px; }
.btn-lg { font-size: 15px; padding: 10px 28px; }
.mode-toggle { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #a0a0b0; cursor: pointer; user-select: none; }
.mode-toggle input { cursor: pointer; }

/* ── 逐章面板 ── */
.step-panel { margin-top: 20px; background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 8px; padding: 24px; }
.step-info { font-size: 14px; }

/* ── 角色表（与 ScreenplayResult 一致的卡片设计）── */
.char-review { margin-bottom: 20px; padding-bottom: 20px; border-bottom: 2px solid #4a5ae0; }
.char-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }
.char-card { padding: 12px; background: #12121e; border-radius: 6px; font-size: 13px; position: relative; border: 1px solid #1a1a3a; }
.char-name { font-weight: 600; margin-bottom: 4px; }
.char-id { font-size: 11px; color: #5a5a7a; margin-bottom: 4px; }
.char-role { font-size: 12px; color: #7c8cf0; margin-bottom: 4px; }
.char-trait { font-size: 12px; color: #a0a0b0; }
.char-aliases { font-size: 11px; color: #6a6a8a; margin-top: 4px; }
.btn-char-delete { position: absolute; top: 6px; right: 8px; background: none; border: none; color: #6a6a8a; font-size: 16px; cursor: pointer; padding: 0 4px; line-height: 1; }
.btn-char-delete:hover { color: #e07070; }
.char-review-actions { display: flex; align-items: center; gap: 12px; }

/* ── 章节流式展示 ── */
.chapter-stack { display: flex; flex-direction: column; gap: 0; margin-top: 12px; }
.chapter-section { border: 1px solid #2a2a4a; border-radius: 8px; margin-bottom: 10px; overflow: hidden; }
.chapter-section.chapter-done { border-color: #2a5a2a; }
.chapter-header { display: flex; align-items: center; gap: 10px; padding: 12px 16px; background: #12121e; font-size: 13px; }
.chapter-done .chapter-header { background: #121a1e; }
.ch-toggle { font-size: 10px; color: #6a6a8a; width: 16px; flex-shrink: 0; }
.ch-num { font-weight: 600; color: #7c8cf0; flex-shrink: 0; }
.ch-title { flex: 1; color: #e0e0e0; }
.ch-status { font-size: 11px; color: #6a6a8a; flex-shrink: 0; min-width: 80px; text-align: right; }
.chapter-done .ch-status { color: #7cc87c; }
.chapter-body { padding: 16px 20px 20px 36px; border-top: 1px solid #2a2a4a; }
.chapter-body-collapsed { padding: 8px 20px 10px 36px; border-top: 1px solid #2a2a4a; color: #6a6a8a; }
.chapter-body-collapsed:hover { background: #12121e; }

/* ── 场景展示（与 ScreenplayResult 一致）── */
.chapter-scenes { display: flex; flex-direction: column; gap: 16px; }
.step-scene-block { padding: 12px; background: #0f0f1a; border-radius: 6px; border: 1px solid #1a1a3a; }
.scene-hd { font-weight: 600; margin-bottom: 4px; font-size: 14px; }
.scene-meta { font-size: 12px; color: #6a6a8a; margin-bottom: 6px; }
.scene-sm { font-size: 13px; color: #a0a0b0; margin-bottom: 8px; font-style: italic; }
.scene-content { display: flex; flex-direction: column; gap: 8px; }
.content-block { font-size: 13px; line-height: 1.6; }
.block-action { color: #e0e0e0; }
.block-dialogue { margin-left: 16px; }
.dialogue-char { font-weight: 600; color: #7cc87c; }
.dialogue-line { margin-left: 16px; }
.dialogue-delivery { margin-left: 16px; font-size: 12px; color: #8a8aaa; }
.block-narration { color: #8a8aaa; font-style: italic; }
.block-transition { text-align: right; color: #6a6a8a; font-size: 12px; }

/* ── 紧凑角色表 ── */
.compact-chars { margin-top: 20px; border: 1px solid #2a2a4a; border-radius: 8px; overflow: hidden; }
.compact-chars-header { display: flex; align-items: center; gap: 8px; padding: 10px 14px; background: #12121e; cursor: pointer; font-size: 13px; font-weight: 600; color: #a0b4ff; }
.compact-chars-header:hover { background: #1a1a2e; }
.compact-chars-body { padding: 8px 12px; display: flex; flex-direction: column; gap: 6px; }
.compact-char-row { display: flex; align-items: center; gap: 6px; }
.compact-input { flex: 1; min-width: 60px; font-size: 12px; padding: 4px 8px; background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 4px; color: #e0e0e0; font-family: inherit; outline: none; }
.compact-input:focus { border-color: #4a5ae0; }
.compact-name { flex: 0 0 100px; font-weight: 600; }
.compact-role { flex: 0 0 100px; }
.compact-del { background: none; border: none; color: #5a5a7a; font-size: 14px; cursor: pointer; padding: 0 4px; }
.compact-del:hover { color: #e07070; }

/* ── Append section ── */
.append-textarea {
  width: 100%;
  min-height: 140px;
  resize: vertical;
  line-height: 1.7;
  font-size: 13px;
  padding: 10px;
  background: #12121e;
  border: 1px solid #2a2a4a;
  border-radius: 6px;
  color: #e0e0e0;
  font-family: inherit;
  outline: none;
}
.append-textarea:focus { border-color: #4a5ae0; }
</style>
