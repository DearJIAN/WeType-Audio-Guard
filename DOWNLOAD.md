# Download | WeType Audio Guard

[README 中文说明](README.md) · [Changes](CHANGELOG.md) · [Privacy policy](PRIVACY.md)

## Official download: WeType Audio Guard v1.1

WeType Audio Guard is a free and open-source Windows 10/11 x64 utility that attempts to restore application playback sessions unexpectedly muted by WeType voice dictation.

Use only the official [GitHub v1.1 Release](https://github.com/DearJIAN/WeType-Audio-Guard/releases/tag/v1.1):

- [Standalone WeTypeAudioGuard.exe](https://github.com/DearJIAN/WeType-Audio-Guard/releases/download/v1.1/WeTypeAudioGuard.exe)
- [WeTypeAudioGuard-1.1-windows-x64.zip (EXE, documentation and license notices)](https://github.com/DearJIAN/WeType-Audio-Guard/releases/download/v1.1/WeTypeAudioGuard-1.1-windows-x64.zip)

The portable EXE requires no Python installation and does not depend on the maintainer's file paths. Exit previous instances and do not run the original CLI in protection mode at the same time.

### EXE validation

**The packaged v1.1 EXE has been tested on a real Windows computer** with WeType voice dictation and playback sessions. The maintainer confirmed actual sound restoration and no recurrence of the former audio-worker timeout. The GitHub Actions Windows build also passed 46 automated tests, but those tests do not substitute for broad testing on other hardware.

### Code signing policy

[**Code signing policy**](CODE_SIGNING_POLICY.md) · [**Privacy policy**](PRIVACY.md)

**SignPath Foundation application: submitted November 3, 2026; approval pending.**

**The currently published v1.1 EXE is not digitally signed.** Users may therefore see a Microsoft Defender SmartScreen warning or an unknown-publisher warning. Do not disable Windows security protections to use this tool.

The intended arrangement, **only if the application is approved**, is: **Free code signing provided by SignPath.io, certificate by SignPath Foundation**. That wording is not a claim that the current EXE has been signed or that SignPath has accepted this project.

Existing v1.1 binaries and the Git tag will not be replaced or mislabeled as signed. Any future signed build will be independently identifiable and linked to a verifiable source and build.

### Local data and removal

The utility observes local Windows audio-session metadata and writes rotating, local-only diagnostic logs under the current user's %LOCALAPPDATA%\WeTypeAudioGuard\logs directory. It has no speech recording, auto-upload, or remote telemetry feature. To uninstall, exit the tray and remove the downloaded portable EXE; optionally delete the local logs. See [Privacy policy](PRIVACY.md).

## Project and licensing

[Source code](https://github.com/DearJIAN/WeType-Audio-Guard) · [MIT license](LICENSE) · [Third-party notices](THIRD_PARTY_NOTICES.md) · [Issues](https://github.com/DearJIAN/WeType-Audio-Guard/issues)
