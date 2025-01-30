from __future__ import annotations

from pathlib import Path
from typing import Final

from configgen.batoceraPaths import BIOS, CONFIGS, ROMS, SAVES

YUZU_CONFIG: Final = CONFIGS / "yuzu"
YUZU_ROMDIR: Final = ROMS / "switch"
YUZU_SAVES:  Final = SAVES / 'switch' / 'yuzu'
YUZU_KEYS: Final = BIOS / 'switch'
YUZU_FIRMWARE: Final = BIOS / 'switch' / 'firmware'
YUZU_APPIMAGE: Final = Path('/userdata/system/switch/yuzu.AppImage')
YUZU_EA_APPIMAGE: Final = Path('/userdata/system/switch/yuzuEA.AppImage')