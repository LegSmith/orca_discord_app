import ctypes
from ctypes import wintypes
import time
from typing import Optional

import psutil
from pypresence import Presence


# Discord Developer Portal에서 복사한 Application ID
CLIENT_ID = "1526762915376533706"

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
    rpc = Presence(CLIENT_ID)
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


def main() -> None:
    mutex = acquire_single_instance_mutex()

    if mutex is None:
        # --windowed로 빌드하면 콘솔이 없으므로 별도 메시지 없이 종료한다.
        return

    rpc: Optional[Presence] = None
    presence_started_at = 0
    last_presence_refresh = 0.0

    try:
        while True:
            orca_running = is_orca_running()

            if not orca_running:
                if rpc is not None:
                    close_presence(rpc)
                    rpc = None
                    presence_started_at = 0
                    last_presence_refresh = 0.0

                time.sleep(CHECK_INTERVAL_SECONDS)
                continue

            # Orca는 켜져 있지만 Discord 연결이 없는 경우 계속 재시도한다.
            if rpc is None:
                try:
                    rpc = connect_presence()
                    presence_started_at = int(time.time())
                    update_presence(rpc, presence_started_at)
                    last_presence_refresh = time.monotonic()
                except Exception:
                    close_presence(rpc)
                    rpc = None
                    time.sleep(CHECK_INTERVAL_SECONDS)
                    continue

            # Discord가 중간에 종료되거나 재실행된 경우를 감지하기 위해 주기적으로 갱신한다.
            if time.monotonic() - last_presence_refresh >= PRESENCE_REFRESH_SECONDS:
                try:
                    update_presence(rpc, presence_started_at)
                    last_presence_refresh = time.monotonic()
                except Exception:
                    close_presence(rpc)
                    rpc = None

            time.sleep(CHECK_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        pass
    finally:
        close_presence(rpc)
        release_mutex(mutex)


if __name__ == "__main__":
    main()
