"""orca.png를 Windows 아이콘(orca.ico)으로 변환한다.

PyInstaller의 --icon과 Inno Setup의 SetupIconFile은 .ico만 받으므로
빌드 전에 이 스크립트를 한 번 실행해야 한다.

    py -m pip install pillow
    py tools\\make_icon.py
"""

from pathlib import Path

from PIL import Image


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
