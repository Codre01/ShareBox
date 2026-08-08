# Publishing a release

For maintainers shipping a new version people can download from GitHub.

Each platform is built on its own OS — there is no cross-compilation. A full
release means running both builds and attaching both artifacts to one tag.

## 1. Build

### Windows

```powershell
.\.venv\Scripts\Activate.ps1
powershell -ExecutionPolicy Bypass -File build\build_windows.ps1
```

Artifact: `build\output\ShareBox.exe`

### Linux

```bash
./build/build_linux.sh
```

Artifact: `build/output/sharebox_<version>_<arch>.deb`

Build on the **oldest** distro you intend to support — glibc is forward
compatible, not backward, so a package built on Ubuntu 24.04 runs on 24.10 but
one built on 24.10 will not run on 24.04.

Both artifacts are gitignored — do not commit them.

## 2. Smoke-test

Walk [acceptance-checklist.md](acceptance-checklist.md) on a real LAN with a
phone, on each platform you are shipping.

For the `.deb`, test the install path a real user takes, on a machine that is
not the build machine:

```bash
sudo apt install ./sharebox_0.1.0_amd64.deb
sharebox                 # launches, Control Center opens
sudo apt remove sharebox # clean removal
```

## 3. Version bump

The `.deb` version comes from `desktop/pyproject.toml`. Keep it in step with
`backend/pyproject.toml` and the `version` reported by `/api/v1/health`.

## 4. Tag and release

```bash
git tag v0.1.0
git push origin v0.1.0

gh release create v0.1.0 \
  "build/output/ShareBox.exe" \
  "build/output/sharebox_0.1.0_amd64.deb" \
  --title "ShareBox v0.1.0" \
  --notes-file docs/release-notes-template.md
```

Or draft notes in the GitHub UI and attach both binaries as assets.

## 5. Verify

Open https://github.com/Bolutifebabs8/ShareBox/releases/latest and confirm both
download links work from a fresh machine.
