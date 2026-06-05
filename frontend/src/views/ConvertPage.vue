<template>
  <div class="convert-page container">
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

const converting = ref(false);
const phase = ref("idle"); // idle | prescan | converting | assembling | done | error
const chapters = ref([]);
const chapterResults = ref({});
const result = ref(null);
const error = ref(null);

const warnings = computed(() => {
  if (!result.value || !result.value.warnings) return [];
  return result.value.warnings;
});

async function handleSubmit(data) {
  converting.value = true;
  error.value = null;
  result.value = null;
  chapterResults.value = {};

  try {
    phase.value = "prescan";
    const parsed = await parseChapters(data.text, data.title, data.author);
    chapters.value = parsed.chapters || [];

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

    // Use raw text if chapters were not parsed correctly
    if (!novel.chapters.length) {
      novel.chapters = [{ index: 1, title: "全文", text: data.text }];
    }

    phase.value = "assembling";
    const screenplay = await convertNovel(novel);
    result.value = screenplay;
    phase.value = "done";
  } catch (e) {
    error.value = e.message || "转换过程出错";
    phase.value = "error";
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
</style>
