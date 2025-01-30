#!/usr/bin/env python3

import os
import logging
import stat
import shutil
import configparser
from pathlib import Path
from configgen.generators.Generator import Generator
from configgen.utils.logger import setup_logging
import configgen.controller as controller
from configgen.Command import Command
import configgen.batoceraPaths as batoceraPaths

logger = logging.getLogger(__name__)

class YuzuMainlineGenerator(Generator):
    """
    Generator for configuring and launching the Yuzu Mainline emulator.
    """

    def generate(self, system, rom, players_controllers, game_resolution):
        """
        Generate the command to launch Yuzu Mainline.
        """
        logger.info("Generating Yuzu Mainline command...")
        self.ensure_executables_exist()
        self.setup_environment()
        self.setup_directories()

        yuzu_config = Path(batoceraPaths.CONFIGS) / "yuzu/qt-config.ini"
        backup_config = Path(batoceraPaths.CONFIGS) / "yuzu/before-qt-config.ini"

        self.write_yuzu_config(yuzu_config, backup_config, system, players_controllers)

        emulator = system.config.get('emulator', 'yuzu-mainline')
        app_image = "/userdata/system/switch/yuzuEA.AppImage" if emulator == 'yuzu-early-access' else "/userdata/system/switch/yuzu.AppImage"

        command_array = [app_image, "-f", "-g", rom]
        environment_vars = {
            "QT_QPA_PLATFORM": "xcb",
            "SDL_GAMECONTROLLERCONFIG": controller.generate_sdl_game_controller_config(players_controllers)
        }

        return Command(array=command_array, env=environment_vars)

    def ensure_executables_exist(self):
        """
        Ensure that the Yuzu AppImage files are executable.
        """
        for app_image in ["/userdata/system/switch/yuzu.AppImage", "/userdata/system/switch/yuzuEA.AppImage"]:
            if os.path.exists(app_image):
                st = os.stat(app_image)
                os.chmod(app_image, st.st_mode | stat.S_IEXEC)
                logger.debug(f"Ensured executable permissions for {app_image}")

    def setup_environment(self):
        """
        Ensure necessary libraries and symbolic links exist.
        """
        libthai_path = "/lib/libthai.so.0.3.1"
        if not os.path.exists(libthai_path):
            shutil.copy("/userdata/system/switch/extra/libthai.so.0.3.1", libthai_path)
            logger.debug(f"Copied libthai to {libthai_path}")

        symlink_path = "/lib/libthai.so.0"
        if not os.path.exists(symlink_path):
            os.symlink(libthai_path, symlink_path)
            logger.debug(f"Created symlink {symlink_path} -> {libthai_path}")

    def setup_directories(self):
        """
        Create necessary directories and setup symbolic links.
        """
        directories = [
            (Path(batoceraPaths.CONFIGS) / "yuzu", False),
            (Path(batoceraPaths.CONFIGS) / "yuzu/keys", False),
            (Path(batoceraPaths.SAVES) / "yuzu", False),
            (Path("/userdata/system/.local/share"), True),
            (Path("/userdata/system/.config"), True),
            (Path("/userdata/system/.cache/yuzu"), True)
        ]

        for directory, is_symlink in directories:
            if is_symlink and directory.exists() and not directory.is_symlink():
                shutil.rmtree(directory)
            if not directory.exists():
                if is_symlink:
                    os.symlink(Path(batoceraPaths.CONFIGS) / "yuzu", directory)
                else:
                    directory.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory or symlink: {directory}")

    @staticmethod
    def write_yuzu_config(yuzu_config_file, backup_config_file, system, players_controllers):
        """
        Write the Yuzu configuration file.
        """
        logger.info("Writing Yuzu configuration...")
        yuzu_config = configparser.ConfigParser()
        yuzu_config.optionxform = str

        if os.path.exists(yuzu_config_file):
            yuzu_config.read(yuzu_config_file)

        # UI section
        if not yuzu_config.has_section("UI"):
            yuzu_config.add_section("UI")
        yuzu_config["UI"].update({
            "fullscreen": "true",
            "fullscreen\\default": "false",
            "confirmClose": "false",
            "confirmClose\\default": "false",
            "firstStart": "false",
            "firstStart\\default": "false",
            "displayTitleBars": "false",
            "displayTitleBars\\default": "false",
            "hideInactiveMouse": "true",
            "hideInactiveMouse\\default": "true"
        })

        # Add more sections and options as needed, following the same pattern...

        with open(yuzu_config_file, 'w') as configfile:
            yuzu_config.write(configfile)
        logger.debug("Yuzu configuration written successfully.")

    def getHotkeysContext(self):
        """
        Returns the hotkey context for the Yuzu emulator.
        """
        return {
            "name": "yuzu",  # Required to prevent KeyError
            "keys": {  # This must be included to match expected structure
                "exit_emulator": "Escape",
                "pause": "P",
                "save_state": "F5",
                "load_state": "F7",
                "screenshot": "F12"
            }
        }



# Entry point for script execution
if __name__ == "__main__":
    setup_logging()
    logger.info("Yuzu Mainline Generator script started.")
