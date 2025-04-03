#!/usr/bin/env python

from configgen.batoceraPaths import CACHE, CONFIGS, SAVES, mkdir_if_not_exists
import generators
from configgen.generators.Generator import Generator
import Command as Command
import os
import stat
import json
import uuid
import os
import controllersConfig as controllersConfig
from shutil import copyfile
from utils.logger import get_logger
import subprocess

from .ryujinxPaths import RYUJINX_CONFIG, RYUJINX_ROMDIR, RYUJINX_APPIMAGE, RYUJINX_AVALONIA_APPIMAGE, RYUJINX_LDN_APPIMAGE


eslog = get_logger(__name__)

class RyujinxMainlineGenerator(Generator):

    def generate(self, system, rom, playersControllers, gameResolution):
        # Set executaable path by system config choice
        if system.config['emulator'] == 'ryujinx-avalonia':
            executable = RYUJINX_AVALONIA_APPIMAGE
        elif system.config['emulator'] == 'ryujinx-ldn':
            executable = RYUJINX_LDN_APPIMAGE
        else:
            executable = RYUJINX_APPIMAGE
        
        # Check if executable exists
        if os.path.exists(executable):
            # Check if execute permissions are set, adding if not
            st = os.stat(executable)
            if not (st.st_mode & stat.S_IXUSR):
                os.chmod(file_path, st.st_mode | stat.S_IXUSR)
        # Fall back to base Ryujinx if selected system does not exist
        elif os.path.exists(RYUJINX_APPIMAGE):
            eslog.warning(f"Executable for {system.config['emulator']} not found. Falling back to base Ryujinx executable.")
            executable = RYUJINX_APPIMAGE
            st = os.stat(executable)
            if not (st.st_mode & stat.S_IXUSR):
                os.chmod(file_path, st.st_mode | stat.S_IXUSR)
        # Exit if neither specified nor base Ryujinx is found
        else:
            eslog.error(f"Could not find executable for Ryujinx base version or {system.config['emulator']}. Please ensure you have added a Ryujinx AppImage with the correct name.")
            
        # Create config dirs if they don't already exist
        mkdir_if_not_exists(RYUJINX_CONFIG)
        mkdir_if_not_exists(RYUJINX_CONFIG / "System")

        # Check if Ryujinx has been run before by checking for Config Json
        CONFIG_FILE = RYUJINX_CONFIG / "Config.json"
        firstrun = False if os.path.exists(CONFIG_FILE) else True

        #Configuration update
        RyujinxMainlineGenerator.writeRyujinxConfig(RyujinxConfig, system, playersControllers)

        # Open Ryujinx without Rom for firmware install if it's never been opened before, else launch with rom
        if firstrun:  
            commandArray = [str(executable)]
        else:
            commandArray = [str(executable) , rom]
        
        eslog.debug("Controller Config before Playing: {}".format(controllersConfig.generateSdlGameControllerConfig(playersControllers)))
        #, "SDL_GAMECONTROLLERCONFIG": controllersConfig.generateSdlGameControllerConfig(playersControllers)
        return Command.Command(
            array=commandArray,
            env={"XDG_CONFIG_HOME":str(CONFIGS), "XDG_CACHE_HOME":str(CACHE), "QT_QPA_PLATFORM":"xcb", "SDL_GAMECONTROLLERCONFIG": controllersConfig.generateSdlGameControllerConfig(playersControllers)}
            )

    def writeRyujinxConfig(RyujinxConfigFile, system, playersControllers):

        #Get ryujinx version
        if system.config['emulator'] == 'ryujinx-avalonia':
            filename = "/userdata/system/switch/extra/ryujinxavalonia/version.txt"
            os.environ["PYSDL2_DLL_PATH"] = "/userdata/system/switch/extra/ryujinxavalonia/"
        elif system.config['emulator'] == 'ryujinx-ldn':
            filename = "/userdata/system/switch/extra/ryujinxldn/version.txt"
            os.environ["PYSDL2_DLL_PATH"] = "/userdata/system/switch/extra/ryujinxldn/"
        else:
            filename = "/userdata/system/switch/extra/ryujinx/version.txt"
            os.environ["PYSDL2_DLL_PATH"] = "/userdata/system/switch/extra/ryujinx/"
            
        if os.path.exists(filename):
            file = open(filename, 'r')
            ryu_version = int(file.readline())
            file.close()
        else:
            ryu_version = 382
        #import SDL to try and guess controller order

        eslog.debug("Ryujinx Version: {}".format(ryu_version))

        #with open('/userdata/system/switch/configgen/mapping.csv', mode='r', encoding='utf-8-sig') as csv_file:
        #    reader = csv.DictReader(csv_file)
        #    controller_data = list(reader)

        if os.path.exists(RyujinxConfigFile):
            with open(RyujinxConfigFile, "r") as read_file:
                data = json.load(read_file)
        else:
                data = {}

        if system.config['emulator'] == 'ryujinx-avalonia':
            if ryu_version >= 1215:
                data['version'] = 49
            elif ryu_version >= 924:
                data['version'] = 47
            else:
                data['version'] = 42
        else:
            if ryu_version >= 1215:
                data['version'] = 49
            elif ryu_version >= 924:
                data['version'] = 47
            elif ryu_version > 382:
                data['version'] = 42
            else:
                data['version'] = 40
                
        data['enable_file_log'] = bool('true')
        data['backend_threading'] = 'Auto'

        if system.isOptSet('res_scale'):
            data['res_scale'] = int(system.config["res_scale"])
        else:
            data['res_scale'] = 1

        data['res_scale_custom'] = 1

        if system.isOptSet('max_anisotropy'):
            data['max_anisotropy'] = int(system.config["max_anisotropy"])
        else:
            data['max_anisotropy'] = -1 

        if system.isOptSet('aspect_ratio'):
            data['aspect_ratio'] = system.config["aspect_ratio"]
        else:
            data['aspect_ratio'] = 'Fixed16x9'

        data['logging_enable_debug'] = bool(0)
        data['logging_enable_stub'] = bool(0)
        data['logging_enable_info'] = bool(0)
        data['logging_enable_warn'] = bool(0)
        data['logging_enable_error'] = bool(0)
        data['logging_enable_trace'] = bool(0)
        data['logging_enable_guest'] = bool(0)
        data['logging_enable_fs_access_log'] = bool(0)
        data['logging_filtered_classes'] = []
        data['logging_graphics_debug_level'] = 'None'

        if system.isOptSet('system_language'):
            data['system_language'] = system.config["system_language"]
        else:
            data['system_language'] = 'AmericanEnglish'

        if system.isOptSet('system_region'):
            data['system_region'] = system.config["system_region"]
        else:
            data['system_region'] = 'USA'

        data['system_time_zone'] = 'UTC'
        data['system_time_offset'] = 0

        if system.isOptSet('ryu_docked_mode'):
            data['docked_mode'] = bool(int(system.config["ryu_docked_mode"]))
        else:
            data['docked_mode'] = bool('true')

        if system.isOptSet('ryu_enable_discord_integration'):
            data['enable_discord_integration'] = bool(int(system.config["ryu_enable_discord_integration"]))
        else:
            data['enable_discord_integration'] = bool('true')    

        data['check_updates_on_start'] = bool('false')
        data['show_confirm_exit'] = bool(0)
        data['hide_cursor_on_idle'] = bool('true')

        #V-Sync
        if system.isOptSet('ryu_vsync'):
            data['enable_vsync'] = bool(int(system.config["ryu_vsync"]))
        else:
            data['enable_vsync'] = bool('true')    

        #Shader Cache
        if system.isOptSet('ryu_shadercache'):
            data['enable_shader_cache'] = bool(int(system.config["ryu_shadercache"]))
        else:
            data['enable_shader_cache'] = bool('true')    

        #data['enable_texture_recompression'] = bool(0)

        if system.isOptSet('enable_ptc'):
            data['enable_ptc'] = bool(int(system.config["enable_ptc"]))
        else:
            data['enable_ptc'] = bool('true')    


        data['enable_internet_access'] = bool(0)

        #File System Integrity Checks
        if system.isOptSet('enable_fs_integrity_checks'):
            data['enable_fs_integrity_checks'] = bool(int(system.config["enable_fs_integrity_checks"]))
        else:
            data['enable_fs_integrity_checks'] = bool('true')    

        data['fs_global_access_log_mode'] = 0
        data['audio_backend'] = 'SDL2'
        data['audio_volume'] = 1

        if system.isOptSet('memory_manager_mode'):
            data['memory_manager_mode'] = system.config["memory_manager_mode"]
        else:
            data['memory_manager_mode'] = 'HostMappedUnsafe'   

        if system.isOptSet('expand_ram'):
            data['expand_ram'] = bool(int(system.config["expand_ram"]))
        else:
            data['expand_ram'] = bool(0)  

        if system.isOptSet('ignore_missing_services'):
            data['ignore_missing_services'] = bool(int(system.config["ignore_missing_services"]))
        else:
            data['ignore_missing_services'] = bool(0) 

        data['language_code'] = str(getLangFromEnvironment())

        data['enable_custom_theme'] = bool(0)
        data['custom_theme_path'] = ''
        data['base_style'] = 'Dark'
        data['game_list_view_mode'] = 0
        data['show_names'] = bool('true')
        data['grid_size'] = 2
        data['application_sort'] = 0
        data['is_ascending_order'] = bool('true')
        data['start_fullscreen'] = bool('true')
        data['show_console'] = bool('true')
        data['enable_keyboard'] = bool(0)
        data['enable_mouse'] = bool(0)
        data['game_dirs'] = ["/userdata/roms/switch"]
        data['keyboard_config'] = []
        data['controller_config'] = []
        hotkeys = {}
        hotkeys['toggle_vsync'] = "Tab"
        hotkeys['screenshot'] = "F8"
        hotkeys['show_ui'] = "F4" 
        hotkeys['pause'] = "F5"
        hotkeys['toggle_mute'] = "F2"
        hotkeys['res_scale_up'] = "Unbound" 
        hotkeys['res_scale_down'] = "Unbound" 
        data['hotkeys'] = hotkeys  
        gui_columns = {}
        gui_columns['fav_column'] = bool('true')
        gui_columns['icon_column'] = bool('true')
        gui_columns['app_column'] = bool('true')
        gui_columns['dev_column'] = bool('true')
        gui_columns['version_column'] = bool('true')
        gui_columns['time_played_column'] = bool('true')
        gui_columns['last_played_column'] = bool('true')
        gui_columns['file_ext_column'] = bool('true')
        gui_columns['file_size_column'] = bool('true')
        gui_columns['path_column'] = bool('true')
        data['gui_columns'] = gui_columns 
        column_sort = {}
        column_sort['sort_column_id'] = 0
        column_sort['sort_ascending'] = bool(0)         
        data['column_sort'] = column_sort

        
        
        #Resolution Scale
        if system.isOptSet('ryu_resolution_scale'):
            if system.config["ryu_resolution_scale"] in {'1.0', '2.0', '3.0', '4.0', 1.0, 2.0, 3.0, 4.0}:
                data['res_scale_custom'] = 1
                if system.config["ryu_resolution_scale"] in {'1.0', 1.0}:
                    data['res_scale'] = 1
                if system.config["ryu_resolution_scale"] in {'2.0', 2.0}:
                    data['res_scale'] = 2
                if system.config["ryu_resolution_scale"] in {'3.0', 3.0}:
                    data['res_scale'] = 3
                if system.config["ryu_resolution_scale"] in {'4.0', 4.0}:
                    data['res_scale'] = 4
            else:
                data['res_scale_custom'] = float(system.config["ryu_resolution_scale"])
                data['res_scale'] = -1
        else:
            data['res_scale_custom'] = 1
            data['res_scale'] = 1

        #Texture Recompression
        if system.isOptSet('ryu_texture_recompression'):
            if system.config["ryu_texture_recompression"] in {"true", "1", 1}:
                data['enable_texture_recompression'] = True
            elif system.config["ryu_texture_recompression"] in {"false", "0", 0}:
                data['enable_texture_recompression'] = False
        else:
            data['enable_texture_recompression'] = False

        #Vulkan or OpenGl
        if system.isOptSet('ryu_backend'):
            data['graphics_backend'] = system.config["ryu_backend"]
        else:
            data['graphics_backend'] = 'Vulkan'

        #Audio backend: SDL2 or OpenAL
        if system.isOptSet('ryu_audio_backend'):
            data['audio_backend'] = system.config["ryu_audio_backend"]
        else:
            data['audio_backend'] = 'SDL2'

        # this erases the user manual configuration.
        # It's problematic in case of hybrid laptop as it may always default to the igpu instead of the dgpu
        # data['preferred_gpu'] = ""

        with open(RYUJINX_CONFIG / "BeforeRyu.json", "w") as outfile:
            outfile.write(json.dumps(data, indent=2))

        with open(RyujinxConfigFile, "w") as outfile:
            outfile.write(json.dumps(data, indent=2))


def getLangFromEnvironment():
    lang = environ['LANG'][:5]
    availableLanguages = [ "en_US", "pt_BR", "es_ES", "fr_FR", "de_DE","it_IT", "el_GR", "tr_TR", "zh_CN"]
    if lang in availableLanguages:
        return lang
    else:
        return "en_US"
