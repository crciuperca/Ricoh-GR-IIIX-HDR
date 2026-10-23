# Ricoh GR IIIx HDR

An offline patcher for **Ricoh GR IIIx firmware 1.60**. It reproduces the current experimental custom firmware from your original firmware file.

## Features

- **RAW+JPG HDR** with a full-resolution gain map, in sRGB or Display P3.
- **Display P3** color conversion and embedded ICC profile.
- **Natural / Natural+ / Natural++** calibrated profiles, with progressively deeper shadows.
- **Provia / Provia+ / Provia++** profiles fitted to a photographed Fujifilm XE5 Provia reference.
- **IR / Green / UV** RGB contrast effects. These do not capture physical infrared or ultraviolet light.
- Custom **P3/HDR and profile icons**, with the original camera looks retained.

HDR is generated from the processed image; it does not recover clipped RAW highlights. RAW remains on its native path. Full-resolution HDR can take longer to save; use single shots and wait for processing to finish. These are experimental profiles and firmware.

Profile icons: Natural `Nat`, Natural+ `Nat+`, Natural++ `Na++`; Provia `Prov`, Provia+ `Pro+`, Provia++ `Pr++`; IR `IR`, Green `Grn`, UV `UV`. Shared native mappings cover the quick menu, main Image Control menu, selected-profile summary, live view and playback details.

![Custom profile icons: Nat, Nat+, Na++, IR, Grn, UV, Prov, Pro+, Pr++](profile-icons-preview.png)

Color space and format icons:

![P3 and HDR icons](p3-hdr-icons-preview.png)

## Camera usage notes

- After switching the camera on, wait a few seconds for the custom icons to update.
- Saved **Format Type** and **Color Space** selections sometimes do not persist after a reboot. Check both settings after startup and reselect your preferred values if needed.

## Samples

Click an image to open the sample.

| Standard | Standard HDR (SDR preview) |
| --- | --- |
| [![Standard](samples/original1.jpg)](samples/original1.jpg) | [![Standard HDR](samples/std-hdr.jpg)](samples/std-hdr.jpg) |

| Natural | Provia |
| --- | --- |
| [![Natural](samples/natural.jpg)](samples/natural.jpg) | [![Provia](samples/provia.jpg)](samples/provia.jpg) |
| **Natural+** | **Provia+** |
| [![Natural+](samples/natural-plus.jpg)](samples/natural-plus.jpg) | [![Provia+](samples/provia-plus.jpg)](samples/provia-plus.jpg) |
| **Natural++** | **Provia++** |
| [![Natural++](samples/natural-plus-plus.jpg)](samples/natural-plus-plus.jpg) | [![Provia++](samples/provia-plus-plus.jpg)](samples/provia-plus-plus.jpg) |

### IR

[![IR](samples/ir.jpg)](samples/ir.jpg)

## Requirements

- **Python 3.8+**, available on PATH. No extra Python packages, compiler, or network access required.
- The **original Ricoh GR IIIx 1.60 firmware `.bin`**. Other models, firmware versions, and already-patched files are rejected.
- Windows uses PowerShell for the `.bat` launcher. Linux/macOS use `sh`.

Keep the scripts and the `native-cfw` folder together. The original firmware is not included or downloaded.

## Run

From this directory, choose one launcher:

**Windows:**

```powershell
.\patch-cfw.bat "C:\Downloads\fwdc243b.bin"
# Or:
.\patch-cfw.ps1 "C:\Downloads\fwdc243b.bin"
```

If PowerShell blocks local scripts:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\patch-cfw.ps1 "C:\Downloads\fwdc243b.bin"
```

**Linux / macOS / WSL / Git Bash:**

```sh
sh ./patch-cfw.sh /path/to/original/fwdc243b.bin
```

By default, output is **`custom-firmware/fwdc243b.bin` beside the input file**. To choose another output file:

```powershell
.\patch-cfw.bat "C:\Downloads\fwdc243b.bin" -o "C:\Output\fwdc243b.bin"
```

```sh
sh ./patch-cfw.sh /path/to/original.bin -o /path/to/output/fwdc243b.bin
```

Every launcher accepts `--info` for version details and `-h` for help. Set `PYTHON` to a Python executable path if needed.

## Output and verification

All launchers apply the same version-specific binary delta and produce identical firmware. The input is preserved, existing output files are refused, and the complete input/output SHA-256 hashes are checked. Nothing is automatically flashed or copied to an SD card.

- Stock GR IIIx 1.60 SHA-256: `708e79f3b7b96a7e1581b4acf4c412233050a1832718ef7f06c8397db1b431c7`
- Current CFW SHA-256: `6415d116b0bd6ac95fc538c08d8abbbb860832d3b176b9587b8326ff06341878`
- Build: `native-cfw-profile-icons-2`

The delta is fixed to this build. It does not compile or update the firmware features when run. `native-cfw/make_patch.py` and `native-cfw/test_patcher.py` are developer utilities for generating and testing a pinned delta; applying it only needs the launchers, `patch.py`, and the patch package. See `native-cfw/THIRD_PARTY.txt` for attribution.
