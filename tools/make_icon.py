"""orca.png를 Windows 아이콘(orca.ico)으로 변환한다.

PyInstaller의 --icon과 Inno Setup의 SetupIconFile은 .ico만 받으므로
빌드 전에 이 스크립트를 한 번 실행해야 한다.

    py -m pip install pillow
    py tools\\make_icon.py
"""

import sys
from pathlib import Path

from PIL import Image


# 영문 Windows는 출력 인코딩이 cp1252라 한글을 출력하면 UnicodeEncodeError가 난다.
# 오류 메시지는 stderr로 나가므로 양쪽 모두 UTF-8로 바꾸고,
# 그래도 표현이 안 되는 문자는 죽는 대신 대체하도록 한다.
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

# Windows가 상황별로 골라 쓰는 크기들을 하나의 .ico에 모두 담는다.
ICON_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "orca.png"
TARGET = ROOT / "orca.ico"


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"원본 이미지를 찾을 수 없습니다: {SOURCE}")

    image = Image.open(SOURCE).convert("RGBA")
    image.save(TARGET, format="ICO", sizes=ICON_SIZES)

    print(f"생성 완료: {TARGET}")


if __name__ == "__main__":
    main()
