import { reactive } from "vue";

const BASE = "/api/workspaces";

// ── Reactive singleton state ──
const state = reactive({
  /** Currently loaded workspace ID (null = unsaved new) */
  currentId: null,
  /** True when there are unsaved local changes */
  isDirty: false,
  /** Workspace title */
  title: "未命名作品",
  /** Workspace author */
  author: "",
  /** Raw input text */
  rawText: "",
  /** Parsed chapters array */
  chapters: [],
  /** Conversion result (null until converted) */
  screenplay: null,
  /** Workspace status */
  status: "draft",
});

/**
 * Fetch all workspaces (summary list).
 */
async function list() {
  const resp = await fetch(BASE);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

/**
 * Create a new workspace on the backend.
 */
async function create(title, author = "") {
  const body = JSON.stringify({ title, author, status: "draft" });
  const resp = await fetch(BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  const ws = await resp.json();
  Object.assign(state, {
    currentId: ws.id,
    title: ws.title,
    author: ws.author || "",
    rawText: ws.raw_text || "",
    chapters: ws.chapters || [],
    screenplay: ws.screenplay || null,
    status: ws.status,
    isDirty: false,
  });
  return ws;
}

/**
 * Load a full workspace from backend into local state.
 */
async function load(id) {
  const resp = await fetch(`${BASE}/${id}`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  const ws = await resp.json();
  Object.assign(state, {
    currentId: ws.id,
    title: ws.title,
    author: ws.author || "",
    rawText: ws.raw_text || "",
    chapters: ws.chapters || [],
    screenplay: ws.screenplay || null,
    status: ws.status,
    isDirty: false,
  });
  return ws;
}

/**
 * Save current state to backend. Creates if new, updates if existing.
 */
async function save() {
  if (!state.currentId) {
    // First save: create
    const resp = await fetch(BASE, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(_toPayload()),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const ws = await resp.json();
    state.currentId = ws.id;
    state.isDirty = false;
    return ws;
  }
  // Update existing
  const resp = await fetch(`${BASE}/${state.currentId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(_toPayload()),
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  const ws = await resp.json();
  state.isDirty = false;
  return ws;
}

/**
 * Delete a workspace by ID.
 */
async function deleteWorkspace(id) {
  const resp = await fetch(`${BASE}/${id}`, { method: "DELETE" });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  if (state.currentId === id) {
    _reset();
  }
}

/**
 * Reset local state (for starting fresh).
 */
function _reset() {
  Object.assign(state, {
    currentId: null,
    isDirty: false,
    title: "未命名作品",
    author: "",
    rawText: "",
    chapters: [],
    screenplay: null,
    status: "draft",
  });
}

/**
 * Mark state as dirty (call from components when user edits).
 */
function touch() {
  state.isDirty = true;
}

/**
 * Build API payload from current state.
 */
function _toPayload() {
  return {
    id: state.currentId || undefined,
    title: state.title,
    author: state.author,
    status: state.status,
    raw_text: state.rawText,
    chapters: state.chapters,
    screenplay: state.screenplay,
  };
}

export function useWorkspace() {
  return {
    state,
    list,
    create,
    load,
    save,
    deleteWorkspace,
    reset: _reset,
    touch,
  };
}
