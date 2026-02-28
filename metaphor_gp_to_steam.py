import os
import sys
import shutil
from pathlib import Path

STEAM_REL = Path("SEGA") / "METAPHOR" / "Steam"
PATCH_N = 16  # patch first N bytes

def die(msg: str, code: int = 1):
    print(f"[ERROR] {msg}")
    input("Press Enter to exit...")
    sys.exit(code)

def ask_int(prompt: str, lo: int, hi: int) -> int:
    while True:
        s = input(prompt).strip()
        try:
            v = int(s)
            if lo <= v <= hi:
                return v
        except ValueError:
            pass
        print(f"Enter a number from {lo} to {hi}.")

def ask_choice(prompt: str, choices: dict):
    # choices: {"1": ("Label", value), ...}
    while True:
        print(prompt)
        for k, (label, _) in choices.items():
            print(f"  {k}) {label}")
        s = input("> ").strip()
        if s in choices:
            return choices[s][1]
        print("Invalid selection.")

def ask_yes_no(prompt: str, default_yes: bool = False) -> bool:
    suffix = " [Y/n]" if default_yes else " [y/N]"
    while True:
        s = input(prompt + suffix + " ").strip().lower()
        if not s:
            return default_yes
        if s in ("y", "yes"):
            return True
        if s in ("n", "no"):
            return False
        print("Enter y or n.")

def read_bytes(p: Path) -> bytearray:
    try:
        return bytearray(p.read_bytes())
    except Exception as e:
        die(f"Failed to read: {p}\n{e}")

def write_bytes(p: Path, data: bytes):
    try:
        p.write_bytes(data)
    except Exception as e:
        die(f"Failed to write: {p}\n{e}")

def find_steam_id_dir(appdata: Path) -> Path:
    root = appdata / STEAM_REL
    if not root.exists():
        die(f"Steam save root not found: {root}")

    steam_ids = [p for p in root.iterdir() if p.is_dir() and p.name.isdigit()]
    if not steam_ids:
        die(f"No SteamID folder found under: {root}")

    steam_ids.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return steam_ids[0]

def slot_filename(slot: int) -> str:
    return f"save{slot:04d}.sav"

def unique_out_path(folder: Path, preferred_name: str) -> Path:
    base = folder / preferred_name
    if not base.exists():
        return base
    stem = Path(preferred_name).stem
    suffix = Path(preferred_name).suffix
    i = 1
    while True:
        cand = folder / f"{stem}_patched_{i:03d}{suffix}"
        if not cand.exists():
            return cand
        i += 1

def main():
    # Input file: drag & drop onto exe/script OR pass as argv[1]
    if len(sys.argv) < 2:
        print("Usage: drag a .sav/.payload file onto this EXE/script.")
        input("Press Enter to exit...")
        return

    in_path = Path(sys.argv[1]).expanduser()
    if not in_path.exists() or not in_path.is_file():
        die(f"Input file not found: {in_path}")

    mode = ask_choice(
        "Select conversion mode:",
        {
            "1": ("Game Pass → Steam", "gp_to_steam"),
            "2": ("Steam → Game Pass", "steam_to_gp"),
        },
    )

    slot = ask_int("Select slot (0–15): ", 0, 15)
    slot_file = slot_filename(slot)

    # Common: verify patch size
    in_data = read_bytes(in_path)
    if len(in_data) < PATCH_N:
        die(f"Input file too small (<{PATCH_N} bytes): {in_path}")

    out_dir = in_path.parent

    if mode == "gp_to_steam":
        appdata = Path(os.environ.get("APPDATA", ""))
        if not appdata:
            die("APPDATA env var not set.")

        steam_id_dir = find_steam_id_dir(appdata)
        steam_save = steam_id_dir / slot_file
        steam_bak  = steam_id_dir / (slot_file + ".bak")

        if not steam_save.exists():
            die(f"{slot_file} not found. Create a Steam save in that slot first:\n{steam_save}")

        steam_data = read_bytes(steam_save)
        if len(steam_data) < PATCH_N:
            die(f"Steam save too small (<{PATCH_N} bytes): {steam_save}")

        print(f"Steam dir:  {steam_id_dir}")
        print(f"Steam save: {steam_save} ({len(steam_data)} bytes)")
        print(f"GP input:   {in_path} ({len(in_data)} bytes)")

        # Backup Steam slot once
        if not steam_bak.exists():
            shutil.copy2(steam_save, steam_bak)
            print(f"Backup created: {steam_bak}")
        else:
            print(f"Backup exists:  {steam_bak}")

        # Patch GP payload header using Steam header
        patched = bytearray(in_data)
        patched[:PATCH_N] = steam_data[:PATCH_N]

        # Write patched output next to GP input
        out_path = unique_out_path(out_dir, slot_file)
        write_bytes(out_path, patched)
        print(f"\nWrote patched file next to input: {out_path}")

        # Optional: also install to Steam slot
        if ask_yes_no(f"Also overwrite Steam slot {slot} with patched data?", default_yes=False):
            write_bytes(steam_save, patched)
            print(f"Installed into Steam slot: {steam_save}")
        else:
            print("Did not overwrite Steam slot.")

    else:  # steam_to_gp
        # Need a GP header source file to patch Steam save into GP format
        print("\nSteam → GP requires a GP header source file (any GP save/payload from the same game).")
        print("Paste the path to a GP file to borrow the first bytes from (you can drag & drop into this window).")
        gp_header_path_str = input("GP header source path: ").strip().strip('"')
        gp_header_path = Path(gp_header_path_str).expanduser()

        if not gp_header_path.exists() or not gp_header_path.is_file():
            die(f"GP header source file not found: {gp_header_path}")

        gp_hdr = read_bytes(gp_header_path)
        if len(gp_hdr) < PATCH_N:
            die(f"GP header source too small (<{PATCH_N} bytes): {gp_header_path}")

        print(f"Steam input: {in_path} ({len(in_data)} bytes)")
        print(f"GP header:   {gp_header_path} ({len(gp_hdr)} bytes)")

        # Patch Steam save header using GP header
        patched = bytearray(in_data)
        patched[:PATCH_N] = gp_hdr[:PATCH_N]

        # Write patched output next to Steam input
        out_name = slot_file  # keep canonical name, unique if exists
        out_path = unique_out_path(out_dir, out_name)
        write_bytes(out_path, patched)
        print(f"\nWrote patched file next to input: {out_path}")
        print("You can now place this into your GP save system as needed (manual step).")

    print("\nDone.")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()