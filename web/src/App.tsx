import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  api,
  clearCredentials,
  ClipboardItem,
  downloadArchive,
  downloadFile,
  FileItem,
  getToken,
  storeCredentials,
  subscribeEvents,
  Transfer,
} from "./api";

type Dialog =
  | null
  | { type: "upload" }
  | { type: "uploading"; names: string[]; pct: number }
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

function formatIsoRelative(iso: string): string {
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return iso;
  return formatTime(t / 1000);
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

function IconDownload() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M12 4v12M6 11l6 6 6-6" />
      <path d="M4 20h16" />
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
  const [tab, setTab] = useState<"files" | "clipboard" | "activity">("files");
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [clipItems, setClipItems] = useState<ClipboardItem[]>([]);
  const [clipDraft, setClipDraft] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  // null = not in selection mode; a Set = selection mode with these paths picked.
  const [selection, setSelection] = useState<Set<string> | null>(null);
  const [zipping, setZipping] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const pathStr = path.join("/");
  const pairToken = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get("pair");
  }, []);

  const refreshFiles = useCallback(async () => {
    if (query.trim()) {
      const res = await api.search(query.trim());
      setItems(res.items);
    } else {
      const res = await api.list(pathStr);
      setItems(res.items);
    }
  }, [pathStr, query]);

  const refreshClipboard = useCallback(async () => {
    const res = await api.clipboard();
    setClipItems(res.items);
  }, []);

  const refreshTransfers = useCallback(async () => {
    const res = await api.transfers();
    setTransfers(res.items);
  }, []);

  const refresh = useCallback(async () => {
    try {
      if (tab === "clipboard") await refreshClipboard();
      else if (tab === "activity") await refreshTransfers();
      else await refreshFiles();
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
  }, [tab, refreshClipboard, refreshFiles, refreshTransfers]);

  useEffect(() => {
    (async () => {
      try {
        if (pairToken) {
          setPairing(true);
          const suggested = guessDeviceName();
          const req = await api.requestPairing(pairToken, suggested);
          window.history.replaceState({}, "", "/");
          // Wait for host to name + approve in Control Center.
          const deadline = Date.now() + 5 * 60 * 1000;
          while (Date.now() < deadline) {
            const status = await api.pairingStatus(req.request_id, req.claim_secret);
            if (status.status === "approved" && status.device_token && status.device_id) {
              storeCredentials(
                status.device_id,
                status.device_token,
                status.display_name || suggested,
              );
              setAuthed(true);
              setPairing(false);
              return;
            }
            if (status.status === "declined") {
              setError("Pairing was declined on the computer.");
              setPairing(false);
              return;
            }
            await new Promise((r) => setTimeout(r, 1500));
          }
          setError("Pairing timed out. Start pairing again from ShareBox on your computer.");
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
    return subscribeEvents((kind) => {
      if (kind === "clipboard_changed") void refreshClipboard().catch(() => undefined);
      if (kind === "fs_changed" && tab === "files") void refreshFiles().catch(() => undefined);
      if (kind === "transfer" && tab === "activity") void refreshTransfers().catch(() => undefined);
    });
  }, [authed, tab, refreshClipboard, refreshFiles, refreshTransfers]);

  // A selection only makes sense for what is on screen right now.
  useEffect(() => {
    setSelection(null);
  }, [pathStr, tab, query]);

  function toggleSelected(path: string) {
    setSelection((current) => {
      const next = new Set(current ?? []);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  }

  async function downloadPaths(paths: string[]) {
    if (paths.length === 0) return;
    setZipping(true);
    try {
      await downloadArchive(paths);
      setSelection(null);
    } catch (e) {
      setError((e as Error).message || "Could not prepare the download");
    } finally {
      setZipping(false);
    }
  }

  async function onPickFiles(fileList: FileList | null) {
    if (!fileList || fileList.length === 0) return;
    // Snapshot immediately — FileList is live and becomes empty if the input is cleared.
    const selected = Array.from(fileList);
    if (selected.length === 0) return;
    const names = selected.map((f) => f.name);
    setDialog({ type: "uploading", names, pct: 0 });
    try {
      const result = await api.upload(selected, (pct) => {
        // One request carries every file, so the browser only reports overall
        // progress. Showing that figure per-file would be a guess.
        setDialog({ type: "uploading", names, pct });
      });
      const uploaded = result.files?.length ?? selected.length;
      setDialog({ type: "uploadDone", count: uploaded });
      // Refresh listing after a tick so the success modal keeps its count.
      void refresh();
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
          <p className="muted">{pairing ? "Waiting for approval on your computer…" : "Connecting…"}</p>
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
          {tab === "files" && !selection && items.length > 0 && (
            <button className="btn btn-ghost" type="button" onClick={() => setSelection(new Set())}>
              Select
            </button>
          )}
          {tab === "files" && (
            <button className="btn btn-primary" type="button" onClick={() => setDialog({ type: "upload" })}>
              Upload
            </button>
          )}
        </div>
        <div className="seg" style={{ marginTop: 12, width: "fit-content" }}>
          <label className="seg-opt">
            <input
              type="radio"
              name="tab"
              checked={tab === "files"}
              onChange={() => setTab("files")}
            />
            Files
          </label>
          <label className="seg-opt">
            <input
              type="radio"
              name="tab"
              checked={tab === "clipboard"}
              onChange={() => setTab("clipboard")}
            />
            Clipboard
          </label>
          <label className="seg-opt">
            <input
              type="radio"
              name="tab"
              checked={tab === "activity"}
              onChange={() => setTab("activity")}
            />
            Activity
          </label>
        </div>
        {tab === "files" && (
          <>
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
          </>
        )}
        {tab === "files" && selection && (
          <div className="header-row" style={{ marginTop: 12 }}>
            <span className="muted" style={{ marginRight: "auto", fontSize: 13 }}>
              {selection.size === 0 ? "Tap items to select" : `${selection.size} selected`}
            </span>
            <button className="btn btn-ghost" type="button" onClick={() => setSelection(null)}>
              Cancel
            </button>
            <button
              className="btn btn-primary"
              type="button"
              disabled={selection.size === 0 || zipping}
              onClick={() => void downloadPaths([...selection])}
            >
              {zipping ? "Preparing…" : "Download as zip"}
            </button>
          </div>
        )}
        {offline && <p className="muted" style={{ marginTop: 8 }}>Host unavailable — retrying when you navigate.</p>}
        {error && !offline && <p className="muted" style={{ marginTop: 8 }}>{error}</p>}
      </header>

      <main className="app-body">
        {tab === "activity" ? (
          transfers.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">
                <IconFile />
              </div>
              <div style={{ fontFamily: "var(--font-heading)", fontSize: 15 }}>No activity yet</div>
              <div className="muted" style={{ marginTop: 4 }}>
                Files you upload or download will be listed here
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {transfers.map((t) => (
                <div className="card elev-sm file-row" key={t.transfer_id}>
                  <div
                    className="file-icon"
                    title={t.direction === "upload" ? "Sent to host" : "Received from host"}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                      {t.direction === "upload" ? (
                        <path d="M12 20V8M6 13l6-6 6 6" />
                      ) : (
                        <path d="M12 4v12M6 11l6 6 6-6" />
                      )}
                    </svg>
                  </div>
                  <div style={{ marginLeft: 12, flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 14, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                      {t.name}
                    </div>
                    <div className="card-meta">
                      {t.direction === "upload" ? "Uploaded" : "Downloaded"}
                      {t.size != null && ` · ${formatSize(t.size)}`}
                      {` · ${formatIsoRelative(t.created_at)}`}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )
        ) : tab === "clipboard" ? (
          <>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 24 }}>
              <textarea
                className="input"
                rows={3}
                placeholder="Paste or type text to share with your other devices"
                value={clipDraft}
                onChange={(e) => setClipDraft(e.target.value)}
              />
              <button
                className="btn btn-secondary"
                style={{ alignSelf: "flex-end" }}
                type="button"
                disabled={!clipDraft.trim()}
                onClick={() => {
                  void (async () => {
                    const text = clipDraft.trim();
                    if (!text) return;
                    await api.shareClipboard(text);
                    setClipDraft("");
                    await refreshClipboard();
                  })();
                }}
              >
                Share to devices
              </button>
            </div>
            {clipItems.length === 0 ? (
              <div style={{ textAlign: "center", padding: "40px 20px" }}>
                <div className="muted" style={{ fontSize: 13 }}>
                  Nothing shared yet. Paste text above to send it to your other devices.
                </div>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {clipItems.map((c) => (
                  <div className="card elev-sm" key={c.item_id}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span className="tag tag-accent">{c.source_label}</span>
                      <span className="card-meta">{formatIsoRelative(c.created_at)}</span>
                      <button
                        className="btn btn-ghost"
                        style={{ marginLeft: "auto", flex: "none" }}
                        type="button"
                        onClick={() => {
                          void navigator.clipboard.writeText(c.text).then(() => {
                            setCopiedId(c.item_id);
                            setTimeout(() => setCopiedId(null), 1200);
                          });
                        }}
                      >
                        {copiedId === c.item_id ? "Copied" : "Copy"}
                      </button>
                    </div>
                    <p style={{ margin: "6px 0 0", fontSize: 14, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                      {c.text}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <>
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
                      if (selection) {
                        toggleSelected(it.path);
                      } else if (it.type === "folder") {
                        if (isSearching) setQuery("");
                        setPath(it.path.split("/").filter(Boolean));
                      } else {
                        setDialog({ type: "preview", item: it });
                      }
                    }}
                  >
                    {selection && (
                      <input
                        type="checkbox"
                        checked={selection.has(it.path)}
                        onChange={() => toggleSelected(it.path)}
                        onClick={(e) => e.stopPropagation()}
                        style={{ marginRight: 10, flex: "none" }}
                        aria-label={`Select ${it.name}`}
                      />
                    )}
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
                    {!selection && (
                      <button
                        className="btn btn-icon btn-ghost"
                        type="button"
                        title={it.type === "folder" ? "Download folder as zip" : "Download"}
                        disabled={zipping}
                        onClick={(e) => {
                          e.stopPropagation();
                          if (it.type === "folder") void downloadPaths([it.path]);
                          else void downloadFile(it.path, it.name);
                        }}
                      >
                        <IconDownload />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
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
                <div className="dialog-title">
                  Uploading {dialog.names.length} file{dialog.names.length === 1 ? "" : "s"}
                </div>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 6 }}>
                    <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {dialog.names.length === 1 ? dialog.names[0] : `${dialog.names.length} items`}
                    </span>
                    <span className="muted">{dialog.pct}%</span>
                  </div>
                  <div className="progress-track">
                    <div className="progress-fill" style={{ width: `${dialog.pct}%` }} />
                  </div>
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
