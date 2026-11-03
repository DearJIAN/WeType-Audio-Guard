# Privacy policy | WeType Audio Guard

**Last updated: November 3, 2026. Applies to WeType Audio Guard 1.1.**

WeType Audio Guard is a locally running Windows audio utility. It does not require an account, does not include telemetry, does not record microphone audio, and does not automatically upload data. This policy describes the utility itself, not the privacy policies of Windows, WeType Input, GitHub, or other programs.

## Local information the software reads

To detect active voice input and unexpectedly muted playback sessions, the program queries Windows Core Audio / WASAPI interfaces. This can expose current audio capture and playback session activity, mute flags, endpoint and session identifiers, and local process names or identifiers. It also inspects Python process command-line metadata when checking for a simultaneously running CLI protection instance.

For the single-instance guard, the application derives a local hashed identifier from the current Windows user SID. That identifier is not used for remote identification or transmitted to a server.

**The program does not record, transcribe, store or transmit microphone audio, spoken words or meeting content.**

## Changes to the local system

When protection is active, the program may unmute a previously unmuted Windows application audio session or playback endpoint that became muted during WeType dictation. It does not mute/unmute microphone inputs, change master volume numbers, configure Windows communications, register startup tasks, or modify system services.

Protection is requested automatically each time the program is launched, and the user can pause or exit through the tray. Because an intentional mute during the short recovery window cannot always be distinguished from a WeType-induced mute, the program may occasionally undo an intentional playback mute.

## Diagnostics and local retention

The tray app writes local rotating files under the current user's Windows profile:

    %LOCALAPPDATA%\WeTypeAudioGuard\logs\

The primary files are audio.log and tray.log. Current logging configuration rotates each file at approximately 1 MiB with up to three backups. Logs contain state changes, elapsed times, restoration counts and sanitized warning/error codes. Session labels, full process IDs, device identifiers, and raw exceptions are not intentionally included in tray logs, but usage timestamps and diagnostic context may still be sensitive.

- **View logs:** creates or refreshes a local recent-diagnostics.txt snapshot in the logs directory and opens that snapshot using Windows Notepad.
- **Copy logs:** places selected recent log text into the Windows clipboard. Other local applications may access the clipboard under applicable Windows behavior.
- **Sharing:** the app does not send either the files or clipboard content over the network. A user may choose to paste the information into a chat, issue, email, or other service. Review the text for sensitive details before sharing.

The original command-line diagnostic tool may print executable names, session labels, local process identifiers or device identifiers to the **local terminal**. It does not automatically transmit this output.

Local logs are retained until rotation or manual deletion. The user can exit the app and delete the portable EXE to stop using it; local logs may be manually deleted afterward.

## Network access and third-party privacy

There is no built-in analytics, advertisement, automatic update mechanism, crash report upload, remote authentication or user data collection endpoint. The application's audio-guard operation does not initiate network transfers.

The program relies on Windows facilities and open-source dependencies. See [Third-party notices](THIRD_PARTY_NOTICES.md) for components and licenses. If users manually visit GitHub to download releases, read documentation, file issues, or share logs, those actions are governed by [GitHub's privacy statement](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement).

The maintainer's separate application to the [SignPath Foundation](https://signpath.org/) for code-signing services does not introduce SignPath data collection into the running Windows program. The application has not yet been accepted or signed.

## Contact

Questions or suspected privacy issues: [GitHub Issues](https://github.com/DearJIAN/WeType-Audio-Guard/issues). Avoid posting unreviewed diagnostic logs on public issues.

This privacy policy may change with later versions; updating this file does not modify already published EXE binaries.
