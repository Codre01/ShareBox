import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  api,
  clearCredentials,
  downloadFile,
  FileItem,
  getToken,
  storeCredentials,
  subscribeEvents,
} from "./api";

type Dialog =
  | null
  | { type: "upload" }
  | { type: "uploading"; files: { name: string; pct: number }[] }
  | { type: "uploadDone"; count: number }
  | { type: "uploadFail"; message: string }
  | { type: "preview"; item: FileItem };

function formatSize(size: number | null): string {
  if (size == null) return "";
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  return `${(size / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

function formatTime(ts: number): string {
  const diff = Date.now() / 1000 - ts;
  if (diff < 60) return "Just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return new Date(ts * 1000).toLocaleDateString();
}

function IconFolder() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M3 6.5A1.5 1.5 0 0 1 4.5 5H9l2 2h8.5A1.5 1.5 0 0 1 21 8.5v9A1.5 1.5 0 0 1 19.5 19h-15A1.5 1.5 0 0 1 3 17.5z" />
    </svg>
  );
}

function IconFile() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M6 3h9l4 4v14H6z" />
    </svg>
  );
}

function guessDeviceName(): string {
  const ua = navigator.userAgent;
  if (/iPhone/i.test(ua)) return "iPhone";
  if (/iPad/i.test(ua)) return "iPad";
  if (/Android/i.test(ua)) return "Android";
  return "Browser";
}

export default function App() {
  const [booting, setBooting] = useState(true);
  const [authed, setAuthed] = useState(false);
  const [hostName, setHostName] = useState("ShareBox");
  const [path, setPath] = useState<string[]>([]);
  const [items, setItems] = useState<FileItem[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pairing, setPairing] = useState(false);
  const [dialog, setDialog] = useState<Dialog>(null);
  const [offline, setOffline] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const pathStr = path.join("/");
  const pairToken = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get("pair");
  }, []);

  const refresh = useCallback(async () => {
    try {
      if (query.trim()) {
        const res = await api.search(query.trim());
        setItems(res.items);
      } else {
        const res = await api.list(pathStr);
        setItems(res.items);
      }
      setError(null);
      setOffline(false);
    } catch (e) {
      const err = e as Error & { code?: string; status?: number };
      if (err.status === 401 || err.code === "UNAUTHORIZED") {
        clearCredentials();
        setAuthed(false);
        setError("Access revoked. Pair this device again from ShareBox on your computer.");
      } else {
        setOffline(true);
        setError(err.message || "Could not reach ShareBox host");
      }
    }
  }, [pathStr, query]);

  useEffect(() => {
    (async () => {
      try {
        if (pairToken) {
          setPairing(true);
          const name = guessDeviceName();
          const res = await api.completePairing(pairToken, name);
          storeCredentials(res.device_id, res.device_token, res.display_name);
          window.history.replaceState({}, "", "/");
          setAuthed(true);
          setPairing(false);
        } else if (getToken()) {
          const status = await api.status();
          setHostName(status.host_name || "ShareBox");
          if (status.authenticated) {
            setAuthed(true);
          } else {
            clearCredentials();
            setAuthed(false);
          }
        }
      } catch (e) {
        const err = e as Error & { code?: string };
        if (pairToken) {
          setError(err.message || "Pairing failed");
          setPairing(false);
        }
      } finally {
        setBooting(false);
      }
    })();
  }, [pairToken]);

  useEffect(() => {
    if (!authed) return;
    void refresh();
  }, [authed, refresh]);

  useEffect(() => {
    if (!authed) return;
    return subscribeEvents(() => {
      void refresh();
    });
  }, [authed, refresh]);

  async function onPickFiles(fileList: FileList | null) {
    if (!fileList || fileList.length === 0) return;
    const files = Array.from(fileList).map((f) => ({ name: f.name, pct: 0 }));
    setDialog({ type: "uploading", files });
    try {
      await api.upload(fileList, (pct) => {
        setDialog({
          type: "uploading",
          files: Array.from(fileList).map((f) => ({ name: f.name, pct })),
        });
      });
      setDialog({ type: "uploadDone", count: fileList.length });
      await refresh();
    } catch (e) {
      setDialog({ type: "uploadFail", message: (e as Error).message });
    }
  }

  if (booting || pairing) {
    return (
      <div className="app-shell">
        <div className="center-card">
          <div className="brand" style={{ marginBottom: 12 }}>
            ShareBox
          </div>
          <p className="muted">{pairing ? "Pairing this device…" : "Connecting…"}</p>
        </div>
      </div>
    );
  }

  if (!authed) {
    return (
      <div className="app-shell">
        <div className="center-card card elev-sm">
          <h2 style={{ marginTop: 0 }}>ShareBox</h2>
          <p className="muted">
            This device is not paired. Open ShareBox on your computer and scan the QR code, or open
            the pairing link from that screen.
          </p>
          {error && <p style={{ color: "var(--color-accent-300)" }}>{error}</p>}
        </div>
      </div>
    );
  }

  const isSearching = query.trim().length > 0;
  const empty = items.length === 0;

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="header-row">
          <div className="brand" style={{ marginRight: "auto" }}>
            ShareBox
          </div>
          <button className="btn btn-primary" type="button" onClick={() => setDialog({ type: "upload" })}>
            Upload
          </button>
        </div>
        <div className="search-wrap">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--color-neutral-500)" strokeWidth="1.8">
            <circle cx="11" cy="11" r="7" />
            <path d="M21 21l-4-4" />
          </svg>
          <input
            className="input"
            placeholder="Search files"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        {!isSearching && path.length > 0 && (
          <nav className="breadcrumb" aria-label="Breadcrumb">
            <button type="button" className="crumb" onClick={() => setPath([])}>
              ShareBox
            </button>
            {path.map((seg, i) => (
              <span key={`${seg}-${i}`} style={{ display: "contents" }}>
                <span style={{ color: "var(--color-neutral-600)" }}>/</span>
                <button
                  type="button"
                  className={`crumb ${i === path.length - 1 ? "current" : ""}`}
                  onClick={() => setPath(path.slice(0, i + 1))}
                >
                  {seg}
                </button>
              </span>
            ))}
          </nav>
        )}
        {offline && <p className="muted" style={{ marginTop: 8 }}>Host unavailable — retrying when you navigate.</p>}
        {error && !offline && <p className="muted" style={{ marginTop: 8 }}>{error}</p>}
      </header>

      <main className="app-body">
        {isSearching && <div className="muted" style={{ marginBottom: 12 }}>{items.length} result(s)</div>}
        {empty ? (
          <div className="empty-state">
            <div className="empty-icon">
              <IconFolder />
            </div>
            <div style={{ fontFamily: "var(--font-heading)", fontSize: 15 }}>
              {isSearching ? "No matches" : "This folder is empty"}
            </div>
            <div className="muted" style={{ marginTop: 4 }}>
              {isSearching ? "Try another search" : `Files on ${hostName} will show up here`}
            </div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {items.map((it) => (
              <div
                key={it.path}
                className="card elev-sm file-row"
                onClick={() => {
                  if (it.type === "folder") {
                    if (isSearching) setQuery("");
                    setPath(it.path.split("/").filter(Boolean));
                  } else {
                    setDialog({ type: "preview", item: it });
                  }
                }}
              >
                <div className="file-icon">{it.type === "folder" ? <IconFolder /> : <IconFile />}</div>
                <div style={{ marginLeft: 12, flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 14, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {it.name}
                  </div>
                  <div className="card-meta">
                    {it.type === "folder"
                      ? formatTime(it.modified)
                      : `${formatSize(it.size)} · ${formatTime(it.modified)}`}
                    {isSearching && <span> · {it.path}</span>}
                  </div>
                </div>
                {it.type === "file" && (
                  <button
                    className="btn btn-icon btn-ghost"
                    type="button"
                    title="Download"
                    onClick={(e) => {
                      e.stopPropagation();
                      void downloadFile(it.path, it.name);
                    }}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                      <path d="M12 4v12M6 11l6 6 6-6" />
                      <path d="M4 20h16" />
                    </svg>
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </main>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        hidden
        onChange={(e) => {
          void onPickFiles(e.target.files);
          e.target.value = "";
        }}
      />

      {dialog && (
        <div className="dialog-backdrop" onClick={() => setDialog(null)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            {dialog.type === "upload" && (
              <>
                <div className="dialog-title">Upload files</div>
                <div
                  className="drop-zone"
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    void onPickFiles(e.dataTransfer.files);
                  }}
                >
                  <div className="muted">Drag files here, or</div>
                  <button className="btn btn-secondary" style={{ marginTop: 10 }} type="button" onClick={() => fileInputRef.current?.click()}>
                    Choose files
                  </button>
                </div>
                <div className="dialog-actions">
                  <button className="btn btn-secondary" type="button" onClick={() => setDialog(null)}>
                    Cancel
                  </button>
                </div>
              </>
            )}
            {dialog.type === "uploading" && (
              <>
                <div className="dialog-title">Uploading</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  {dialog.files.map((u) => (
                    <div key={u.name}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 6 }}>
                        <span>{u.name}</span>
                        <span className="muted">{u.pct}%</span>
                      </div>
                      <div className="progress-track">
                        <div className="progress-fill" style={{ width: `${u.pct}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
            {dialog.type === "uploadDone" && (
              <>
                <div className="dialog-title" style={{ textAlign: "center" }}>
                  Upload complete
                </div>
                <div className="dialog-body" style={{ textAlign: "center" }}>
                  {dialog.count} file(s) added to this device&apos;s folder.
                </div>
                <div className="dialog-actions" style={{ justifyContent: "center" }}>
                  <button className="btn btn-primary" type="button" onClick={() => setDialog(null)}>
                    Done
                  </button>
                </div>
              </>
            )}
            {dialog.type === "uploadFail" && (
              <>
                <div className="dialog-title">Upload failed</div>
                <div className="dialog-body">{dialog.message}</div>
                <div className="dialog-actions">
                  <button className="btn btn-primary" type="button" onClick={() => setDialog(null)}>
                    Close
                  </button>
                </div>
              </>
            )}
            {dialog.type === "preview" && (
              <>
                <div className="dialog-title" style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {dialog.item.name}
                </div>
                <PreviewBody item={dialog.item} />
                <div className="card-meta">
                  {formatSize(dialog.item.size)} · {formatTime(dialog.item.modified)}
                </div>
                <div className="dialog-actions">
                  <button className="btn btn-secondary" type="button" onClick={() => setDialog(null)}>
                    Close
                  </button>
                  <button
                    className="btn btn-primary"
                    type="button"
                    onClick={() => void downloadFile(dialog.item.path, dialog.item.name)}
                  >
                    Download
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function PreviewBody({ item }: { item: FileItem }) {
  const [url, setUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const lower = item.name.toLowerCase();
  const isImage = /\.(png|jpe?g|gif|webp|bmp|svg)$/i.test(lower);

  useEffect(() => {
    if (!isImage) return;
    let objectUrl: string | null = null;
    const token = getToken();
    (async () => {
      try {
        const res = await fetch(api.previewUrl(item.path), {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (!res.ok) throw new Error("preview failed");
        const blob = await res.blob();
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      } catch {
        setFailed(true);
      }
    })();
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [item.path, isImage]);

  return (
    <div className="preview-frame">
      {isImage && url && !failed ? (
        <img src={url} alt={item.name} />
      ) : (
        <span className="muted" style={{ fontFamily: "ui-monospace, monospace", fontSize: 12 }}>
          preview unavailable
        </span>
      )}
    </div>
  );
}
