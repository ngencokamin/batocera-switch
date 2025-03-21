from __future__ import annotations

from pathlib import Path
from typing import Final

from configgen.batoceraPaths import BIOS, CONFIGS, ROMS, SAVES

RYUJINX_CONFIG: Final = CONFIGS / 'Ryujinx'
RYUJINX_ROMDIR: Final = ROMS / 'switch'
RYUJINX_APPIMAGE: Final = Path('/userdata/system/switch/Ryujinx.AppImage')
RYUJINX_AVALONIA_APPIMAGE: Final = Path('/userdata/system/switch/Ryujinx-Avalonia.AppImage')
RYUJINX_LDN_APPIMAGE: Final = Path('/userdata/system/switch/Ryujinx-LDN.AppImage')

