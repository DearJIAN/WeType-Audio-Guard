# Code signing policy | WeType Audio Guard

> **Application submitted, approval pending (2026-11-03).** SignPath Foundation has **not** yet approved this project for code signing. **The already published v1.1 EXE is unsigned.** This document describes our intended signing process, not an existing certificate or a signed download.

## Intended signing service

**Free code signing provided by SignPath.io, certificate by SignPath Foundation**

The line above describes a **proposed future arrangement, conditional on approval**. It does not state that SignPath Foundation already provides a certificate for this project. No existing release is retroactively signed or relabeled.

Application status: submission confirmed on November 3, 2026, pending independent review.

## Maintainers, reviewers and approvers

This is an individually maintained open-source project, owned by [DearJIAN](https://github.com/DearJIAN).

| Role | Responsible party | Responsibility |
| --- | --- | --- |
| Authors / committers | Repository owner DearJIAN, and explicitly authorized collaborators if added | Maintain the source code and build scripts |
| Reviewers | DearJIAN; other explicitly trusted reviewers if appointed | Review external contributions and security-significant workflow/dependency changes |
| Signing approver | DearJIAN (project maintainer) | Manually review and approve each future signing request |

The roles describe responsibilities, not an assertion that GitHub branch protection, SignPath accounts or SignPath signing permissions are already configured. SignPath and GitHub multifactor authentication is required before any signing approval is performed. Untrusted pull requests do not acquire signing privileges.

## Source, build and signing provenance

- **Source:** [DearJIAN/WeType-Audio-Guard](https://github.com/DearJIAN/WeType-Audio-Guard).
- **Current version tag:** [v1.1](https://github.com/DearJIAN/WeType-Audio-Guard/tree/v1.1).
- **Windows build process:** [GitHub Actions release workflow](.github/workflows/windows-release.yml), with build dependencies declared in this repository.
- **Current unsigned build controls:** Python compilation and unit tests, original CLI self-test, packaged EXE import and simulated worker/UI checks, SHA-256 build verification, and bundled third-party license notices.
- **Current official binaries:** [GitHub Releases](https://github.com/DearJIAN/WeType-Audio-Guard/releases). The version 1.1 EXE has also been **tested on a real Windows machine**, including restoration of playback during WeType dictation. This real EXE verification is distinct from CI simulation.

**After approval only**, an auditable SignPath-to-GitHub-Actions signing integration may be configured. Each requested signature must be based on verifiable source and controlled build outputs, manually approved by an authorized maintainer, and verified before any signed download is announced. The team will sign only eligible binaries built from its maintained source, and will not misrepresent third-party binaries as its own.

No SignPath signing credentials, certificate, signing workflow or manual-signature approval procedure is currently active. No existing v1.1 release asset or tag will be overwritten merely to add a signature.

## Privacy policy

[Privacy policy](PRIVACY.md)

**This program will not transfer any information to other networked systems unless specifically requested by the user or the person installing or operating it.**

The application reads Windows audio session metadata locally, stores limited diagnostic logs locally, and allows the user to manually view or copy them. It does not capture voice recordings or automatically send logs or telemetry. Users who choose to visit GitHub or share logs are using separately governed services. Third-party dependencies and licenses are described in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Reporting

[Report a problem via GitHub Issues](https://github.com/DearJIAN/WeType-Audio-Guard/issues). Please review and remove any sensitive information before sharing logs. For downloads and current signing status see [DOWNLOAD.md](DOWNLOAD.md).

This policy is maintained on the default branch and does not rewrite historical tagged sources.
