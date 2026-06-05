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
