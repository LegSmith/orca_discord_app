; Orca Presence 설치 프로그램 (Inno Setup 6)
;
; 빌드 전에 dist\OrcaPresence.exe와 orca.ico가 준비되어 있어야 한다.
;   py tools\make_icon.py
;   py -m PyInstaller --noconfirm --clean --onefile --windowed ^
;       --name OrcaPresence --icon orca.ico --add-data "orca.png;." orca_presence.py
;   iscc installer.iss

#define AppName "Orca Presence"
#define AppVersion "1.0.0"
#define AppPublisher "LegSmith"
#define AppURL "https://github.com/LegSmith/orca_discord_app"
#define AppExeName "OrcaPresence.exe"

; CLIENT_ID 입력 페이지의 기본값. orca_presence.py의 DEFAULT_CLIENT_ID와 같은 값이다.
#define DefaultClientId "1526762915376533706"

; Korean.isl은 Inno Setup 기본 설치에 포함되지 않는 비공식 번역이다.
; 없으면 영어 마법사로만 빌드되도록 조건부로 처리한다.
#define KoreanIsl AddBackslash(CompilerPath) + "Languages\Korean.isl"

[Setup]
; 프로그램 추가/제거에서 이 프로그램을 식별하는 고유값. 절대 바꾸지 말 것.
AppId={{A009D71C-ABCA-48D3-AE34-F5F4BAE21B96}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
VersionInfoVersion={#AppVersion}

; 관리자 권한 없이 사용자 폴더에 설치한다. 시작프로그램 등록도 사용자 단위이므로
; UAC 창을 띄울 이유가 없다. {autopf}는 %LocalAppData%\Programs로 해석된다.
PrivilegesRequired=lowest
DefaultDirName={autopf}\OrcaPresence
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes

; 설치 위치 선택 화면을 항상 보여준다.
DisableDirPage=no

UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}
SetupIconFile=orca.ico

OutputDir=installer_output
OutputBaseFilename=OrcaPresence-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

; 설치 시작 시 한국어/영어 선택 창을 항상 띄운다.
ShowLanguageDialog=yes

[Languages]
#if FileExists(KoreanIsl)
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
#endif
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
#if FileExists(KoreanIsl)
korean.StartupTask=Windows 시작 시 자동으로 실행 (권장)
korean.StartupGroup=추가 작업:
korean.ClientIdTitle=Discord Application ID
korean.ClientIdSubtitle=Discord 프로필에 표시할 앱을 지정합니다.
korean.ClientIdDesc=Discord Developer Portal에서 만든 애플리케이션의 ID를 입력하세요.%n%n기본값을 그대로 두면 Orca AI Agent IDE로 표시됩니다. 직접 만든 앱을 쓰려면 해당 ID로 바꾸세요. 설치 후 config.ini에서 변경할 수도 있습니다.
korean.ClientIdLabel=Application ID:
korean.ClientIdEmpty=Application ID를 입력하세요.
korean.ClientIdInvalid=Application ID는 숫자로만 이루어져야 합니다.%n%nDiscord Developer Portal의 General Information 탭에서 확인할 수 있습니다.
#endif
english.StartupTask=Run automatically when Windows starts (recommended)
english.StartupGroup=Additional tasks:
english.ClientIdTitle=Discord Application ID
english.ClientIdSubtitle=Choose which app appears on your Discord profile.
english.ClientIdDesc=Enter the ID of the application you created in the Discord Developer Portal.%n%nLeaving the default shows it as Orca AI Agent IDE. To use your own app, replace it with that ID. You can also change this later in config.ini.
english.ClientIdLabel=Application ID:
english.ClientIdEmpty=Please enter an Application ID.
english.ClientIdInvalid=The Application ID must contain digits only.%n%nYou can find it on the General Information tab of the Discord Developer Portal.

[Tasks]
; 설치 마법사에 체크박스로 표시된다. 기본은 체크된 상태.
Name: "startup"; Description: "{cm:StartupTask}"; GroupDescription: "{cm:StartupGroup}"

[Files]
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[INI]
; 입력받은 Application ID를 EXE 옆에 저장한다. orca_presence.py의 load_client_id()가 읽는다.
Filename: "{app}\config.ini"; Section: "discord"; Key: "client_id"; String: "{code:GetClientId}"

[UninstallDelete]
; [INI]로 만든 파일은 자동으로 지워지지 않으므로 직접 정리한다.
Type: files; Name: "{app}\config.ini"

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
; shell:startup 폴더. EXE 원본이 아니라 바로가기를 넣어야 제거 시 함께 정리된다.
Name: "{userstartup}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: startup

[Run]
; 완료 화면에 "지금 실행하시겠습니까?" 체크박스로 표시된다.
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; 실행 중이면 EXE를 지울 수 없으므로 먼저 종료시킨다.
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM {#AppExeName}"; Flags: runhidden; RunOnceId: "StopOrcaPresence"

[Code]
var
  ClientIdPage: TInputQueryWizardPage;

{ 설치 위치 선택 다음에 Application ID 입력 페이지를 끼워넣는다. }
procedure InitializeWizard();
begin
  ClientIdPage := CreateInputQueryPage(wpSelectDir,
    ExpandConstant('{cm:ClientIdTitle}'),
    ExpandConstant('{cm:ClientIdSubtitle}'),
    ExpandConstant('{cm:ClientIdDesc}'));

  ClientIdPage.Add(ExpandConstant('{cm:ClientIdLabel}'), False);
  ClientIdPage.Values[0] := '{#DefaultClientId}';
end;

{ 재설치일 때는 기존 config.ini의 값을 미리 채워 넣는다.
  설치 폴더는 wpSelectDir에서 정해지므로 페이지에 진입하는 시점에 읽어야 한다. }
procedure CurPageChanged(CurPageID: Integer);
var
  Existing: String;
begin
  if CurPageID = ClientIdPage.ID then
  begin
    Existing := Trim(GetIniString('discord', 'client_id', '',
                                  ExpandConstant('{app}\config.ini')));
    if Existing <> '' then
      ClientIdPage.Values[0] := Existing;
  end;
end;

function IsAllDigits(Value: String): Boolean;
var
  I: Integer;
begin
  Result := Length(Value) > 0;

  for I := 1 to Length(Value) do
    if (Value[I] < '0') or (Value[I] > '9') then
    begin
      Result := False;
      Exit;
    end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Value: String;
begin
  Result := True;

  if CurPageID = ClientIdPage.ID then
  begin
    Value := Trim(ClientIdPage.Values[0]);

    if Value = '' then
    begin
      MsgBox(ExpandConstant('{cm:ClientIdEmpty}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;

    if not IsAllDigits(Value) then
    begin
      MsgBox(ExpandConstant('{cm:ClientIdInvalid}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
  end;
end;

{ [INI] 항목의 {code:GetClientId}가 이 값을 가져간다. }
function GetClientId(Param: String): String;
begin
  Result := Trim(ClientIdPage.Values[0]);
end;

{ 이 프로그램은 창이 없어서 Inno의 CloseApplications가 감지하지 못한다.
  덮어쓰기 전에 직접 종료시켜야 "파일이 사용 중" 오류가 나지 않는다. }
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM {#AppExeName}',
       '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := '';
end;
