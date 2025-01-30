#!/usr/bin/env python3

# New
from __future__ import annotations

from configgen.utils.logger import setup_logging
import configparser
import shutil
import stat

import codecs
import logging
import os
import subprocess
from os import environ
from pathlib import Path
from typing import TYPE_CHECKING


from configgen.Command import Command
from configgen.batoceraPaths import CACHE, CONFIGS, SAVES, mkdir_if_not_exists

from configgen.controller import generate_sdl_game_controller_config
from configgen.utils import vulkan
from ..Generator import Generator


# TODO
# Remove whichever line below doesn't work
from ...sdl2.sdlgfx import ellipseColor
# from system.switch.configgen.sdl2.sdlgfx import ellipseColor


from . import yuzuControllers
from .yuzuPaths import YUZU_CONFIG, YUZU_FIRMWARE, YUZU_KEYS, YUZU_ROMDIR, YUZU_SAVES, YUZU_APPIMAGE, YUZU_EA_APPIMAGE

if TYPE_CHECKING:
    from configgen.Emulator import Emulator
    from configgen.types import HotkeysContext

eslog = logging.getLogger(__name__)


class YuzuGenerator(Generator):
    def getHotkeysContext(self) -> HotkeysContext:
        return {
            "name": "yuzu",
            "keys": {"exit": ["KEY_LEFTALT", "KEY_F4"]}
        }

    # disable hud & bezels for now - causes game issues
    # TODO
    # Test if the same is true for Yuzu
    def hasInternalMangoHUDCall(self):
        return True

    def generate(self, system, rom, players_controllers, game_resolution):
        rom_path = Path(rom)

        # in case of squashfs, the root directory is passed
        paths = list(rom_path.glob('**/code/*.rpx'))
        if len(paths) >= 1:
            rom_path = paths[0]

        # Create the settings file
        YuzuGenerator.YuzuConfig(YUZU_CONFIG / "qt-config.ini", system)

        # Set-up the controllers
        yuzuControllers.generateControllerConfig(system, playersControllers, YUZU_CONFIG / "qt-config.ini")

        # Set executable to launch from ES emulator config
        if emulator == 'yuzu-early-access':
            app_image = YUZU_EA_APPIMAGE
        else:
            app_image = YUZU_APPIMAGE

        # Set command to run
        commandArray = [app_image, "-f", "-g", rom_path]

        # Set Environment Variables
        # IMPORTANT
        # CONFIGURATIONS AND UPDATES/DLC INSTALLED TO NAND
        # WILL NOT BE USED IF THIS ISN'T SET
        environment_variables = {
            "QT_QPA_PLATFORM": "xcb",
            # "XDG_CONFIG_HOME": f"{CONFIGS}",
            # "XDG_DATA_HOME": f"{CONFIGS}",
            "XDG_CACHE_HOME": f"{CACHE}",
            "QT_QPA_PLATFORM": "xcb",
            "SDL_GAMECONTROLLERCONFIG": generate_sdl_game_controller_config(players_controllers)
        }

        return Command.Command(array=commandArray, env=environment_variables)

    @staticmethod
    def YuzuConfig(yuzu_config_file, system, players_controllers):
        # Write the Yuzu configuration file.

        eslog.info("Writing Yuzu configuration...")

        yuzu_config = configparser.RawConfigParser()
        yuzu_config.optionxform = str

        if os.path.exists(yuzu_config_file):
            yuzu_config.read(yuzu_config_file)

        if system.isOptSet('yuzu_enable_discord_presence'):
            yuzu_config.set("UI", "enable_discord_presence",
                           system.config["yuzu_enable_discord_presence"])
        else:
            yuzu_config.set("UI", "enable_discord_presence", "false")

        yuzu_config.set("UI", "enable_discord_presence\\default", "false")

        yuzu_config.set("UI", "calloutFlags", "1")
        yuzu_config.set("UI", "calloutFlags\\default", "false")

        # Single Window Mode
        if system.isOptSet('single_window'):
            yuzu_config.set("UI", "singleWindowMode",
                           system.config["single_window"])
            yuzu_config.set("UI", "singleWindowMode\\default", "false")
        else:
            yuzu_config.set("UI", "singleWindowMode", "true")
            yuzu_config.set("UI", "singleWindowMode\\default", "true")

        # User Profile select on boot
        if system.isOptSet('user_profile'):
            yuzu_config.set("UI", "select_user_on_boot",
                           system.config["user_profile"])
            yuzu_config.set("UI", "select_user_on_boot\\default", "false")
        else:
            yuzu_config.set("UI", "select_user_on_boot", "true")
            yuzu_config.set("UI", "select_user_on_boot\\default", "true")

        yuzu_config.set("UI", "hideInactiveMouse", "true")
        yuzu_config.set("UI", "hideInactiveMouse\\default", "true")
        
        # Roms path (need for load update/dlc)
        yuzu_config.set("UI", "Paths\\gamedirs\\1\\deep_scan", "true")
        yuzu_config.set("UI", "Paths\\gamedirs\\1\\deep_scan\\default", "false")
        yuzu_config.set("UI", "Paths\\gamedirs\\1\\expanded", "true")
        yuzu_config.set("UI", "Paths\\gamedirs\\1\\expanded\\default", "true")
        yuzu_config.set("UI", "Paths\\gamedirs\\1\\path", YUZU_ROMDIR)
        yuzu_config.set("UI", "Paths\\gamedirs\\size", "1")

        yuzu_config.set("UI", "Screenshots\\enable_screenshot_save_as", "true")
        yuzu_config.set("UI", "Screenshots\\enable_screenshot_save_as\\default", "true")
        yuzu_config.set("UI", "Screenshots\\screenshot_path", "/userdata/screenshots")
        yuzu_config.set("UI", "Screenshots\\screenshot_path\\default", "false")

        yuzu_config.set("UI", "Shortcuts\Main%20Window\Exit%20yuzu\Controller_KeySeq", "Home+Plus")
        yuzu_config.set("UI", "Shortcuts\Main%20Window\Exit%20yuzu\Controller_KeySeq\\default", "false")
        
        # Data Storage section
        if not yuzu_config.has_section("Data%20Storage"):
            yuzu_config.add_section("Data%20Storage")
        yuzu_config.set("Data%20Storage", "dump_directory", YUZU_CONFIG /"dump")
        yuzu_config.set("Data%20Storage", "dump_directory\\default", "true")

        yuzu_config.set("Data%20Storage", "load_directory", YUZU_CONFIG /"load")
        yuzu_config.set("Data%20Storage", "load_directory\\default", "true")

        yuzu_config.set("Data%20Storage", "nand_directory", YUZU_CONFIG /"nand")
        yuzu_config.set("Data%20Storage", "nand_directory\\default", "true")

        yuzu_config.set("Data%20Storage", "sdmc_directory", YUZU_CONFIG /"sdmc")
        yuzu_config.set("Data%20Storage", "sdmc_directory\\default", "true")

        yuzu_config.set("Data%20Storage", "tas_directory", YUZU_CONFIG /"tas")
        yuzu_config.set("Data%20Storage", "tas_directory\\default", "true")

        yuzu_config.set("Data%20Storage", "use_virtual_sd", "true")
        yuzu_config.set("Data%20Storage", "use_virtual_sd\\default", "true")
        
        # Core section
        if not yuzu_config.has_section("Core"):
            yuzu_config.add_section("Core")

        # Multicore
        if system.isOptSet('multicore'):
            yuzu_config.set("Core", "use_multi_core", system.config["multicore"])
            yuzu_config.set("Core", "use_multi_core\\default", "false")
        else:
            yuzu_config.set("Core", "use_multi_core", "true")
            yuzu_config.set("Core", "use_multi_core\\default", "true")
        
        # Renderer section
        if not yuzu_config.has_section("Renderer"):
            yuzu_config.add_section("Renderer")

        # Aspect ratio
        if system.isOptSet('yuzu_ratio'):
            yuzu_config.set("Renderer", "aspect_ratio", system.config["yuzu_ratio"])
            yuzu_config.set("Renderer", "aspect_ratio\\default", "false")
        else:
            yuzu_config.set("Renderer", "aspect_ratio", "0")
            yuzu_config.set("Renderer", "aspect_ratio\\default", "true")

        # Graphical backend
        if system.isOptSet('yuzu_backend'):
            yuzu_config.set("Renderer", "backend", system.config["yuzu_backend"])
        else:
            yuzu_config.set("Renderer", "backend", "0")
        yuzu_config.set("Renderer", "backend\\default", "false")

        # Async Shader compilation
        if system.isOptSet('async_shaders'):
            yuzu_config.set("Renderer", "use_asynchronous_shaders", system.config["async_shaders"])
        else:
            yuzu_config.set("Renderer", "use_asynchronous_shaders", "true")
        yuzu_config.set("Renderer", "use_asynchronous_shaders\\default", "false")

        # Assembly shaders
        if system.isOptSet('shaderbackend'):
            yuzu_config.set("Renderer", "shader_backend", system.config["shaderbackend"])
            yuzu_config.set("Renderer", "shader_backend\\default", "false")
        else:
            yuzu_config.set("Renderer", "shader_backend", "0")
            yuzu_config.set("Renderer", "shader_backend\\default", "true")

        # Async Gpu Emulation
        if system.isOptSet('async_gpu'):
            yuzu_config.set("Renderer", "use_asynchronous_gpu_emulation", system.config["async_gpu"])
            yuzu_config.set("Renderer", "use_asynchronous_gpu_emulation\\default", "false")
        else:
            yuzu_config.set("Renderer", "use_asynchronous_gpu_emulation", "true")
            yuzu_config.set("Renderer", "use_asynchronous_gpu_emulation\\default", "true")

        # NVDEC Emulation
        if system.isOptSet('nvdec_emu'):
            yuzu_config.set("Renderer", "nvdec_emulation", system.config["nvdec_emu"])
            yuzu_config.set("Renderer", "nvdec_emulation\\default", "false")
        else:
            yuzu_config.set("Renderer", "nvdec_emulation", "2")
            yuzu_config.set("Renderer", "nvdec_emulation\\default", "true")

        # Gpu Accuracy
        if system.isOptSet('gpuaccuracy'):
            yuzu_config.set("Renderer", "gpu_accuracy", system.config["gpuaccuracy"])
        else:
            yuzu_config.set("Renderer", "gpu_accuracy", "0")
        yuzu_config.set("Renderer", "gpu_accuracy\\default", "false")

        # Vsync
        if system.isOptSet('vsync'):
            yuzu_config.set("Renderer", "use_vsync", system.config["vsync"])
            yuzu_config.set("Renderer", "use_vsync\\default", "false")
            if system.config["vsync"] == "2":
                yuzu_config.set("Renderer", "use_vsync\\default", "true")
        else:
            yuzu_config.set("Renderer", "use_vsync", "1")
            yuzu_config.set("Renderer", "use_vsync\\default", "false")

        # Gpu cache garbage collection
        if system.isOptSet('gpu_cache_gc'):
            yuzu_config.set("Renderer", "use_caches_gc", system.config["gpu_cache_gc"])
        else:
            yuzu_config.set("Renderer", "use_caches_gc", "false")
        yuzu_config.set("Renderer", "use_caches_gc\\default", "false")

        # Max anisotropy
        if system.isOptSet('anisotropy'):
            yuzu_config.set("Renderer", "max_anisotropy", system.config["anisotropy"])
            yuzu_config.set("Renderer", "max_anisotropy\\default", "false")
        else:
            yuzu_config.set("Renderer", "max_anisotropy", "0")
            yuzu_config.set("Renderer", "max_anisotropy\\default", "true")

        # Resolution scaler
        if system.isOptSet('resolution_scale'):
            yuzu_config.set("Renderer", "resolution_setup", system.config["resolution_scale"])
            yuzu_config.set("Renderer", "resolution_setup\\default", "false")
        else:
            yuzu_config.set("Renderer", "resolution_setup", "2")
            yuzu_config.set("Renderer", "resolution_setup\\default", "true")

        # Scaling filter
        if system.isOptSet('scale_filter'):
            yuzu_config.set("Renderer", "scaling_filter", system.config["scale_filter"])
            yuzu_config.set("Renderer", "scaling_filter\\default", "false")
        else:
            yuzu_config.set("Renderer", "scaling_filter", "1")
            yuzu_config.set("Renderer", "scaling_filter\\default", "true")

        # Anti aliasing method
        if system.isOptSet('aliasing_method'):
            yuzu_config.set("Renderer", "anti_aliasing", system.config["aliasing_method"])
            yuzu_config.set("Renderer", "anti_aliasing\\default", "false")
        else:
            yuzu_config.set("Renderer", "anti_aliasing", "0")
            yuzu_config.set("Renderer", "anti_aliasing\\default", "true")

        #ASTC Decoding Method
        if system.isOptSet('accelerate_astc'):
            yuzu_config.set("Renderer", "accelerate_astc", system.config["accelerate_astc"])
            yuzu_config.set("Renderer", "accelerate_astc\\default", "false")
        else:
            yuzu_config.set("Renderer", "accelerate_astc", "1")
            yuzu_config.set("Renderer", "accelerate_astc\\default", "true")            

        # ASTC Texture Recompression
        if system.isOptSet('astc_recompression'):


            yuzu_config.set("Renderer", "astc_recompression", system.config["astc_recompression"])
            yuzu_config.set("Renderer", "astc_recompression\\default", "false")
            if system.config["astc_recompression"] == "0":
                yuzu_config.set("Renderer", "use_vsync\\default", "true")
            yuzu_config.set("Renderer", "async_astc", "false")
            yuzu_config.set("Renderer", "async_astc\\default", "true")
        else:
            yuzu_config.set("Renderer", "astc_recompression", "0")
            yuzu_config.set("Renderer", "astc_recompression\\default", "true")
            yuzu_config.set("Renderer", "async_astc", "false")
            yuzu_config.set("Renderer", "async_astc\\default", "true")

        # Cpu Section
        if not yuzu_config.has_section("Cpu"):
            yuzu_config.add_section("Cpu")

        # Cpu Accuracy
        if system.isOptSet('cpuaccuracy'):
            yuzu_config.set("Cpu", "cpu_accuracy", system.config["cpuaccuracy"])
            yuzu_config.set("Cpu", "cpu_accuracy\\default", "false")
        else:
            yuzu_config.set("Cpu", "cpu_accuracy", "0")
            yuzu_config.set("Cpu", "cpu_accuracy\\default", "true")

        # System section
        if not yuzu_config.has_section("System"):
            yuzu_config.add_section("System")

        # Language
        if system.isOptSet('language'):
            yuzu_config.set("System", "language_index", system.config["language"])
            yuzu_config.set("System", "language_index\\default", "false")
        else:
            yuzu_config.set("System", "language_index", "1")
            yuzu_config.set("System", "language_index\\default", "true")

        # Audio Mode
        if system.isOptSet('audio_mode'):
            yuzu_config.set("System", "sound_index", system.config["audio_mode"])
            yuzu_config.set("System", "sound_index\\default", "false")
        else:
            yuzu_config.set("System", "sound_index", "1")
            yuzu_config.set("System", "sound_index\\default", "true")

        # Region
        if system.isOptSet('region'):
            yuzu_config.set("System", "region_index", system.config["region"])
            yuzu_config.set("System", "region_index\\default", "false")
        else:
            yuzu_config.set("System", "region_index", "1")
            yuzu_config.set("System", "region_index\\default", "true")
            
        # Dock Mode
        if system.isOptSet('dock_mode'):
            if system.config["dock_mode"] == "1":
                yuzu_config.set("System", "use_docked_mode", "1")
                yuzu_config.set("System", "use_docked_mode\\default", "true")
            elif system.config["dock_mode"] == "0":
                yuzu_config.set("System", "use_docked_mode", "0")
                yuzu_config.set("System", "use_docked_mode\\default", "false")
        else:
            yuzu_config.set("System", "use_docked_mode", "1")
            yuzu_config.set("System", "use_docked_mode\\default", "true")
    
        
        # telemetry section
        if not yuzu_config.has_section("WebService"):
            yuzu_config.add_section("WebService") 
        yuzu_config.set("WebService", "enable_telemetry", "false")
        yuzu_config.set("WebService", "enable_telemetry\\default", "false") 
        
        
    # Services section
        if not yuzu_config.has_section("Services"):
            yuzu_config.add_section("Services")
        yuzu_config.set("Services", "bcat_backend", "none")
        yuzu_config.set("Services", "bcat_backend\\default", "none") 

        ### update the configuration file
        if not os.path.exists(os.path.dirname(yuzu_configFile)):
            os.makedirs(os.path.dirname(yuzu_configFile))
        with open(yuzu_configFile, 'w') as configfile:
            yuzu_config.write(configfile)


    def setup_directories():
        mkdir_if_not_exists(YUZU_CONFIG)
        # TODO
        # Figure out yuzu save handling and make symlink to YUZU_SAVES dir
        # mkdir_if_not_exists(YUZU_SAVES)
