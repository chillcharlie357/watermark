import argparse
import os
import sys
import subprocess
import shutil


def build_pyinstaller_cmd(
    target: str,
    name: str,
    onefile: bool,
    windowed: bool,
    clean: bool,
    noconfirm: bool,
    icon: str | None,
    collect: list[str],
    use_spec: bool,
    spec_file: str | None,
):
    if use_spec:
        sp = spec_file or "WatermarkTool.spec"
        return ["pyinstaller", sp]

    cmd = ["pyinstaller"]
    if noconfirm:
        cmd.append("--noconfirm")
    if clean:
        cmd.append("--clean")
    if windowed:
        cmd.append("--windowed")
    if onefile:
        cmd.append("--onefile")
    if name:
        cmd.extend(["--name", name])
    if icon:
        cmd.extend(["--icon", icon])
    for pkg in collect:
        cmd.extend(["--collect-all", pkg])
    cmd.append(target)
    return cmd


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pack GUI app with PyInstaller via uv")
    parser.add_argument("target", nargs="?", default="gui_entry.py", help="Entry script (default: gui_entry.py)")
    parser.add_argument("--name", default="WatermarkTool", help="Executable name")
    parser.add_argument("--onefile", action="store_true", help="Pack into single executable")
    parser.add_argument("--no-windowed", action="store_true", help="Show console window")
    parser.add_argument("--no-clean", action="store_true", help="Skip cleaning build cache")
    parser.add_argument("--no-noconfirm", action="store_true", help="Ask before overwriting output")
    parser.add_argument("--icon", default=None, help="Icon file path (.ico/.icns)")
    parser.add_argument("--collect", action="append", default=["PyQt6"], help="Package to collect resources from (repeatable)")
    parser.add_argument("--use-spec", action="store_true", help="Use existing .spec file (default WatermarkTool.spec)")
    parser.add_argument("--spec", default=None, help="Path to .spec file")

    args = parser.parse_args(argv)

    # Check uv availability
    if shutil.which("uv") is None:
        print("Error: uv is not installed or not in PATH.")
        print("Install from https://github.com/astral-sh/uv and try again.")
        return 1

    # Ensure dev dependencies are available
    sync_cmd = ["uv", "sync", "--group", "dev"]
    print("->", " ".join(sync_cmd))
    res = subprocess.run(sync_cmd, cwd=os.getcwd())
    if res.returncode != 0:
        print("uv sync failed")
        return res.returncode

    # Build pyinstaller command (executed via uv run)
    py_cmd = build_pyinstaller_cmd(
        target=args.target,
        name=args.name,
        onefile=args.onefile,
        windowed=not args.no_windowed,
        clean=not args.no_clean,
        noconfirm=not args.no_noconfirm,
        icon=args.icon,
        collect=args.collect,
        use_spec=args.use_spec,
        spec_file=args.spec,
    )

    full_cmd = ["uv", "run", "--group", "dev", *py_cmd]
    print("->", " ".join(full_cmd))
    res2 = subprocess.run(full_cmd, cwd=os.getcwd())
    if res2.returncode != 0:
        print("PyInstaller build failed")
    else:
        print("Build finished. Check the dist/ directory.")
    return res2.returncode


if __name__ == "__main__":
    raise SystemExit(main())