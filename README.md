# Orca Presence

한국어 | [English](README_en.md)

Orca가 실행 중일 때 Discord 프로필에 `Orca AI Agent IDE` 활동을 표시하는 Windows용 프로그램입니다.

![Discord 프로필에 표시된 모습](example.png)

Orca를 켜면 활동이 자동으로 등록되고, 끄면 사라집니다. Discord가 중간에 종료됐다가 다시 실행돼도 알아서 재연결합니다. 5초마다 프로세스 목록만 확인하므로 CPU 사용량은 거의 없습니다.

## 요구 사항

- Windows 10 / 11
- Discord **데스크톱 앱** (웹 버전에는 Rich Presence가 표시되지 않습니다)
- Python 3.9 이상

## 설치 및 실행

PowerShell에서 실행합니다.

```powershell
py -m pip install -r requirements.txt
py .\orca_presence.py
```

중단하려면 `Ctrl + C`를 누릅니다.

## 단일 EXE로 빌드

Python 설치 없이 쓰고 싶다면 EXE로 만들 수 있습니다.

```powershell
py -m pip install --upgrade pyinstaller
py -m PyInstaller --noconfirm --clean --onefile --windowed --name "OrcaPresence" .\orca_presence.py
```

결과물은 `.\dist\OrcaPresence.exe`에 생성되며, 이 파일 하나만 배포하면 됩니다.

`Win + R` → `shell:startup`으로 열리는 폴더에 이 EXE의 **바로가기**를 넣으면 Windows 로그인 시 자동 실행됩니다.

## 설정 변경

`orca_presence.py` 상단과 `update_presence()` 함수에서 바꿀 수 있습니다.

```python
CLIENT_ID = "1526762915376533706"   # Discord Application ID
IMAGE_KEY = "orca"                  # Developer Portal에 등록한 이미지 키
ORCA_PROCESS_NAME = "orca.exe"      # 감지할 프로세스 이름

details="AI 에이전트와 개발 중"      # 화면에 표시되는 문구
state="Orca IDE 사용 중"
large_text="Orca AI Agent IDE"
```

EXE로 빌드해서 쓰는 경우 수정 후 다시 빌드해야 적용됩니다.

## 문제 해결

**활동이 표시되지 않을 때** — Discord 데스크톱 앱이 실행 중인지, 사용자 설정에서 활동 공유가 켜져 있는지 확인합니다. 그리고 Orca 프로세스 이름이 실제로 `orca.exe`가 맞는지 확인합니다.

```powershell
Get-Process | Where-Object { $_.ProcessName -match "orca" } | Select-Object ProcessName, Id, Path
```

**아이콘이 표시되지 않을 때** — Discord Developer Portal의 Rich Presence > Art Assets에 등록된 이미지 키가 소스의 `IMAGE_KEY`와 정확히 일치해야 합니다. 등록 직후에는 반영에 시간이 걸릴 수 있습니다.

## 참고

Discord Application ID는 공개 식별자라 소스에 포함해도 됩니다. 이 프로그램은 Bot Token이나 Client Secret 같은 비밀값을 사용하지 않습니다.
