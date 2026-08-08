# ShareBox acceptance checklist (§162)
# Run manually on each host platform, with a phone on the same LAN, after packaging.

- [ ] Install ShareBox without developer dependencies (PyInstaller artifact or portable folder)
- [ ] Create/select shared folder
- [ ] LAN service starts reliably
- [ ] Pair phone via QR
- [ ] Unauthorized devices cannot browse files
- [ ] Trusted device reconnects without pairing again
- [ ] Host files browsable; subfolders work
- [ ] Download works
- [ ] Upload from phone; device folder created only on first upload
- [ ] Duplicate uploads rename instead of overwrite
- [ ] Multi-file upload works
- [ ] Large transfer does not require equivalent RAM (streamed)
- [ ] Revocation removes access immediately
- [ ] Path traversal attempts fail (covered by automated tests)
- [ ] Works offline / without internet
- [ ] Host filesystem changes appear in browser (watcher + SSE)
- [ ] Tray open/quit works
- [ ] Launch-at-startup works when enabled
- [ ] Network/IP change does not require re-pairing
- [ ] Critical errors are understandable
- [ ] Clean uninstall / delete portable folder works
- [ ] `pytest` critical-path suite passes

Automated coverage lives in `backend/tests/`.

## Linux (.deb) only

- [ ] `sudo apt install ./sharebox_*.deb` pulls GTK dependencies automatically
- [ ] App appears in the application menu with the ShareBox icon
- [ ] `sharebox` on the command line launches the same app
- [ ] Tray icon appears (with `gir1.2-ayatanaappindicator3-0.1` installed)
- [ ] Launch-at-startup writes `~/.config/autostart/sharebox.desktop` and survives reboot
- [ ] "Open folder" opens the shared folder in the system file manager
- [ ] `sudo apt remove sharebox` removes the app and leaves `~/.config/sharebox` + `~/ShareBox` intact
- [ ] Installs on a machine that is *not* the build machine
