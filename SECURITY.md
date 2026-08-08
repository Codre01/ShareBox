# Security policy

## Supported versions

Windows V1 builds published on [GitHub Releases](https://github.com/Bolutifebabs8/ShareBox/releases) are the supported distribution. Prefer the latest release.

## Reporting a vulnerability

Please open a [GitHub issue](https://github.com/Bolutifebabs8/ShareBox/issues) labeled for security, or contact the maintainers privately if the issue is sensitive. Avoid posting full exploit details publicly until a fix is available when possible.

## Design notes

ShareBox V1 is a **local-LAN** tool. See [docs/security.md](docs/security.md) for hardening already applied and residual risks (HTTP on LAN, token storage, shared-folder trust model).
