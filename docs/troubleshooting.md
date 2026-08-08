# Troubleshooting

## Phone can’t open the page / QR doesn’t load

1. Confirm the phone is on the **same Wi‑Fi** as the PC (not mobile data, not a different SSID).
2. In Control Center, check that ShareBox shows as **running** and note the **IP:port**.
3. On the phone, try `http://<that-ip>:8765` in the browser (use `http`, not `https`).
4. Temporarily allow **Python** / **ShareBox** through Windows Firewall if prompted — private networks.
5. Some routers enable **AP / client isolation** (common on guest Wi‑Fi). Switch to the main LAN or disable isolation.

## `sharebox.local` doesn’t work

mDNS is best-effort. Use the numeric IP shown in Control Center instead. iOS/Android support for `.local` varies by network.

## Windows SmartScreen / “Unknown publisher”

Expected until the exe is code‑signed. Use **More info → Run anyway** if you trust the download from [this GitHub releases page](https://github.com/Bolutifebabs8/ShareBox/releases/latest). Prefer downloading only from that official repo.

## Control Center is blank or won’t load

1. Quit ShareBox from the tray and start again.
2. Check nothing else is using port **8765**.
3. If you built from source, ensure `web` was built (`npm run build`) and `backend/sharebox/host/` exists.
4. Update WebView2 Runtime (Windows 10/11 usually have it).

## Pairing stuck / “pending” forever

1. Approve or decline on the **PC** Control Center (phones cannot self-approve).
2. Start pairing again if the QR expired (pairing sessions time out).
3. Don’t share the pairing link across different phones — each device should start its own pair flow.

## Upload fails or says file too large

V1 enforces size limits (on the order of ~1 GiB per file / larger per request). Split huge transfers or copy via cable for multi‑GB archives. Stay on Wi‑Fi for the whole upload.

## Device was paired before but now gets errors

Token may have been revoked or app data reset. Pair again from Control Center. Revoked devices must re-pair.

## Can’t see files another device uploaded

Uploads typically land under that device’s named folder inside the shared root. Browse from the share root or that folder. Confirm you’re looking at the same shared folder path shown in Settings.

## Antivirus quarantines the exe

False positives happen with new PyInstaller apps. Restore the file and add an exclusion, or build from source ([CONTRIBUTING.md](../CONTRIBUTING.md)). Report persistent AV hits in an issue.

## Still stuck?

Open a [GitHub issue](https://github.com/Bolutifebabs8/ShareBox/issues/new/choose) with:

- Windows version  
- ShareBox version / release tag  
- Whether host is exe or `python -m sharebox_desktop`  
- Steps to reproduce  
- Any Control Center or terminal error text  
