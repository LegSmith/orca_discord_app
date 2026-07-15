import asyncio
import configparser
import ctypes
import sys
import threading
import time
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import psutil
import pystray
from PIL import Image
from pypresence import Presence


# Discord Developer Portal에서 복사한 Application ID.
# 설치 프로그램이 config.ini에 값을 써두면 그쪽이 우선하고, 없으면 이 값을 쓴다.
DEFAULT_CLIENT_ID = "1526762915376533706"

# EXE와 같은 폴더에 놓이는 설정 파일 이름
CONFIG_FILENAME = "config.ini"

# Rich Presence > Art Assets에 등록한 이미지 키
IMAGE_KEY = "orca"

# Orca 실행 파일명 (프로세스 이름 비교는 소문자로 수행한다)
ORCA_PROCESS_NAME = "orca.exe"

# Orca 실행 여부를 확인하는 주기
CHECK_INTERVAL_SECONDS = 5

# Discord 상태를 다시 갱신하는 주기
PRESENCE_REFRESH_SECONDS = 15

# 동일 프로그램의 중복 실행을 막기 위한 Windows Mutex 이름
MUTEX_NAME = "Local\\OrcaPresence_1526762915376533706"


@dataclass
class Status:
    """감시 스레드가 기록하고 트레이 메뉴가 읽는 현재 상태.

    양쪽 모두 bool 하나를 읽고 쓸 뿐이라 별도의 잠금은 두지 않는다.
    """

    orca_running: bool = False
    connected: bool = False


def resource_path(name: str) -> Path:
    """번들에 포함된 읽기 전용 리소스의 경로를 돌려준다."""
    # --onefile로 묶으면 실행 시점에 임시 폴더로 풀리고 그 경로가 _MEIPASS에 담긴다.
    bundle_dir = getattr(sys, "_MEIPASS", None)

    if bundle_dir:
        return Path(bundle_dir) / name

    return Path(__file__).resolve().parent / name


def config_path() -> Path:
    """설정 파일 경로를 돌려준다.

    resource_path()와 달리 번들 임시 폴더가 아니라 EXE가 실제로 설치된 폴더를
    가리켜야 한다. 임시 폴더는 실행이 끝나면 사라지기 때문이다.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / CONFIG_FILENAME

    return Path(__file__).resolve().parent / CONFIG_FILENAME


def load_client_id() -> str:
    """설치 시 입력받은 Application ID를 읽는다. 없거나 깨졌으면 기본값을 쓴다."""
    parser = configparser.ConfigParser()

    try:
        parser.read(config_path(), encoding="utf-8")
        client_id = parser.get("discord", "client_id", fallback="").strip()
    except (configparser.Error, OSError):
        return DEFAULT_CLIENT_ID

    return client_id or DEFAULT_CLIENT_ID


def _kernel32() -> ctypes.WinDLL:
    """HANDLE이 32비트로 잘리지 않도록 시그니처를 지정한 kernel32를 돌려준다."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    kernel32.CreateMutexW.argtypes = (
        wintypes.LPVOID,
        wintypes.BOOL,
        wintypes.LPCWSTR,
    )
    kernel32.CreateMutexW.restype = wintypes.HANDLE

    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL

    return kernel32


def acquire_single_instance_mutex() -> Optional[int]:
    """동일한 프로그램이 이미 실행 중이면 None을 돌려준다."""
    kernel32 = _kernel32()
    mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)

    # CreateMutexW는 이미 존재하는 Mutex에 대해서도 유효한 핸들을 돌려주므로
    # 중복 실행 여부는 반환값이 아니라 마지막 오류 코드로 판단해야 한다.
    last_error = ctypes.get_last_error()

    if not mutex:
        raise ctypes.WinError(last_error)

    error_already_exists = 183
    if last_error == error_already_exists:
        kernel32.CloseHandle(mutex)
        return None

    return mutex


def release_mutex(mutex: Optional[int]) -> None:
    """프로그램 종료 시 Windows Mutex를 해제한다."""
    if mutex:
        _kernel32().CloseHandle(mutex)


def is_orca_running() -> bool:
    """Orca 프로세스가 하나라도 실행 중인지 확인한다."""
    for process in psutil.process_iter(["name"]):
        try:
            process_name = (process.info.get("name") or "").lower()

            if process_name == ORCA_PROCESS_NAME.lower():
                return True

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue

    return False


def connect_presence() -> Presence:
    """실행 중인 Discord 데스크톱 앱에 연결한다."""
    rpc = Presence(load_client_id())
    rpc.connect()
    return rpc


