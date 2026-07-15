# Orca Presence

Orca가 실행 중일 때 Discord 프로필에 `Orca AI Agent IDE` 활동을 표시하는 Windows용 프로그램입니다.

## 동작 방식

- `Orca.exe` 실행 감지 → Discord 활동 표시
- Orca 종료 감지 → Discord 활동 제거
- Orca 재실행 → 활동 자동 재등록
- Discord가 중간에 종료됐다가 다시 실행되어도 자동 재연결
- 프로그램 중복 실행 방지
- 5초마다 프로세스만 확인하므로 CPU 사용량은 일반적으로 매우 낮음

## 필요한 환경

- Windows 10 또는 Windows 11
- Discord 데스크톱 앱
- Orca
- 소스코드로 실행할 경우 Python 3.9 이상

웹 브라우저에서 실행한 Discord에는 Rich Presence가 표시되지 않을 수 있으므로 Discord 데스크톱 앱을 사용해야 합니다.

## 현재 설정

`orca_presence.py` 상단에서 다음 값을 사용합니다.

```python
CLIENT_ID = "1526762915376533706"
IMAGE_KEY = "orca"
ORCA_PROCESS_NAME = "orca.exe"
```

Discord Developer Portal의 Rich Presence 이미지 키가 `orca`여야 Orca 아이콘이 표시됩니다.

업로드한 원본 파일 이름이 `orca.png`여도, Developer Portal에서 등록된 이미지 키가 `orca`라면 문제없습니다.

## 소스코드 실행

PowerShell에서 필요한 패키지를 설치합니다.

```powershell
py -m pip install --upgrade pypresence psutil
```

프로그램을 실행합니다.

```powershell
py .\orca_presence.py
```

콘솔 실행을 중단하려면 `Ctrl + C`를 누릅니다.

## 단일 EXE 빌드

PyInstaller와 Pillow를 설치합니다.

```powershell
py -m pip install --upgrade pyinstaller pillow
```

`orca.png`를 EXE 아이콘으로 사용하여 빌드하는 예시입니다.

```powershell
py -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name "OrcaPresence" `
  --icon "C:\Users\사용자명\Desktop\orca.png" `
  ".\orca_presence.py"
```

빌드가 완료되면 다음 위치에 EXE가 생성됩니다.

```text
.\dist\OrcaPresence.exe
```

`--onefile`로 만들어진 EXE에는 Python 런타임과 필요한 라이브러리가 포함되므로 다른 Windows PC에 Python을 설치하지 않아도 됩니다.

Discord에 표시되는 큰 Orca 이미지는 EXE 내부의 PNG를 읽는 것이 아니라 Discord Developer Portal에 등록한 `orca` 이미지를 사용합니다.

## Windows 시작프로그램 등록

1. `Win + R`을 누릅니다.
2. 아래 명령을 입력합니다.

```text
shell:startup
```

3. 열린 시작프로그램 폴더에 `OrcaPresence.exe`의 바로가기를 넣습니다.
4. 다음 Windows 로그인부터 프로그램이 백그라운드에서 자동 실행됩니다.

EXE 원본을 시작프로그램 폴더에 복사하기보다는 바로가기를 넣는 방식을 권장합니다.

## 실행 여부 확인

PowerShell에서 다음 명령을 실행합니다.

```powershell
Get-Process OrcaPresence -ErrorAction SilentlyContinue |
Select-Object ProcessName, Id, Path
```

PyInstaller의 `--onefile` 프로그램은 한 번 실행했을 때 부모 프로세스와 자식 프로세스가 함께 표시될 수 있습니다. 이 소스에는 중복 실행 방지가 포함되어 있으므로 EXE를 다시 실행해도 별도 인스턴스가 계속 추가되지 않습니다.

## 프로그램 종료

PowerShell에서 종료할 수 있습니다.

```powershell
Stop-Process -Name OrcaPresence -Force
```

작업 관리자에서 `OrcaPresence`를 종료해도 됩니다.

## 상태 문구 변경

`update_presence()` 함수의 아래 값을 수정합니다.

```python
details="AI 에이전트와 개발 중",
state="Orca IDE 사용 중",
large_text="Orca AI Agent IDE",
```

수정한 뒤 EXE를 다시 빌드해야 변경 내용이 적용됩니다.

## 다른 PC에서 사용

다른 Windows PC에는 다음 조건만 필요합니다.

- Discord 데스크톱 앱이 실행 중일 것
- Orca 프로세스 이름이 `orca.exe`일 것
- 인터넷 연결이 가능할 것

배포할 파일은 기본적으로 `OrcaPresence.exe` 하나면 됩니다.

## 보안

Discord Application ID는 공개 식별자이므로 소스코드나 EXE에 포함할 수 있습니다.

다음 값은 코드나 저장소에 넣으면 안 됩니다.

- Discord Bot Token
- Client Secret
- 사용자 계정 토큰

이 프로그램에는 위 비밀값이 필요하지 않습니다.

## 문제 해결

### Discord에 활동이 표시되지 않음

다음을 확인합니다.

- Discord 웹이 아닌 데스크톱 앱인지
- Discord 사용자 설정에서 활동 공유가 활성화되어 있는지
- `CLIENT_ID`가 올바른지
- Developer Portal 이미지 키가 정확히 `orca`인지
- Orca 프로세스 이름이 `orca.exe`인지

프로세스 이름 확인:

```powershell
Get-Process |
Where-Object {
    $_.ProcessName -match "orca"
} |
Select-Object ProcessName, Id, Path
```

### Orca 아이콘이 표시되지 않음

Discord Developer Portal에서 이미지가 등록되어 있어야 하며, 소스의 `IMAGE_KEY`와 등록된 이미지 키가 정확히 일치해야 합니다.

```python
IMAGE_KEY = "orca"
```

이미지 등록 직후에는 Discord 쪽 반영에 약간의 시간이 걸릴 수 있습니다.
