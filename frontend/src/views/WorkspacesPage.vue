<template>
  <div class="workspaces container">
    <div class="page-header">
      <h2 class="section-title">工作区</h2>
      <button class="btn btn-primary" @click="handleNew">新建工作区</button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">加载中...</div>

    <!-- Empty state -->
    <div v-else-if="list.length === 0" class="empty">
      <p>暂无工作区</p>
      <p class="empty-hint">点击「新建工作区」开始创建项目</p>
    </div>

    <!-- Workspace list -->
    <div v-else class="ws-list">
      <div
        v-for="ws in list"
        :key="ws.id"
        class="ws-card card"
        @click="handleOpen(ws)"
      >
        <div class="ws-info">
          <h3 class="ws-title">{{ ws.title }}</h3>
          <div class="ws-meta">
            <span v-if="ws.author" class="ws-author">{{ ws.author }}</span>
            <span class="ws-chapters">{{ ws.chapter_count }} 章</span>
            <span class="ws-status" :class="'status-' + ws.status">{{ statusLabel(ws.status) }}</span>
            <span class="ws-date">{{ formatDate(ws.updated_at) }}</span>
          </div>
        </div>
        <button class="btn btn-danger btn-sm" @click.stop="handleDelete(ws)">删除</button>
      </div>
    </div>

    <!-- Delete confirmation modal -->
    <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
      <div class="modal card">
        <p>确定要删除工作区「{{ deleteTarget.title }}」吗？此操作不可撤销。</p>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="deleteTarget = null">取消</button>
          <button class="btn btn-danger" @click="confirmDelete">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useWorkspace } from "../composables/useWorkspace.js";

const router = useRouter();
const workspace = useWorkspace();

const list = ref([]);
const loading = ref(true);
const deleteTarget = ref(null);

onMounted(async () => {
  await refresh();
});

async function refresh() {
  loading.value = true;
  try {
    list.value = await workspace.list();
  } catch {
    list.value = [];
  } finally {
    loading.value = false;
  }
}

async function handleNew() {
  workspace.reset();
  router.push("/convert");
}

async function handleOpen(ws) {
  try {
    await workspace.load(ws.id);
    router.push("/convert");
  } catch {
    // workspace not found, refresh list
    await refresh();
  }
}

function handleDelete(ws) {
  deleteTarget.value = ws;
}

async function confirmDelete() {
  if (!deleteTarget.value) return;
  try {
    await workspace.deleteWorkspace(deleteTarget.value.id);
    deleteTarget.value = null;
    await refresh();
  } catch {
    deleteTarget.value = null;
  }
}

function statusLabel(s) {
  const map = { draft: "草稿", converting: "转换中", completed: "已完成", error: "出错" };
  return map[s] || s;
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
</script>

<style scoped>
.workspaces {
  padding-top: 24px;
  padding-bottom: 64px;
  max-width: 800px;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}
.loading, .empty {
  text-align: center;
  padding: 48px 0;
  color: #8a8aaa;
}
.empty-hint {
  font-size: 13px;
  margin-top: 8px;
  color: #6a6a8a;
}
.ws-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.ws-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: border-color 0.15s;
}
.ws-card:hover {
  border-color: #4a5ae0;
}
.ws-title {
  font-size: 15px;
  margin-bottom: 6px;
}
.ws-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #8a8aaa;
}
.ws-date {
  color: #6a6a8a;
}
.status-draft { color: #8a8aaa; }
.status-converting { color: #d0b06a; }
.status-completed { color: #7cc87c; }
.status-error { color: #d06a6a; }

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
  max-width: 400px;
  text-align: center;
}
.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 16px;
}
.btn-sm {
  font-size: 12px;
  padding: 4px 12px;
}
.btn-danger {
  background: #5a2a2a;
  color: #e07070;
  border: 1px solid #7a3a3a;
}
.btn-danger:hover {
  background: #6a3a3a;
}
</style>
