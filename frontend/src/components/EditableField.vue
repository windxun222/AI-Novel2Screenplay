<template>
  <span v-if="!editing" class="editable" :class="{ empty: !displayValue }" @click="startEdit" :title="label || '点击编辑'">
    {{ displayValue || (label ? '点击添加' + label : '点击编辑') }}
  </span>
  <input
    v-else
    ref="inputEl"
    class="editable-input"
    :value="modelValue"
    @blur="finishEdit"
    @keyup.enter="finishEdit"
    @keyup.escape="cancelEdit"
  />
</template>

<script setup>
import { ref, computed, nextTick } from "vue";

const props = defineProps({
  value: String,
  label: String,
});

const emit = defineEmits(["change"]);

const editing = ref(false);
const inputEl = ref(null);
const modelValue = ref(props.value || "");

const displayValue = computed(() => props.value || "");

async function startEdit() {
  modelValue.value = props.value || "";
  editing.value = true;
  await nextTick();
  if (inputEl.value) {
    inputEl.value.focus();
    inputEl.value.select();
  }
}

function finishEdit() {
  editing.value = false;
  const newVal = modelValue.value.trim();
  if (newVal !== (props.value || "")) {
    emit("change", newVal || null);
  }
}

function cancelEdit() {
  editing.value = false;
  modelValue.value = props.value || "";
}
</script>

<style scoped>
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
</style>
