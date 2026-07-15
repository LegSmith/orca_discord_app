# Orca Presence

한국어 | [English](README_en.md)

Orca가 실행 중일 때 Discord 프로필에 `Orca AI Agent IDE` 활동을 표시하는 Windows용 프로그램입니다.

![Discord 프로필에 표시된 모습](example.png)

Orca를 켜면 활동이 자동으로 등록되고, 끄면 사라집니다. Discord가 중간에 종료됐다가 다시 실행돼도 알아서 재연결합니다. 5초마다 프로세스 목록만 확인하므로 CPU 사용량은 거의 없습니다.

## 요구 사항

- Windows 10 / 11
- Discord **데스크톱 앱** (웹 버전에는 Rich Presence가 표시되지 않습니다)

## 설치

[Releases](https://github.com/LegSmith/orca_discord_app/releases)에서 `OrcaPresence-Setup-x.y.z.exe`를 받아 실행합니다. Python은 설치하지 않아도 됩니다.

마법사는 언어(한국어/영어) 선택으로 시작하고, 이어서 설치 위치와 **Discord Application ID**를 물어봅니다. Application ID는 반드시 입력해야 다음으로 넘어갈 수 있습니다 — [Discord Developer Portal](https://discord.com/developers/applications)에서 애플리케이션을 만들고 **General Information** 탭의 Application ID를 복사해 넣으세요. **Windows 시작 시 자동 실행** 체크박스를 켜두면 로그인할 때마다 백그라운드에서 실행되고, 마지막 화면에서 바로 실행할지 물어봅니다.

아이콘까지 표시하려면 Developer Portal의 **Rich Presence > Art Assets**에 이미지를 `orca`라는 키로 등록해야 합니다.

관리자 권한이 필요 없으며 사용자 폴더(`%LocalAppData%\Programs\OrcaPresence`)에 설치됩니다. 제거는 Windows 설정의 **앱 > 설치된 앱**에서 하면 됩니다.

> 서명되지 않은 프로그램이라 SmartScreen 경고가 뜰 수 있습니다. **추가 정보 > 실행**을 누르면 됩니다.

## 사용법

실행하면 작업 표시줄 우측 알림 영역에 Orca 아이콘이 생깁니다. 아이콘을 우클릭하면 현재 상태(`Orca 미실행` / `Discord 연결 대기 중` / `Discord에 표시 중`)를 볼 수 있고, **종료**로 프로그램을 끌 수 있습니다.

아이콘이 안 보이면 알림 영역의 `^` 버튼을 눌러 숨겨진 아이콘을 펼쳐보세요.

## 소스코드로 실행

개발용으로 직접 실행하려면 Python 3.9 이상이 필요합니다.

```powershell
py -m pip install -r requirements.txt
py .\orca_presence.py
```

중단하려면 `Ctrl + C`를 누릅니다.

## 직접 빌드

`master`에 push하거나 GitHub의 Actions 탭에서 워크플로를 수동 실행하면 설치 파일이 자동으로 만들어집니다. `v1.0.0` 같은 태그를 push하면 Releases에도 자동 등록됩니다.

로컬에서 빌드하려면 [Inno Setup 6](https://jrsoftware.org/isdl.php)을 설치한 뒤 실행합니다.

```powershell
py -m pip install -r requirements.txt pyinstaller
py tools\make_icon.py
py -m PyInstaller --noconfirm --clean --onefile --windowed --name OrcaPresence --icon orca.ico --add-data "orca.png;." orca_presence.py
iscc installer.iss
```

설치 파일은 `installer_output\`에 생성됩니다. 마법사를 한국어로 표시하려면 [Korean.isl](https://raw.githubusercontent.com/jrsoftware/issrc/main/Files/Languages/Unofficial/Korean.isl)을 Inno Setup의 `Languages` 폴더에 넣어야 합니다. 없으면 영어로 빌드됩니다.

## 설정 변경

Application ID는 설치 폴더의 `config.ini`에서 바꿀 수 있습니다. 재설치할 필요 없이 프로그램만 다시 시작하면 적용됩니다.

```ini
[discord]
client_id = 1526762915376533706
```

나머지는 `orca_presence.py`를 고치고 다시 빌드해야 합니다.

```python
IMAGE_KEY = "orca"                  # Developer Portal에 등록한 이미지 키
ORCA_PROCESS_NAME = "orca.exe"      # 감지할 프로세스 이름

details="AI 에이전트와 개발 중"      # 화면에 표시되는 문구
state="Orca IDE 사용 중"
large_text="Orca AI Agent IDE"
```

## 문제 해결

**활동이 표시되지 않을 때** — Discord 데스크톱 앱이 실행 중인지, 사용자 설정에서 활동 공유가 켜져 있는지 확인합니다. 그리고 Orca 프로세스 이름이 실제로 `orca.exe`가 맞는지 확인합니다.

```powershell
Get-Process | Where-Object { $_.ProcessName -match "orca" } | Select-Object ProcessName, Id, Path
```

**아이콘이 표시되지 않을 때** — Discord Developer Portal의 Rich Presence > Art Assets에 등록된 이미지 키가 소스의 `IMAGE_KEY`와 정확히 일치해야 합니다. 등록 직후에는 반영에 시간이 걸릴 수 있습니다.

## 참고

Discord Application ID는 공개 식별자라 소스에 포함해도 됩니다. 이 프로그램은 Bot Token이나 Client Secret 같은 비밀값을 사용하지 않습니다.