def update_presence(rpc: Presence, started_at: int) -> None:
    """Discord Rich Presence 내용을 등록하거나 갱신한다."""
    rpc.update(
        details="AI 에이전트와 개발 중",
        state="Orca IDE 사용 중",
        start=started_at,
        large_image=IMAGE_KEY,
        large_text="Orca AI Agent IDE",
    )


def close_presence(rpc: Optional[Presence]) -> None:
    """Discord 활동을 제거하고 RPC 연결을 닫는다."""
    if rpc is None:
        return

    try:
        rpc.clear()
    except Exception:
        pass

    try:
        rpc.close()
    except Exception:
        pass


def presence_loop(stop_event: threading.Event, status: Status) -> None:
    """Orca를 감시하며 Discord 활동을 등록/해제한다. 트레이와 별도 스레드로 돈다."""
    # pypresence는 내부적으로 asyncio.get_event_loop()를 호출하는데, 메인 스레드가
    # 아닌 곳에는 기본 루프가 없어 RuntimeError가 난다. 이 스레드 전용 루프를 붙여준다.
    # Windows는 Python 3.8부터 기본 정책이 Proactor라 명명 파이프 통신에 문제가 없다.
    asyncio.set_event_loop(asyncio.new_event_loop())

    rpc: Optional[Presence] = None
    presence_started_at = 0
    last_presence_refresh = 0.0

    try:
        while not stop_event.is_set():
            orca_running = is_orca_running()
            status.orca_running = orca_running

            if not orca_running:
                if rpc is not None:
                    close_presence(rpc)
                    rpc = None
                    presence_started_at = 0
                    last_presence_refresh = 0.0

                status.connected = False
                stop_event.wait(CHECK_INTERVAL_SECONDS)
                continue

            # Orca는 켜져 있지만 Discord 연결이 없는 경우 계속 재시도한다.
            if rpc is None:
                try:
                    rpc = connect_presence()
                    presence_started_at = int(time.time())
                    update_presence(rpc, presence_started_at)
                    last_presence_refresh = time.monotonic()
                    status.connected = True
                except Exception:
                    close_presence(rpc)
                    rpc = None
                    status.connected = False
                    stop_event.wait(CHECK_INTERVAL_SECONDS)
                    continue

            # Discord가 중간에 종료되거나 재실행된 경우를 감지하기 위해 주기적으로 갱신한다.
            if time.monotonic() - last_presence_refresh >= PRESENCE_REFRESH_SECONDS:
                try:
                    update_presence(rpc, presence_started_at)
                    last_presence_refresh = time.monotonic()
                except Exception:
                    close_presence(rpc)
                    rpc = None
                    status.connected = False

            stop_event.wait(CHECK_INTERVAL_SECONDS)

    finally:
        close_presence(rpc)
        status.connected = False


def build_tray_icon(stop_event: threading.Event, status: Status) -> pystray.Icon:
    """작업 표시줄 우측 알림 영역에 표시할 트레이 아이콘을 만든다."""
    image = Image.open(resource_path("orca.png"))

    def status_text(_item) -> str:
        if not status.orca_running:
            return "Orca 미실행"
        if status.connected:
            return "Discord에 표시 중"
        return "Discord 연결 대기 중"

    def on_quit(icon: pystray.Icon, _item) -> None:
        stop_event.set()
        icon.stop()

    menu = pystray.Menu(
        # 클릭할 수 없는 상태 표시줄. 메뉴를 열 때마다 현재 상태로 갱신된다.
        pystray.MenuItem(status_text, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("종료", on_quit),
    )

    return pystray.Icon("orca_presence", image, "Orca Presence", menu)


def main() -> None:
    mutex = acquire_single_instance_mutex()

    if mutex is None:
        # --windowed로 빌드하면 콘솔이 없으므로 별도 메시지 없이 종료한다.
        return

    status = Status()
    stop_event = threading.Event()

    worker = threading.Thread(
        target=presence_loop,
        args=(stop_event, status),
        daemon=True,
    )
    worker.start()

    icon = build_tray_icon(stop_event, status)

    try:
        # pystray는 메인 스레드에서 자체 이벤트 루프를 돌리며, 종료 메뉴를 누르면 반환된다.
        icon.run()
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        worker.join(timeout=CHECK_INTERVAL_SECONDS + 5)
        release_mutex(mutex)


if __name__ == "__main__":
    main()
