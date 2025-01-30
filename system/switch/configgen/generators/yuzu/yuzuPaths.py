from __future__ import annotations

from pathlib import Path
from typing import Final

from configgen.batoceraPaths import BIOS, CONFIGS, ROMS, SAVES

YUZU_CONFIG: Final = CONFIGS / "yuzu"
YUZU_ROMDIR: Final = ROMS / "switch"
YUZU_SAVES:  Final = SAVES / 'switch'
YUZU_KEYS: Final = BIOS / 'switch'
YUZU_FIRMWARE: Final = BIOS / 'switch' / 'firmware'
YUZU_DATA_DIR: Final = Path('/userdata/system/switch/yuzu.AppImage')
YUZU_EA_DATA_DIR: Final = Path('/userdata/system/switch/yuzuEA.AppImage')
CEMU_CONTROLLER_PROFILES: Final = CONFIGS / 'yuzu' / 'controllerProfiles'