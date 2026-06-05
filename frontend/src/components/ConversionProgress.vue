<template>
  <div class="progress card">
    <h3 class="section-title">转换进度</h3>

    <div class="phase-list">
      <div class="phase-item" :class="phaseClass(prescanPhase)">
        <span class="phase-icon">{{ phaseIcon(prescanPhase) }}</span>
        <span class="phase-label">预扫描：提取角色与章节概要</span>
      </div>

      <div
        v-for="ch in chapters"
        :key="ch.index"
        class="phase-item"
        :class="phaseClass(getChapterPhase(ch.index))"
      >
        <span class="phase-icon">{{ phaseIcon(getChapterPhase(ch.index)) }}</span>
        <span class="phase-label">第{{ ch.index }}章「{{ ch.title }}」转换中...</span>
      </div>

      <div class="phase-item" :class="phaseClass(donePhase)">
        <span class="phase-icon">{{ phaseIcon(donePhase) }}</span>
        <span class="phase-label">组装：场景拼接与连续性校验</span>
      </div>
    </div>

    <div v-if="phase === 'converting'" class="progress-bar">
      <div class="progress-fill" :style="{ width: progressPct + '%' }"></div>
    </div>
    <div v-if="phase === 'converting'" class="progress-text">
      已完成 {{ Object.keys(chapterResults).length }} / {{ chapters.length }} 章（{{ progressPct }}%）
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  phase: String,
  chapters: Array,
  chapterResults: Object,
});

const prescanPhase = computed(() => {
  if (props.phase === "prescan") return "active";
  if (["converting", "assembling", "done"].includes(props.phase)) return "done";
  return "pending";
});

const donePhase = computed(() => {
  if (props.phase === "done") return "done";
  if (props.phase === "assembling") return "active";
  return "pending";
});

const progressPct = computed(() => {
  if (!props.chapters?.length) return 0;
  const done = Object.keys(props.chapterResults).length;
  return Math.round((done / props.chapters.length) * 100);
});

function getChapterPhase(index) {
  if (props.chapterResults[index]) return "done";
  if (props.phase === "converting") return "active";
  return "pending";
}

function phaseClass(s) {
  if (s === "done") return "phase-done";
  if (s === "active") return "phase-active";
  return "phase-pending";
}

function phaseIcon(s) {
  if (s === "done") return "✓";
  if (s === "active") return "▶";
  return "○";
}
</script>

<style scoped>
.phase-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}
.phase-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  transition: background 0.3s;
}
.phase-icon {
  width: 20px;
  text-align: center;
  font-weight: bold;
  flex-shrink: 0;
}
.phase-label {
  flex: 1;
}
.phase-done {
  color: #7cc87c;
}
.phase-done .phase-icon {
  color: #4aae4a;
}
.phase-active {
  background: #1a2a4a;
  color: #a0b4ff;
}
.phase-active .phase-icon {
  color: #7c8cf0;
}
.phase-pending {
  color: #5a5a7a;
}
.progress-bar {
  height: 6px;
  background: #2a2a4a;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4a5ae0, #7c8cf0);
  border-radius: 3px;
  transition: width 0.5s ease;
}
.progress-text {
  font-size: 12px;
  color: #6a6a8a;
  text-align: center;
}
</style>