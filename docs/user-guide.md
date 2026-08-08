# ShareBox user guide

ShareBox turns a folder on your PC into a private share for phones and other devices on the **same Wi‑Fi**. No cloud account. No app install on the phone.

## Install / run

Open the [latest GitHub Release](https://github.com/Bolutifebabs8/ShareBox/releases/latest), then follow your platform:

### Windows

1. Download **ShareBox.exe**.
2. Double‑click to run.  
   - If SmartScreen appears: **More info → Run anyway**.  
   - There is **no installer** — this is a portable app. Put the exe somewhere stable (e.g. `Documents\ShareBox-App\`) if you like, or keep the Desktop shortcut created when you build from source.

### Linux (Debian / Ubuntu / Mint)

1. Download **sharebox_*.deb**.
2. Install it:

   ```bash
   sudo apt install ./sharebox_0.1.0_amd64.deb
   ```

   Keep the `./` — that is what lets apt install the dependencies too.
3. Launch **ShareBox** from your application menu, or run `sharebox`.

More detail, including what to do if the tray icon or menu entry is missing: [linux-run.md](linux-run.md).

Optional: in Control Center → Settings, enable **Launch at startup** so ShareBox comes back after reboot.

## First-time setup

1. Confirm the **shared folder** (default is under your user profile, often `ShareBox`).
2. Keep the Control Center window open (or leave ShareBox running in the tray).
3. Click **Pair new device**.
4. On the new device (same Wi‑Fi):
   - **Phone:** scan the QR code, or  
   - **Another PC:** click **Copy link** in Control Center, paste/open that URL in a browser.
5. On the host PC, **approve** the request and give the device a clear name (this also names its upload folder).
6. On the new device, browse files, upload, download, and use the shared clipboard.

## Everyday use

| On the PC (Control Center) | On the phone (browser) |
|----------------------------|-------------------------|
| See status & LAN address | Open files / folders |
| Pair / approve / rename / revoke devices | Upload into your device folder |
| Change shared folder & settings | Download anything in the share |
| | Download a folder, or **Select** several items, as one .zip |
| Clipboard list (add / delete) | Clipboard tab |

Closing the window usually leaves ShareBox running in the **system tray** — use tray → Quit to stop fully.

## Tips

- **Same Wi‑Fi** is required. Guest/client isolation on some routers blocks device-to-device traffic — see [troubleshooting](troubleshooting.md).
- Use the **IP address** shown in Control Center (e.g. `http://192.168.x.x:8765`). Friendly names like `sharebox.local` are disabled for now — they were unreliable on phones.
- Revoke devices you no longer trust from the Devices page.
- Large uploads: stay on Wi‑Fi; don’t switch networks mid-transfer.

## What ShareBox does *not* do (V1)

- No internet / cloud sync  
- No phone app store install  
- No end-to-end encryption on the wire (LAN HTTP)  
- No official macOS host build yet (Windows and Linux are packaged)  

## More help

- [Troubleshooting](troubleshooting.md)  
- [Security notes](security.md)  
- [GitHub Issues](https://github.com/Bolutifebabs8/ShareBox/issues)  
