<template>
  <div class="novel-input card">
    <div class="input-meta">
      <input
        v-model="title"
        placeholder="作品名称（可选）"
        class="input-title"
        :disabled="disabled"
      />
      <input
        v-model="author"
        placeholder="作者（可选）"
        class="input-author"
        :disabled="disabled"
      />
    </div>

    <textarea
      v-model="text"
      placeholder="将你的小说文本粘贴到这里，至少 3 章内容。&#10;&#10;支持格式：&#10;第1章 / 第一章 / Chapter 1 等标记&#10;&#10;或者上传 .txt 文件："
      class="input-textarea"
      rows="12"
      :disabled="disabled"
    ></textarea>

    <div class="input-actions">
      <label class="btn btn-secondary upload-btn">
        <input
          type="file"
          accept=".txt"
          @change="handleFileUpload"
          :disabled="disabled"
          hidden
        />
        上传 .txt 文件
      </label>
      <span class="char-count">{{ text.length }} 字</span>
      <button
        class="btn btn-primary"
        @click="handleSubmit"
        :disabled="disabled || !canSubmit"
      >
        {{ disabled ? "转换中..." : "开始转换" }}
      </button>
    </div>

    <div v-if="error" class="input-error">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

const emit = defineEmits(["submit"]);
const props = defineProps({
  disabled: Boolean,
});

const title = ref("");
const author = ref("");
const text = ref("");
const error = ref("");

const canSubmit = computed(() => text.value.trim().length >= 100);

function handleFileUpload(e) {
  const file = e.target.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (ev) => {
    text.value = ev.target?.result || "";
    error.value = "";
  };
  reader.onerror = () => {
    error.value = "文件读取失败";
  };
  reader.readAsText(file, "UTF-8");
}

function handleSubmit() {
  if (!canSubmit.value) {
    error.value = "请输入至少 100 字的小说内容（建议 3 章以上）";
    return;
  }
  error.value = "";
  emit("submit", {
    title: title.value || "未命名作品",
    author: author.value,
    text: text.value,
  });
}
</script>

<style scoped>
.input-meta {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}
.input-title,
.input-author {
  flex: 1;
}
.input-textarea {
  width: 100%;
  min-height: 240px;
  resize: vertical;
  line-height: 1.7;
  margin-bottom: 12px;
}
.input-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.upload-btn {
  font-size: 13px;
  padding: 8px 16px;
}
.char-count {
  font-size: 12px;
  color: #6a6a8a;
  margin-left: auto;
}
.input-error {
  margin-top: 12px;
  padding: 8px 12px;
  background: #3a1a1a;
  border: 1px solid #5a2a2a;
  border-radius: 6px;
  color: #e07070;
  font-size: 13px;
}
</style>
