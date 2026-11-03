# SignPath Foundation application — November 3, 2026

**Project:** [WeType Audio Guard](https://github.com/DearJIAN/WeType-Audio-Guard)

## Status

- The maintainer submitted the SignPath Foundation free OSS signing application on **2026-11-03** and observed the submission confirmation page.
- **SignPath has not yet confirmed approval or enabled signing** for this project.
- The published [v1.1](https://github.com/DearJIAN/WeType-Audio-Guard/releases/tag/v1.1) standalone Windows EXE remains **unsigned**. Its release tag and binary are not to be changed or represented as signed.
- The **packaged Windows EXE** has been tested by the maintainer on a real Windows system. It restored playback sessions during WeType dictation, and the earlier worker-timeout warning did not recur. Windows Actions separately passed **46 automated tests**, including frozen EXE simulation. This does not establish compatibility with all drivers or hardware.

## Public application materials

- [Code signing policy](../CODE_SIGNING_POLICY.md): roles, proposed provider, current status, review and manual-approval plan.
- [Privacy policy](../PRIVACY.md): audio-session metadata, local logs, manual clipboard export, no telemetry.
- [Download page](../DOWNLOAD.md): official unsigned v1.1 binaries and future-signing disclaimer.
- [Windows audio validation](windows-tray-validation.md): reproducible logs and field-test boundaries.

## Pending action

Wait for the actual SignPath response. If approved, configure an auditable and manually approved source-to-signature workflow, meet its identity/MFA requirements and publish a separately identifiable signed release only after verifying the Authenticode signature. Do not invent application status, certificate ownership or signing success.

Personal application information and email addresses are intentionally excluded from this public record.
