const TOKEN_KEY = "sharebox.deviceToken";
const DEVICE_KEY = "sharebox.deviceId";
const NAME_KEY = "sharebox.deviceName";

export type FileItem = {
  name: string;
  type: "file" | "folder";
  size: number | null;
  modified: number;
  path: string;
};

export type DeviceInfo = {
  device_id: string;
  display_name: string;
  folder_slug: string;
};

export type ClipboardItem = {
  item_id: string;
  text: string;
  source_label: string;
  device_id: string | null;
  created_at: string;
};

export type Transfer = {
  transfer_id: string;
  direction: "upload" | "download";
  device_id: string | null;
  device_label: string;
  path: string;
  name: string;
  size: number | null;
  created_at: string;
};

type ApiError = { code: string; message: string };

async function request<T>(
  path: string,
  init: RequestInit = {},
  auth = true,
): Promise<T> {
  const headers = new Headers(init.headers);
  if (auth) {
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  const res = await fetch(path, { ...init, headers });
  if (!res.ok) {
    let err: ApiError = { code: "HTTP_ERROR", message: res.statusText };
    try {
      const body = await res.json();
      err = body.detail ?? body.error ?? err;
    } catch {
      /* ignore */
    }
    const e = new Error(err.message) as Error & { code: string; status: number };
    e.code = err.code;
    e.status = res.status;
    throw e;
  }
  if (res.status === 204) return undefined as T;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res as unknown as T;
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredDevice(): DeviceInfo | null {
  const id = localStorage.getItem(DEVICE_KEY);
  const name = localStorage.getItem(NAME_KEY);
  if (!id || !name) return null;
  return { device_id: id, display_name: name, folder_slug: "" };
}

export function storeCredentials(deviceId: string, token: string, name: string) {
  localStorage.setItem(DEVICE_KEY, deviceId);
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(NAME_KEY, name);
}

export function clearCredentials() {
  localStorage.removeItem(DEVICE_KEY);
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(NAME_KEY);
}

export const api = {
  health: () => request<{ ok: boolean }>("/api/v1/health", {}, false),
  status: () =>
    request<{
      authenticated: boolean;
      sharing: boolean;
      host_name: string;
      device: DeviceInfo | null;
      url_hints: string[];
    }>("/api/v1/status"),
  list: (path = "") =>
    request<{ path: string; items: FileItem[] }>(
      `/api/v1/files?path=${encodeURIComponent(path)}`,
    ),
  search: (q: string) =>
    request<{ query: string; items: FileItem[] }>(
      `/api/v1/files/search?q=${encodeURIComponent(q)}`,
    ),
  downloadUrl: (path: string) =>
    `/api/v1/files/download?path=${encodeURIComponent(path)}`,
  previewUrl: (path: string) =>
    `/api/v1/files/preview?path=${encodeURIComponent(path)}`,
  requestPairing: (token: string, suggestedName: string) =>
    request<{
      request_id: string;
      status: string;
      claim_secret: string;
      suggested_name?: string;
    }>(
      "/api/v1/pairing/request",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, suggested_name: suggestedName }),
      },
      false,
    ),
  pairingStatus: (requestId: string, claimSecret: string) =>
    request<{
      status: string;
      request_id: string;
      device_id?: string;
      display_name?: string;
      folder_slug?: string;
      device_token?: string;
    }>(
      `/api/v1/pairing/request/${requestId}?claim_secret=${encodeURIComponent(claimSecret)}`,
      {},
      false,
    ),
  upload: async (files: FileList | File[], onProgress?: (pct: number) => void) => {
    const form = new FormData();
    Array.from(files).forEach((f) => form.append("files", f));
    const token = getToken();
    return new Promise<{ folder: string; files: { name: string; path: string; size: number }[] }>(
      (resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open("POST", "/api/v1/files/upload");
        if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
        xhr.upload.onprogress = (ev) => {
          if (ev.lengthComputable && onProgress) {
            onProgress(Math.round((ev.loaded / ev.total) * 100));
          }
        };
        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            try {
              const body = JSON.parse(xhr.responseText);
              reject(new Error(body.detail?.message || body.error?.message || "Upload failed"));
            } catch {
              reject(new Error("Upload failed"));
            }
          }
        };
        xhr.onerror = () => reject(new Error("Network error"));
        xhr.send(form);
      },
    );
  },
  transfers: (limit = 100) =>
    request<{ items: Transfer[]; scope: string }>(`/api/v1/transfers?limit=${limit}`),
  archiveTicket: (paths: string[]) =>
    request<{
      ticket: string;
      filename: string;
      file_count: number;
      expires_in: number;
    }>("/api/v1/files/archive/ticket", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ paths }),
    }),
  clipboard: () => request<{ items: ClipboardItem[] }>("/api/v1/clipboard"),
  shareClipboard: (text: string) =>
    request<{ item: ClipboardItem }>("/api/v1/clipboard", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    }),
  deleteClipboard: (itemId: string) =>
    request<{ status: string }>(`/api/v1/clipboard/${itemId}`, { method: "DELETE" }),
};

export async function downloadFile(path: string, filename: string) {
  const token = getToken();
  const res = await fetch(`/api/v1/files/download?path=${encodeURIComponent(path)}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error("Download failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export async function downloadArchive(paths: string[]): Promise<number> {
  const { ticket, file_count } = await api.archiveTicket(paths);
  // Hand the browser a plain link rather than fetching into a blob: the zip is
  // streamed straight to disk instead of being held in the phone's memory.
  const link = document.createElement("a");
  link.href = `/api/v1/files/archive?ticket=${encodeURIComponent(ticket)}`;
  link.rel = "noopener";
  document.body.appendChild(link);
  link.click();
  link.remove();
  return file_count;
}

export function subscribeEvents(onEvent: (kind: string) => void): () => void {
  const token = getToken();
  if (!token) return () => undefined;
  const ctrl = new AbortController();
  (async () => {
    try {
      const res = await fetch("/api/v1/events", {
        headers: { Authorization: `Bearer ${token}` },
        signal: ctrl.signal,
      });
      if (!res.ok || !res.body) return;
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";
        for (const part of parts) {
          if (part.includes("fs_changed")) onEvent("fs_changed");
          if (part.includes("clipboard_changed")) onEvent("clipboard_changed");
          if (part.includes("event: transfer")) onEvent("transfer");
        }
      }
    } catch {
      /* aborted or network */
    }
  })();
  return () => ctrl.abort();
}
