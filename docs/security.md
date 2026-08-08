# ShareBox security notes (V1)

## Hardened in this release

- **Host admin APIs are loopback-only** (pairing start/approve/decline, devices, settings, sharing control, QR). LAN clients cannot self-pair or change the shared folder.
- **`/status` on the LAN** no longer returns pairing tokens or the shared-folder path.
- **Pairing claim secrets** — only the device that requested pairing can redeem the device token after approval.
- **Upload size limits** — 1 GiB per file, 2 GiB per request.
- **CORS** tightened (no `*` + credentials).
- **Desktop shell** validates `open_url` (http/https only) and restricts `open_folder` to the shared folder.

## Optional: HTTPS on the LAN

Settings → **Encrypt traffic on the network (HTTPS)**. Off by default; takes
effect on restart.

When enabled, the host generates a self-signed certificate covering `localhost`
and its current LAN addresses, kept in the app-data directory (`tls/`). The
certificate is regenerated when it is close to expiry or when the machine picks
up a LAN address it does not cover — joining a different Wi-Fi network, for
example.

The private key is chmod `0600` **on Linux and macOS only**. Windows `chmod`
cannot express owner-only, so there it relies on `%LOCALAPPDATA%` already being
unreadable to other unprivileged users; restricting it properly on Windows would
mean setting ACLs, which ShareBox does not do yet.

**What this does and does not buy you.** It encrypts traffic against passive
sniffing on the network, which plain HTTP does not. It does *not* authenticate
the host on first contact: ShareBox has no domain name and cannot reach a public
CA, so browsers show a warning the first time each device connects. Control
Center displays the certificate's SHA-256 fingerprint; compare it with the one
the browser shows before continuing. Accepting blindly on a hostile network
leaves you open to an active man-in-the-middle.

The Control Center window keeps talking to a **loopback-only plain-HTTP listener**
on `port + 1` while HTTPS serves the LAN. That avoids teaching the embedded
WebView to trust a self-signed certificate — WebView2 and WebKitGTK each refuse
that differently — and the listener is bound to `127.0.0.1`, so it is never
reachable from the network.

## Accepted residual risks (documented)

- **HTTP on the LAN by default** — traffic is not confidential against a capable local attacker (see ADR-003). Turn on HTTPS above, or avoid hostile networks for sensitive files.
- **Self-signed trust on first use** — with HTTPS on, the first connection from each device is only as trustworthy as the fingerprint check the user performs.
- **Device tokens in `localStorage`** — any XSS in the web client could steal a token; keep the UI free of unsafe HTML.
- **Trusted devices see the whole share** — by design for V1 “family folder” sharing; revoke devices you no longer trust.
- **Editing is per-device and off by default** — pairing grants browse + upload only. Renaming and deleting require the host to tick *Allow this device to rename and delete files* for that device. Deletes move items to a hidden `.sharebox-trash/` folder inside the share; only the host (loopback) can empty it. A device with editing rights can still trash anything in the share, so grant it deliberately.
- **Clipboard is shared among trusted devices** — treat it like a shared scratchpad, not a password vault.

## Report issues

Please open a GitHub issue for security findings. Avoid posting exploit details publicly until a fix is available when possible.
