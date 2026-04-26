# build.py — creates Waqt.exe
# Run: python build.py

import subprocess, sys, os

def build():
    # Check pyinstaller
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "Waqt",
        "--add-data", f"core{os.pathsep}core",
        "--add-data", f"ui{os.pathsep}ui",
        "--add-data", f"assets{os.pathsep}assets",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PyQt6.QtWidgets",
        "--hidden-import", "PyQt6.QtSvg",
        "--hidden-import", "requests",
        "--hidden-import", "PIL",
        "--collect-all", "PyQt6",
        "main.py"
    ]

    # Add icon if exists
    for ico in ["assets/icon.ico", "assets/icons/app_icon.png"]:
        if os.path.exists(ico):
            cmd += ["--icon", ico]
            break

    print("Building Waqt.exe...")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n✓ Done! → dist/Waqt.exe")
        print("Send this file to friends — no Python needed!")
    else:
        print("\n✗ Failed. Run this first:")
        print("  pip install pyinstaller Pillow")

if __name__ == "__main__":
    build()