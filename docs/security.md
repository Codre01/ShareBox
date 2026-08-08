# ShareBox security notes (V1)

## Hardened in this release

- **Host admin APIs are loopback-only** (pairing start/approve/decline, devices, settings, sharing control, QR). LAN clients cannot self-pair or change the shared folder.
- **`/status` on the LAN** no longer returns pairing tokens or the shared-folder path.
- **Pairing claim secrets** — only the device that requested pairing can redeem the device token after approval.
- **Upload size limits** — 1 GiB per file, 2 GiB per request.
- **CORS** tightened (no `*` + credentials).
- **Desktop shell** validates `open_url` (http/https only) and restricts `open_folder` to the shared folder.

## Accepted residual risks (documented)

- **HTTP on the LAN** — traffic is not confidential against a capable local attacker (see ADR-003). Do not use on hostile networks for sensitive files.
- **Device tokens in `localStorage`** — any XSS in the web client could steal a token; keep the UI free of unsafe HTML.
- **Trusted devices see the whole share** — by design for V1 “family folder” sharing; revoke devices you no longer trust.
- **Editing is per-device and off by default** — pairing grants browse + upload only. Renaming and deleting require the host to tick *Allow this device to rename and delete files* for that device. Deletes move items to a hidden `.sharebox-trash/` folder inside the share; only the host (loopback) can empty it. A device with editing rights can still trash anything in the share, so grant it deliberately.
- **Clipboard is shared among trusted devices** — treat it like a shared scratchpad, not a password vault.

## Report issues

Please open a GitHub issue for security findings. Avoid posting exploit details publicly until a fix is available when possible.
