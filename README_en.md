# Orca Presence

[한국어](README.md) | English

A Windows program that shows an `Orca AI Agent IDE` activity on your Discord profile while Orca is running.

![How it looks on a Discord profile](example.png)

The activity is registered automatically when Orca starts and disappears when it exits. If Discord is closed and reopened, the program reconnects on its own. It only polls the process list every 5 seconds, so CPU usage is negligible.

## Requirements

- Windows 10 / 11
- Discord **desktop app** (Rich Presence does not show up on the web version)

## Install

Download `OrcaPresence-Setup-x.y.z.exe` from [Releases](https://github.com/LegSmith/orca_discord_app/releases) and run it. You do not need Python.

The wizard starts by asking for a language (Korean or English), then for an install location and a **Discord Application ID**. Leaving the ID at its default shows the activity as `Orca AI Agent IDE`; enter your own app's ID to use that instead. A **Run automatically when Windows starts** checkbox makes it launch in the background at every login, and the final page asks whether to start it right away.

It installs per-user (`%LocalAppData%\Programs\OrcaPresence`) and needs no administrator rights. Uninstall from **Apps > Installed apps** in Windows Settings.

> The program is unsigned, so SmartScreen may warn you. Click **More info > Run anyway**.

## Usage

Once running, an Orca icon appears in the notification area at the right of the taskbar. Right-click it to see the current status (`Orca 미실행` / `Discord 연결 대기 중` / `Discord에 표시 중`) and to **종료** (quit) the program.

If you cannot see the icon, click the `^` button in the notification area to expand hidden icons.

## Run from source

For development you will need Python 3.9 or later.

```powershell
py -m pip install -r requirements.txt
py .\orca_presence.py
```

Press `Ctrl + C` to stop.

## Building it yourself

Pushing to `master` or running the workflow manually from the Actions tab builds the installer for you. Pushing a tag like `v1.0.0` also publishes it to Releases.

To build locally, install [Inno Setup 6](https://jrsoftware.org/isdl.php) and run:

```powershell
py -m pip install -r requirements.txt pyinstaller
py tools\make_icon.py
py -m PyInstaller --noconfirm --clean --onefile --windowed --name OrcaPresence --icon orca.ico --add-data "orca.png;." orca_presence.py
iscc installer.iss
```

The installer lands in `installer_output\`. For a Korean wizard, drop [Korean.isl](https://raw.githubusercontent.com/jrsoftware/issrc/main/Files/Languages/Unofficial/Korean.isl) into Inno Setup's `Languages` folder; without it the build falls back to English.

## Configuration

The Application ID lives in `config.ini` in the install folder. Edit it and restart the program — no reinstall needed.

```ini
[discord]
client_id = 1526762915376533706
```

Everything else requires editing `orca_presence.py` and rebuilding.

```python
IMAGE_KEY = "orca"                  # Image key registered in the Developer Portal
ORCA_PROCESS_NAME = "orca.exe"      # Process name to watch for

details="AI 에이전트와 개발 중"      # Text shown on the profile
state="Orca IDE 사용 중"
large_text="Orca AI Agent IDE"
```

## Troubleshooting

**The activity does not appear** — Check that the Discord desktop app is running and that activity sharing is enabled in User Settings. Then confirm the Orca process is actually named `orca.exe`:

```powershell
Get-Process | Where-Object { $_.ProcessName -match "orca" } | Select-Object ProcessName, Id, Path
```

**The icon does not appear** — The image key registered under Rich Presence > Art Assets in the Discord Developer Portal must match `IMAGE_KEY` in the source exactly. It can take a little while to propagate after uploading.

## Notes

The Discord Application ID is a public identifier, so it is fine to keep it in source. This program does not use any secrets such as a Bot Token or Client Secret.
