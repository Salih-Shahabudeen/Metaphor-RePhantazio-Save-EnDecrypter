# Metaphor Save Header Patcher (Game Pass ⇄ Steam)

This tool patches the **first 16 bytes** of a save file so it is accepted by the target platform.  
It does **not** decrypt/encrypt save contents; it only swaps a small header block.

---

## Modes (what each mode does)

### Mode 1 — **Game Pass → Steam** (`gp_to_steam`)
- **Input:** a Game Pass WGS payload file (the large hex-named file you extracted)
- **Header source:** Steam `saveXXXX.sav` for the slot you choose
- **Action:** copies the **first 16 bytes** from Steam’s slot save onto the Game Pass payload
- **Output:** patched `saveXXXX.sav` written **next to the Game Pass input file**
- **Optional:** can also overwrite Steam’s `saveXXXX.sav` after making a `.bak` backup

### Mode 2 — **Steam → Game Pass** (`steam_to_gp`)
- **NOTE:** This path hasn't been tested as much as GP to steam so more unstable
- **Input:** a Steam `saveXXXX.sav`
- **Header source:** a Game Pass WGS payload file you provide (header donor)
- **Action:** copies the **first 16 bytes** from the Game Pass header source onto the Steam save
- **Output:** patched `saveXXXX.sav` written **next to the Steam input file**
- **Note:** does **not** auto-reinject into WGS; you manually replace the target WGS payload

---

## Slot numbering (0–15)
Slot number maps to filenames:
- Slot 0  → `save0000.sav`
- Slot 1  → `save0001.sav`
- …
- Slot 15 → `save0015.sav`

---

## Requirements
- Create at least one save on **Steam** first (so Steam slot files exist).
- For **Game Pass**, you need the extracted **WGS payload** (big hex-named file inside a WGS container folder).

---

## How to run

### Option A (recommended): Run the EXE by Drag & Drop
1) Drag your input file onto `metaphor_gp_to_steam.exe` (Found in Releases)
2) Follow prompts:
   - Select mode (1 or 2)
   - Select slot (0–15)
   - If Mode 2, paste the Game Pass header source path when asked
3) The patched output file is written **in the same folder as the file you dragged in**.

### Option B: Run the EXE from command line
PowerShell (same works in CMD with minor quoting changes):
```powershell

.\metaphor_gp_to_steam.exe "C:\path\to\input_file"
