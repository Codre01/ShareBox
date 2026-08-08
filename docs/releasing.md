# Publishing a release

Releases are built by CI. Tag the commit and the
[Release workflow](../.github/workflows/release.yml) builds both artifacts and
attaches them to a **draft** GitHub Release.

It stops at a draft on purpose. Neither artifact is code-signed, and
[acceptance-checklist.md](acceptance-checklist.md) needs a real LAN and a real
phone. Automation handles the building; a human smoke-tests and presses Publish.

## 1. Bump the version

The workflow refuses to build if the tag and the code disagree, so update both
files first:

- `backend/pyproject.toml`
- `desktop/pyproject.toml`

A tag of `v0.1.1` requires `version = "0.1.1"` in both. The `.deb` filename and
the version reported by `/api/v1/health` come from here.

## 2. Tag and push

```bash
git tag v0.1.1
git push origin v0.1.1
```

The workflow then:

1. **verify** — checks tag against both pyproject files, runs the test suite
2. **build-linux** — `sharebox_<version>_amd64.deb` on ubuntu-latest
3. **build-windows** — `ShareBox.exe` on windows-latest
4. **release** — writes `SHA256SUMS.txt`, creates the draft with notes generated
   from merged PRs (categorised by [.github/release.yml](../.github/release.yml))

To build a tag that already exists, run **Release** from the Actions tab and give
it the tag name. Re-running replaces the assets on an existing draft.

## 3. Smoke-test the draft

Download both assets from the draft and walk
[acceptance-checklist.md](acceptance-checklist.md) on a machine that is **not**
the build machine.

```bash
sudo apt install ./sharebox_0.1.1_amd64.deb
sharebox                 # launches, Control Center opens
sudo apt remove sharebox # clean removal
```

## 4. Edit the notes and publish

The generated notes list merged PRs.
[release-notes-template.md](release-notes-template.md) is the guide for the human
summary at the top. Then press **Publish release**.

---

## What the automation does not do

**Code signing.** Neither artifact is signed. Windows SmartScreen will still warn
on first run, and the `.deb` is unsigned too. `SHA256SUMS.txt` at least lets
people verify a download matches what CI produced. Real signing needs a
certificate and repository secrets, and is worth doing before wide distribution.

**Compatibility beyond the build image.** The `.deb` is built on `ubuntu-latest`
(24.04), which fixes two floors:

- glibc is forward- but not backward-compatible, so the package will not run on
  meaningfully older distros.
- The dependency is `gir1.2-webkit2-4.1`. Ubuntu 22.04 ships the older
  `gir1.2-webkit2-4.0` under a different package name, so the package will not
  satisfy dependencies there.

In practice this targets **Ubuntu 24.04+, Debian 13+, Mint 22+**. Going older
means pinning `runs-on: ubuntu-22.04` *and* overriding `SHAREBOX_DEPENDS` for the
4.0 typelib — a second build, not a flag flip.

**Other architectures.** amd64 only. arm64 would need an `ubuntu-24.04-arm`
runner and a build matrix.

**macOS.** No build — there is no macOS host shell yet.

## Building locally

Still supported, and what you want when debugging packaging:

```bash
./build/build_linux.sh                       # Linux
powershell -File build\build_windows.ps1     # Windows
```

Both write to `build/output/` (gitignored — do not commit artifacts). The Windows
script drops a Desktop shortcut for convenience; pass `-SkipShortcut`, or set
`CI`, to suppress it.
