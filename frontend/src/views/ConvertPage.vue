<template>
  <div class="convert-page container">
    <!-- Workspace header -->
    <div class="ws-header" v-if="ws.state.currentId">
      <span class="ws-title">{{ ws.state.title }}</span>
      <span class="ws-badge" :class="ws.state.isDirty ? 'dirty' : 'saved'">
        {{ ws.state.isDirty ? '未保存' : '已保存' }}
      </span>
      <button class="btn btn-sm btn-secondary" @click="handleSave" :disabled="converting">
        保存
      </button>
    </div>

    <h2 class="section-title">开始转换</h2>

    <!-- Step 1: Input -->
    <NovelInput
      @submit="handleSubmit"
      :disabled="converting"
    />

    <!-- Step 2: Progress -->
    <ConversionProgress
      v-if="converting"
      :phase="phase"
      :chapters="chapters"
      :chapterResults="chapterResults"
    />

    <!-- Step 3: Result -->
    <ScreenplayResult
      v-if="result || error"
      :screenplay="result"
      :error="error"
      :warnings="warnings"
    />
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import NovelInput from "../components/NovelInput.vue";
import ConversionProgress from "../components/ConversionProgress.vue";
import ScreenplayResult from "../components/ScreenplayResult.vue";
import { parseChapters, convertNovel } from "../api/client.js";
import { useWorkspace } from "../composables/useWorkspace.js";

const ws = useWorkspace();

const converting = ref(false);
const phase = ref("idle");
const chapters = ref([]);
const chapterResults = ref({});
const result = ref(null);
const error = ref(null);

const warnings = computed(() => {
  if (!result.value || !result.value.warnings) return [];
  return result.value.warnings;
});

async function handleSave() {
  try {
    ws.state.status = result.value ? "completed" : (converting.value ? "converting" : "draft");
    await ws.save();
  } catch (e) {
    // silent fail in UI
  }
}

async function handleSubmit(data) {
  converting.value = true;
  error.value = null;
  result.value = null;
  chapterResults.value = {};

  try {
    // Update workspace state from input
    ws.state.rawText = data.text;
    ws.state.title = data.title || "未命名作品";
    ws.state.author = data.author || "";
    ws.state.status = "converting";
    ws.state.isDirty = true;

    phase.value = "prescan";
    const parsed = await parseChapters(data.text, data.title, data.author);
    chapters.value = parsed.chapters || [];

    // Auto-save after parsing (raw text + chapters)
    ws.state.chapters = chapters.value;
    ws.state.status = "converting";
    await ws.save().catch(() => {});

    phase.value = "converting";
    const novel = {
      title: data.title || "未命名作品",
      author: data.author || "",
      chapters: (parsed.chapters || []).map((ch, i) => ({
        index: ch.index || i + 1,
        title: ch.title || `第${i + 1}章`,
        text: ch.text || data.text,
      })),
    };

    if (!novel.chapters.length) {
      novel.chapters = [{ index: 1, title: "全文", text: data.text }];
    }

    phase.value = "assembling";
    const screenplay = await convertNovel(novel);
    result.value = screenplay;

    // Auto-save after conversion (full result)
    ws.state.screenplay = screenplay;
    ws.state.status = "completed";
    await ws.save().catch(() => {});

    phase.value = "done";
  } catch (e) {
    error.value = e.message || "转换过程出错";
    phase.value = "error";
    ws.state.status = "error";
    await ws.save().catch(() => {});
  } finally {
    converting.value = false;
  }
}
</script>

<style scoped>
.convert-page {
  padding-top: 32px;
  padding-bottom: 64px;
}
.ws-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: #1a1a2e;
  border: 1px solid #2a2a4a;
  border-radius: 8px;
  margin-bottom: 20px;
}
.ws-title {
  font-weight: 600;
  font-size: 14px;
}
.ws-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
}
.ws-badge.saved {
  color: #7cc87c;
  background: #1a2a1a;
}
.ws-badge.dirty {
  color: #d0b06a;
  background: #2a2a1a;
}
.btn-sm {
  font-size: 12px;
  padding: 4px 12px;
  margin-left: auto;
}
</style>
