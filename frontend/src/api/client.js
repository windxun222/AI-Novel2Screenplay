const BASE = "/api";

async function request(path, options = {}) {
  const url = BASE + path;
  const config = {
    headers: { "Content-Type": "application/json" },
    ...options,
  };
  const resp = await fetch(url, config);
  if (!resp.ok) {
    const error = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(error.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

export async function parseChapters(text, title, author) {
  return request("/chapters/parse", {
    method: "POST",
    body: JSON.stringify({ text, title, author }),
  });
}

export async function convertNovel(novel) {
  return request("/convert", {
    method: "POST",
    body: JSON.stringify(novel),
  });
}

export async function getSchema() {
  return request("/schema");
}

// ── Workspace API ──

export async function listWorkspaces() {
  return request("/workspaces");
}

export async function createWorkspace(ws) {
  return request("/workspaces", {
    method: "POST",
    body: JSON.stringify(ws),
  });
}

export async function loadWorkspace(id) {
  return request(`/workspaces/${id}`);
}

export async function saveWorkspace(id, ws) {
  return request(`/workspaces/${id}`, {
    method: "PUT",
    body: JSON.stringify(ws),
  });
}


// ── Step-by-step conversion ──

export async function preScan(novel) {
  return request("/convert/pre-scan", {
    method: "POST",
    body: JSON.stringify(novel),
  });
}

export async function convertChapter(chapterIndex, chapterText, existingChars, prevSummaries) {
  return request("/convert/chapter", {
    method: "POST",
    body: JSON.stringify({
      chapter_index: chapterIndex,
      chapter_text: chapterText,
      existing_characters: existingChars,
      previous_summaries: prevSummaries,
    }),
  });
}

export async function assembleStep(novel) {
  return request("/convert/assemble", {
    method: "POST",
    body: JSON.stringify(novel),
  });
}

export async function deleteWorkspace(id) {
  return request(`/workspaces/${id}`, {
    method: "DELETE",
  });
}
