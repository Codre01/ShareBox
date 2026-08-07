(() => {
  const state = {
    page: "status",
    status: null,
    devices: [],
    settings: null,
    clipboard: [],
    clipDraft: "",
    pairing: null,
    pairingTimer: null,
  };

  const apiBase = () => {
    if (typeof window.__SHAREBOX_API__ === "string") return window.__SHAREBOX_API__;
    // Same-origin when served from http://127.0.0.1:port/host/
    return "";
  };

  async function api(path, init = {}) {
    const method = (init.method || "GET").toUpperCase();
    const headers = { ...(init.headers || {}) };
    // Only set JSON content-type when sending a body — avoids needless CORS preflights.
    if (init.body != null && !headers["Content-Type"] && !headers["content-type"]) {
      headers["Content-Type"] = "application/json";
    }
    const res = await fetch(apiBase() + path, {
      ...init,
      method,
      headers,
    });
    if (!res.ok) {
      let msg = res.statusText;
      try {
        const body = await res.json();
        msg = body.detail?.message || body.error?.message || msg;
      } catch {}
      throw new Error(msg);
    }
    if (res.status === 204) return null;
    return res.json();
  }

  function $(id) {
    return document.getElementById(id);
  }

  function setNav() {
    document.querySelectorAll(".nav-item").forEach((el) => {
      el.classList.toggle("active", el.dataset.nav === state.page);
    });
  }

  function formatWhen(iso) {
    if (!iso) return "—";
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return iso;
    }
  }

  function formatRelative(iso) {
    if (!iso) return "";
    const t = Date.parse(iso);
    if (Number.isNaN(t)) return iso;
    const diff = (Date.now() - t) / 1000;
    if (diff < 60) return "Just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return new Date(t).toLocaleDateString();
  }

  function renderStatus() {
    const s = state.status || {};
    const sharing = !!s.sharing;
    const primary = (s.primary_url || (s.url_hints && s.url_hints[0]) || `http://127.0.0.1:${s.port || 8765}`).replace(
      /^https?:\/\//,
      "",
    );
    const ipHint = (s.lan_addresses && s.lan_addresses[0] ? `${s.lan_addresses[0]}:${s.port || 8765}` : "");
    const folder = (state.settings && state.settings.shared_folder) || "";
    const mdnsNote = s.mdns_active
      ? `sharebox.local points to ${s.mdns_ip || ipHint}`
      : ipHint
        ? `If sharebox.local fails, use ${ipHint}`
        : "Waiting for network…";
    return `
      <div style="max-width:560px;">
        <h6 style="color:var(--color-neutral-500);margin-bottom:var(--space-2);">Overview</h6>
        <h2 style="margin-bottom:var(--space-6);">Status</h2>
        <div class="card elev-sm" style="margin-bottom:var(--space-6);">
          <div style="display:flex;align-items:center;gap:10px;">
            <div class="status-dot ${sharing ? "on" : ""}" style="width:12px;height:12px;"></div>
            <div>
              <div style="font-family:var(--font-heading);font-weight:500;font-size:17px;">${sharing ? "Sharing" : "Stopped"}</div>
              <div class="card-meta" style="margin-top:2px;">${sharing ? "Devices on your network can connect" : "Start sharing to accept connections"}</div>
            </div>
            <button class="btn btn-secondary" style="margin-left:auto;flex:none;" id="btn-toggle">${sharing ? "Stop" : "Start"}</button>
          </div>
        </div>
        ${
          sharing
            ? `<div class="card elev-sm" style="margin-bottom:var(--space-6);gap:var(--space-3);">
            <div class="card-kicker">Connect from another device</div>
            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
              <span class="mono">${escapeHtml(primary)}</span>
              <button class="btn btn-ghost" style="margin-left:auto;flex:none;" id="btn-copy">Copy address</button>
            </div>
            <div class="card-meta">${escapeHtml(mdnsNote)}</div>
          </div>`
            : ""
        }
        <div class="card elev-sm" style="margin-bottom:var(--space-6);">
          <div class="card-kicker">Shared folder</div>
          <div style="display:flex;align-items:center;gap:10px;">
            <span class="mono" style="overflow:hidden;text-overflow:ellipsis;">${escapeHtml(folder)}</span>
            <button class="btn btn-ghost" style="margin-left:auto;flex:none;" id="btn-open-folder">Open folder</button>
          </div>
        </div>
        <button class="btn btn-primary btn-block" id="btn-pair" ${sharing ? "" : "disabled"}>Pair new device</button>
      </div>`;
  }

  function renderDevices() {
    const rows = state.devices
      .map((d) => {
        const initial = (d.display_name || "?").trim().charAt(0).toUpperCase();
        return `<div class="card elev-sm" style="margin-bottom:var(--space-3);flex-direction:row;align-items:center;">
          <div style="width:36px;height:36px;border-radius:50%;background:var(--color-accent-800);color:var(--color-accent-100);display:flex;align-items:center;justify-content:center;font-family:var(--font-heading);font-size:14px;flex:none;">${initial}</div>
          <div style="margin-left:var(--space-3);flex:1;min-width:0;">
            <div style="font-family:var(--font-heading);font-weight:500;font-size:14px;">${escapeHtml(d.display_name)}</div>
            <div class="card-meta">Paired ${formatWhen(d.created_at)} · Last seen ${formatWhen(d.last_seen_at)}</div>
          </div>
          <button class="btn btn-ghost" data-rename="${d.device_id}" data-name="${escapeAttr(d.display_name)}" style="flex:none;">Rename</button>
          <button class="btn btn-secondary" data-revoke="${d.device_id}" style="flex:none;margin-left:6px;">Revoke</button>
        </div>`;
      })
      .join("");
    return `
      <div style="max-width:640px;">
        <h6 style="color:var(--color-neutral-500);margin-bottom:var(--space-2);">Access</h6>
        <div style="display:flex;align-items:baseline;justify-content:space-between;margin-bottom:var(--space-6);">
          <h2 style="margin:0;">Trusted devices</h2>
          <button class="btn btn-secondary" id="btn-pair">+ Pair new device</button>
        </div>
        ${rows || `<div class="text-muted" style="font-size:13px;padding:var(--space-4) 0;">No trusted devices yet. Pair one to get started.</div>`}
      </div>`;
  }

  function renderClipboard() {
    const rows = state.clipboard
      .map(
        (c) => `<div class="card elev-sm">
          <div style="display:flex;align-items:center;gap:8px;">
            <span class="tag tag-accent">${escapeHtml(c.source_label)}</span>
            <span class="card-meta">${formatRelative(c.created_at)}</span>
            <button class="btn btn-ghost" style="margin-left:auto;flex:none;" data-copy-id="${c.item_id}">Copy</button>
            <button class="btn btn-ghost" style="flex:none;" data-delete-id="${c.item_id}">Delete</button>
          </div>
          <p style="margin:6px 0 0;font-size:14px;white-space:pre-wrap;word-break:break-word;">${escapeHtml(c.text)}</p>
        </div>`,
      )
      .join("");
    return `
      <div style="max-width:560px;">
        <h6 style="color:var(--color-neutral-500);margin-bottom:var(--space-2);">Cross-device</h6>
        <h2 style="margin-bottom:var(--space-6);">Clipboard</h2>
        <div style="display:flex;flex-direction:column;gap:8px;margin-bottom:var(--space-6);">
          <textarea class="input" id="clip-draft" rows="3" placeholder="Type or paste text to send to your other devices">${escapeHtml(state.clipDraft)}</textarea>
          <button class="btn btn-secondary" style="align-self:flex-end;" id="btn-share-clip" ${state.clipDraft.trim() ? "" : "disabled"}>Share to devices</button>
        </div>
        ${
          rows
            ? `<div style="display:flex;flex-direction:column;gap:8px;">${rows}</div>`
            : `<div class="text-muted" style="font-size:13px;padding:var(--space-4) 0;">Nothing shared yet.</div>`
        }
      </div>`;
  }

  function renderSettings() {
    const s = state.settings || {};
    return `
      <div style="max-width:480px;">
        <h6 style="color:var(--color-neutral-500);margin-bottom:var(--space-2);">Preferences</h6>
        <h2 style="margin-bottom:var(--space-6);">Settings</h2>
        <div class="field" style="margin-bottom:var(--space-6);">
          <label>Shared folder</label>
          <div style="display:flex;gap:8px;">
            <input class="input mono" id="shared-folder" value="${escapeAttr(s.shared_folder || "")}" readonly />
            <button class="btn btn-secondary" style="flex:none;" id="btn-change-folder">Change…</button>
          </div>
        </div>
        <div class="field" style="margin-bottom:var(--space-6);">
          <label>This computer's name</label>
          <input class="input" id="host-name" value="${escapeAttr(s.host_name || "")}" />
        </div>
        <div class="field" style="margin-bottom:var(--space-6);">
          <label>Launch ShareBox when my computer starts</label>
          <div class="seg" style="width:fit-content;">
            <label class="seg-opt"><input type="radio" name="startup" value="1" ${s.launch_at_startup ? "checked" : ""}/>On</label>
            <label class="seg-opt"><input type="radio" name="startup" value="0" ${!s.launch_at_startup ? "checked" : ""}/>Off</label>
          </div>
        </div>
        <div class="field" style="margin-bottom:var(--space-6);">
          <label>Port</label>
          <input class="input mono" id="port" type="number" min="1024" max="65535" value="${s.port || 8765}" />
        </div>
        <button class="btn btn-primary" id="btn-save-settings">Save</button>
      </div>`;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
  function escapeAttr(s) {
    return escapeHtml(s).replace(/'/g, "&#39;");
  }

  function render() {
    setNav();
    const main = $("main");
    if (state.page === "status") main.innerHTML = renderStatus();
    else if (state.page === "devices") main.innerHTML = renderDevices();
    else if (state.page === "clipboard") main.innerHTML = renderClipboard();
    else main.innerHTML = renderSettings();
    bind();
    updateChrome();
  }

  function updateChrome() {
    const sharing = !!(state.status && state.status.sharing);
    const dot = $("nav-dot");
    const label = $("nav-running-label");
    dot.className = "status-dot " + (sharing ? "on" : "");
    label.textContent = sharing ? "Sharing" : "Stopped";
    $("device-count").textContent = String(state.devices.length);
  }

  function showPairDialog(session) {
    const dlg = $("dialog");
    const qrUrl = apiBase() + "/api/v1/qr.png?" + Date.now();
    dlg.style.display = "flex";
    dlg.innerHTML = `
      <div class="dialog">
        <div class="dialog-title">Pair a new device</div>
        <div class="dialog-body">Open a browser on the new device and scan this code.</div>
        <img src="${qrUrl}" alt="Pairing QR" width="180" height="180" style="align-self:center;border-radius:var(--radius-md);background:#fff;padding:8px;" />
        <div class="text-muted" style="text-align:center;font-size:12px;" id="pair-ttl">Expires soon</div>
        <div class="mono" style="text-align:center;font-size:11px;word-break:break-all;">${escapeHtml(session.pair_url)}</div>
        <div class="dialog-actions">
          <button class="btn btn-secondary" id="btn-cancel-pair">Cancel</button>
        </div>
      </div>`;
    $("btn-cancel-pair").onclick = async () => {
      try {
        await api("/api/v1/pairing/cancel", { method: "POST" });
      } catch {}
      hideDialog();
      if (state.pairingTimer) clearInterval(state.pairingTimer);
    };
    const expires = Date.parse(session.expires_at);
    state.pairingTimer = setInterval(() => {
      const left = Math.max(0, Math.floor((expires - Date.now()) / 1000));
      const el = $("pair-ttl");
      if (!el) return;
      if (left <= 0) {
        el.textContent = "Expired";
        clearInterval(state.pairingTimer);
      } else {
        const m = Math.floor(left / 60);
        const s = String(left % 60).padStart(2, "0");
        el.textContent = `Code expires in ${m}:${s}`;
      }
    }, 500);
  }

  function hideDialog() {
    const dlg = $("dialog");
    dlg.style.display = "none";
    dlg.innerHTML = "";
  }

  function showApproveDialog(req) {
    const dlg = $("dialog");
    const suggested = req.suggested_name || "Trusted device";
    dlg.style.display = "flex";
    dlg.innerHTML = `
      <div class="dialog">
        <div class="dialog-title">New device wants to pair</div>
        <div class="dialog-body">Name this device. Its upload folder will use the same name.</div>
        <div class="field">
          <label>Device name</label>
          <input class="input" id="pair-name" value="${escapeAttr(suggested)}" />
        </div>
        <div class="dialog-actions">
          <button class="btn btn-secondary" id="btn-decline-pair">Decline</button>
          <button class="btn btn-primary" id="btn-approve-pair">Approve</button>
        </div>
      </div>`;
    $("btn-decline-pair").onclick = async () => {
      await api("/api/v1/pairing/decline", {
        method: "POST",
        body: JSON.stringify({ request_id: req.request_id }),
      });
      hideDialog();
      await refresh();
    };
    $("btn-approve-pair").onclick = async () => {
      const name = ($("pair-name")?.value || "").trim() || suggested;
      await api("/api/v1/pairing/approve", {
        method: "POST",
        body: JSON.stringify({ request_id: req.request_id, display_name: name }),
      });
      hideDialog();
      await refresh();
    };
  }

  function bind() {
    const toggle = $("btn-toggle");
    if (toggle) {
      toggle.onclick = async () => {
        if (state.status?.sharing) await api("/api/v1/sharing/stop", { method: "POST" });
        else await api("/api/v1/sharing/start", { method: "POST" });
        await refresh();
      };
    }
    const pair = $("btn-pair");
    if (pair) {
      pair.onclick = async () => {
        const session = await api("/api/v1/pairing/start", { method: "POST" });
        state.pairing = session;
        showPairDialog(session);
      };
    }
    const copy = $("btn-copy");
    if (copy) {
      copy.onclick = async () => {
        const url = state.status?.primary_url || (state.status?.url_hints && state.status.url_hints[0]) || "";
        try {
          await navigator.clipboard.writeText(url);
          copy.textContent = "Copied";
          setTimeout(() => (copy.textContent = "Copy address"), 1200);
        } catch {}
      };
    }
    const openFolder = $("btn-open-folder");
    if (openFolder) {
      openFolder.onclick = async () => {
        const path = state.settings?.shared_folder;
        if (window.pywebview?.api?.open_folder && path) {
          await window.pywebview.api.open_folder(path);
        }
      };
    }
    document.querySelectorAll("[data-revoke]").forEach((btn) => {
      btn.onclick = async () => {
        if (!confirm("Revoke this device? It will need to pair again.")) return;
        await api("/api/v1/devices/" + btn.dataset.revoke, { method: "DELETE" });
        await refresh();
      };
    });
    document.querySelectorAll("[data-rename]").forEach((btn) => {
      btn.onclick = async () => {
        const current = btn.dataset.name || "";
        const next = prompt("Rename device", current);
        if (next == null) return;
        const name = next.trim();
        if (!name || name === current) return;
        await api("/api/v1/devices/" + btn.dataset.rename, {
          method: "PATCH",
          body: JSON.stringify({ display_name: name }),
        });
        await refresh();
      };
    });
    const draft = $("clip-draft");
    if (draft) {
      draft.oninput = () => {
        state.clipDraft = draft.value;
        const share = $("btn-share-clip");
        if (share) share.disabled = !draft.value.trim();
      };
    }
    const shareClip = $("btn-share-clip");
    if (shareClip) {
      shareClip.onclick = async () => {
        const text = ($("clip-draft")?.value || "").trim();
        if (!text) return;
        await api("/api/v1/clipboard", { method: "POST", body: JSON.stringify({ text }) });
        state.clipDraft = "";
        await refresh();
      };
    }
    document.querySelectorAll("[data-copy-id]").forEach((btn) => {
      btn.onclick = async () => {
        const item = state.clipboard.find((c) => c.item_id === btn.dataset.copyId);
        if (!item) return;
        try {
          await navigator.clipboard.writeText(item.text || "");
          btn.textContent = "Copied";
          setTimeout(() => (btn.textContent = "Copy"), 1200);
        } catch {}
      };
    });
    document.querySelectorAll("[data-delete-id]").forEach((btn) => {
      btn.onclick = async () => {
        await api("/api/v1/clipboard/" + btn.dataset.deleteId, { method: "DELETE" });
        await refresh();
      };
    });
    const changeFolder = $("btn-change-folder");
    if (changeFolder) {
      changeFolder.onclick = async () => {
        let path = null;
        if (window.pywebview?.api?.pick_folder) {
          path = await window.pywebview.api.pick_folder();
        } else {
          path = prompt("Shared folder path", state.settings?.shared_folder || "");
        }
        if (!path) return;
        await api("/api/v1/settings", {
          method: "PATCH",
          body: JSON.stringify({ shared_folder: path }),
        });
        await refresh();
      };
    }
    const save = $("btn-save-settings");
    if (save) {
      save.onclick = async () => {
        const host_name = $("host-name").value;
        const port = Number($("port").value);
        const launch = document.querySelector('input[name="startup"]:checked')?.value === "1";
        await api("/api/v1/settings", {
          method: "PATCH",
          body: JSON.stringify({ host_name, port, launch_at_startup: launch }),
        });
        await refresh();
        alert("Settings saved. Port changes apply on next restart.");
      };
    }
  }

  async function refresh() {
    try {
      state.status = await api("/api/v1/status");
      state.settings = await api("/api/v1/settings");
      state.devices = (await api("/api/v1/devices")).devices;
      if (state.page === "clipboard") {
        state.clipboard = (await api("/api/v1/clipboard")).items;
      }
      const pending = (await api("/api/v1/pairing/pending")).requests || [];
      const dlg = $("dialog");
      const namingOpen =
        dlg && dlg.style.display !== "none" && dlg.innerHTML.includes("New device wants to pair");
      if (pending.length && !namingOpen) {
        if (state.pairingTimer) clearInterval(state.pairingTimer);
        showApproveDialog(pending[0]);
      } else if (!pending.length && namingOpen) {
        hideDialog();
      }
      render();
    } catch (e) {
      $("main").innerHTML = `<div class="card elev-sm"><div class="dialog-title">Cannot reach ShareBox service</div><div class="dialog-body">${escapeHtml(e.message)}</div></div>`;
    }
  }

  document.querySelectorAll(".nav-item").forEach((el) => {
    el.addEventListener("click", async () => {
      state.page = el.dataset.nav;
      if (state.page === "clipboard") {
        try {
          state.clipboard = (await api("/api/v1/clipboard")).items;
        } catch {}
      }
      render();
    });
  });

  window.addEventListener("pywebviewready", () => refresh());
  setTimeout(refresh, 400);
  setInterval(refresh, 4000);
})();
