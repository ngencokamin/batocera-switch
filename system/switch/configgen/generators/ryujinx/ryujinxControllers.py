from __future__ import annotations

import configparser
from typing import TYPE_CHECKING, Any

import pyudev
import os
import logging
import subprocess

from configgen.batoceraPaths import mkdir_if_not_exists
from .ryujinxPaths import RYUJINX_CONFIG

if TYPE_CHECKING:
    from pathlib import Path
    from configgen.controller import Controller, ControllerMapping
    from configgen.Emulator import Emulator


eslog = logging.getLogger(__name__)


def generateControllerConfig(system: Emulator, playersControllers: ControllerMapping, ryujinx_config_file):
    if ((system.isOptSet('ryu_auto_controller_config') and not (system.config["ryu_auto_controller_config"] == "0")) or not system.isOptSet('ryu_auto_controller_config')):

            # make sure that libSDL2.so is restored (because when using Xbox series X, it has to be renamed in libSDL2.so-configgen
            filename_sdl2 = os.environ["PYSDL2_DLL_PATH"] + "libSDL2.so"
            filename_sdl2_configgen = filename_sdl2 + "-configgen"
            if not os.path.exists(filename_sdl2):
                os.replace(filename_sdl2_configgen, filename_sdl2)

            filename = "/userdata/system/switch/configgen/debugcontrollers.txt"
            if os.path.exists(filename):
                file = open(filename, 'r')
                debugcontrollers = bool(file.readline())
                file.close()
            else:
                debugcontrollers = False

            if debugcontrollers:
                eslog.debug(
                    "=====================================================Start Bato Controller Debug Info=========================================================")
                for index in playersControllers:
                    controller = playersControllers[index]
                    eslog.debug("Controller configName: {}".format(
                        controller.configName))
                    eslog.debug(
                        "Controller index: {}".format(controller.index))
                    eslog.debug("Controller realName: {}".format(
                        controller.realName))
                    eslog.debug("Controller dev: {}".format(controller.dev))
                    eslog.debug("Controller player: {}".format(
                        controller.player))
                    eslog.debug("Controller GUID: {}".format(controller.guid))
                    eslog.debug("")
                eslog.debug(
                    "=====================================================End Bato Controller Debug Info===========================================================")
                eslog.debug("")

            import sdl2
            from sdl2 import (
                SDL_TRUE
            )
            from sdl2 import joystick
            from ctypes import create_string_buffer
            sdl2.SDL_ClearError()
            sdl2.SDL_SetHint(b"SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", b"1")
            ret = sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO |
                                sdl2.SDL_INIT_GAMECONTROLLER)
            assert ret == 0, _check_error_msg()

            input_config = []

            sdl_devices = []
            count = joystick.SDL_NumJoysticks()

            if debugcontrollers:
                eslog.debug(
                    "=====================================================Start SDL Controller Debug Info==========================================================")
                for i in range(count):
                    if sdl2.SDL_IsGameController(i) == SDL_TRUE:
                        pad = sdl2.SDL_JoystickOpen(i)
                        cont = sdl2.SDL_GameControllerOpen(i)
                        joy_guid = joystick.SDL_JoystickGetDeviceGUID(i)
                        buff = create_string_buffer(33)
                        joystick.SDL_JoystickGetGUIDString(joy_guid, buff, 33)
                        buff[2] = b'0'
                        buff[3] = b'0'
                        buff[4] = b'0'
                        buff[5] = b'0'
                        buff[6] = b'0'
                        buff[7] = b'0'
                        guidstring = ((bytes(buff)).decode()
                                      ).split('\x00', 1)[0]
                        eslog.debug("Joystick GUID: {}".format(guidstring))
                        joy_path = joystick.SDL_JoystickPathForIndex(i)
                        eslog.debug("Joystick Path: {}".format(
                            joy_path.decode()))
                        eslog.debug("Joystick Type: {}".format(
                            sdl2.SDL_JoystickGetDeviceType(i)))
                        pad_type = sdl2.SDL_GameControllerTypeForIndex(i)
                        eslog.debug("Joystick Pad Type: {}".format(pad_type))
                        controllername = (
                            sdl2.SDL_GameControllerNameForIndex(i)).decode()
                        eslog.debug("Joystick Name: {}".format(controllername))

                        eslog.debug("Joystick Vendor: {}".format(
                            joystick.SDL_JoystickGetDeviceVendor(i)))
                        eslog.debug("Joystick Product: {}".format(
                            joystick.SDL_JoystickGetDeviceProduct(i)))
                        eslog.debug("Joystick Product Version: {}".format(
                            joystick.SDL_JoystickGetDeviceProductVersion(i)))

                        sdl2.SDL_GameControllerClose(cont)
                        sdl2.SDL_JoystickClose(pad)
                        eslog.debug("")
                eslog.debug(
                    "=====================================================End SDL Controller Debug Info============================================================")
                eslog.debug("")

            for i in range(count):
                    if sdl2.SDL_IsGameController(i) == SDL_TRUE:
                        pad = sdl2.SDL_GameControllerOpen(i)
                        joy_guid = joystick.SDL_JoystickGetDeviceGUID(i)
                        buff = create_string_buffer(33)
                        joystick.SDL_JoystickGetGUIDString(joy_guid, buff, 33)
                        joy_path = joystick.SDL_JoystickPathForIndex(i)
                        guidstring = ((bytes(buff)).decode()
                                      ).split('\x00', 1)[0]

                        if (joy_path.decode() == 'nintendo_joycons_combined'):
                            outputpath = 'nintendo_joycons_combined'
                        else:
                            command = "udevadm info --query=path --name=" + joy_path.decode()
                            outputpath = (((subprocess.check_output(command, shell=True)).decode()).partition(
                                '/input/')[0]).partition('/hidraw')[0]

                        pad_type = sdl2.SDL_GameControllerTypeForIndex(i)
                        # Fix for Steam controller assignment
                        controllername = (
                            sdl2.SDL_GameControllerNameForIndex(i)).decode()
                        if ("Steam" in controllername):
                            pad_type = 1
                        if ("Xin-Mo Xin-Mo Dual Arcade" in controllername):
                            pad_type = 1
                        controller_value = {
                            "index": i, 'path': outputpath, "guid": guidstring, "type": pad_type}
                        sdl_devices.append(controller_value)
                        sdl2.SDL_GameControllerClose(pad)
            sdl2.SDL_Quit()

            eslog.debug("Joysticks: {}".format(sdl_devices))
            # New Logic
            for index in playersControllers:
                controller = playersControllers[index]
                # inputguid = controller.guid
                if (controller.guid != "050000007e0500000620000001800000" and controller.guid != "050000007e0500000720000001800000"):
                    # don't run the code for Joy-Con (L) or Joy-Con (R) - Batocera adds these and only works with a pair
                    if debugcontrollers:
                        eslog.debug("Controller configName: {}".format(
                            controller.configName))
                        eslog.debug(
                            "Controller index: {}".format(controller.index))
                        eslog.debug("Controller realName: {}".format(
                            controller.realName))
                        eslog.debug(
                            "Controller dev: {}".format(controller.dev))
                        eslog.debug("Controller player: {}".format(
                            controller.player))
                        eslog.debug(
                            "Controller GUID: {}".format(controller.guid))

                    # works in Batocera v37
                    if (playersControllers[index].realName == 'Nintendo Switch Combined Joy-Cons'):
                        outputpath = "nintendo_joycons_combined"
                        sdl_mapping = next((item for item in sdl_devices if (
                            item["path"] == outputpath or item["path"] == '/devices/virtual')), None)
                    else:
                        command = "udevadm info --query=path --name=" + \
                            playersControllers[index].dev
                        outputpath = ((subprocess.check_output(
                            command, shell=True)).decode()).partition('/input/')[0]
                        sdl_mapping = next(
                            (item for item in sdl_devices if item["path"] == outputpath), None)

                    eslog.debug("Mapping: {}".format(sdl_mapping))

                    myid = uuid.UUID(sdl_mapping['guid'])
                    myid.bytes_le
                    convuuid = uuid.UUID(bytes=myid.bytes_le)
                    controllernumber = str(sdl_mapping['index'])
                    # Map Keys and GUIDs
                    cvalue = {}

                    motion = {}
                    motion['motion_backend'] = "GamepadDriver"
                    motion['sensitivity'] = 100
                    motion['gyro_deadzone'] = 1

                    motion['enable_motion'] = bool('true')

                    rumble = {}
                    rumble['strong_rumble'] = 1
                    rumble['weak_rumble'] = 1
                    if system.isOptSet("ryu_enable_rumble"):
                        rumble['enable_rumble'] = bool(
                            int(system.config["ryu_enable_rumble"]))
                    else:
                        rumble['enable_rumble'] = bool('true')

                    which_pad = "p" + str(int(controller.player)) + "_pad"

                    if ((system.isOptSet(which_pad) and ((system.config[which_pad] == "ProController") or (system.config[which_pad] == "JoyconPair"))) or not system.isOptSet(which_pad)):
                        left_joycon_stick = {}
                        left_joycon_stick['joystick'] = "Left"
                        left_joycon_stick['rotate90_cw'] = bool(0)
                        left_joycon_stick['invert_stick_x'] = bool(0)
                        left_joycon_stick['invert_stick_y'] = bool(0)
                        left_joycon_stick['stick_button'] = "LeftStick"

                        right_joycon_stick = {}
                        right_joycon_stick['joystick'] = "Right"
                        right_joycon_stick['rotate90_cw'] = bool(0)
                        right_joycon_stick['invert_stick_x'] = bool(0)
                        right_joycon_stick['invert_stick_y'] = bool(0)
                        right_joycon_stick['stick_button'] = "RightStick"

                        left_joycon = {}
                        left_joycon['button_minus'] = "Minus"
                        left_joycon['button_l'] = "LeftShoulder"
                        left_joycon['button_zl'] = "LeftTrigger"
                        left_joycon['button_sl'] = "Unbound"
                        left_joycon['button_sr'] = "Unbound"
                        left_joycon['dpad_up'] = "DpadUp"
                        left_joycon['dpad_down'] = "DpadDown"
                        left_joycon['dpad_left'] = "DpadLeft"
                        left_joycon['dpad_right'] = "DpadRight"

                        right_joycon = {}
                        right_joycon['button_plus'] = "Plus"
                        right_joycon['button_r'] = "RightShoulder"
                        right_joycon['button_zr'] = "RightTrigger"
                        right_joycon['button_sl'] = "Unbound"
                        right_joycon['button_sr'] = "Unbound"

                        if (sdl_mapping['type'] == 0) or (sdl_mapping['type'] == 5) or (sdl_mapping['type'] >= 11):
                            right_joycon['button_x'] = "X"
                            right_joycon['button_b'] = "B"
                            right_joycon['button_y'] = "Y"
                            right_joycon['button_a'] = "A"
                        else:
                            right_joycon['button_x'] = "Y"
                            right_joycon['button_b'] = "A"
                            right_joycon['button_y'] = "X"
                            right_joycon['button_a'] = "B"

                        if system.isOptSet(which_pad):
                            cvalue['controller_type'] = system.config["p1_pad"]
                        else:
                            cvalue['controller_type'] = "ProController"

                    elif (system.isOptSet(which_pad) and (system.config[which_pad] == "JoyconLeft")):
                        left_joycon_stick = {}
                        left_joycon_stick['joystick'] = "Left"
                        left_joycon_stick['rotate90_cw'] = bool(0)
                        left_joycon_stick['invert_stick_x'] = bool(0)
                        left_joycon_stick['invert_stick_y'] = bool(0)
                        left_joycon_stick['stick_button'] = "LeftStick"

                        right_joycon_stick = {}
                        right_joycon_stick['joystick'] = "Unbound"
                        right_joycon_stick['rotate90_cw'] = bool(0)
                        right_joycon_stick['invert_stick_x'] = bool(0)
                        right_joycon_stick['invert_stick_y'] = bool(0)
                        right_joycon_stick['stick_button'] = "Unbound"

                        left_joycon = {}
                        left_joycon['button_minus'] = "Minus"
                        left_joycon['button_l'] = "LeftShoulder"
                        left_joycon['button_zl'] = "LeftTrigger"
                        left_joycon['button_sl'] = "LeftShoulder"
                        left_joycon['button_sr'] = "RightShoulder"

                        if (sdl_mapping['type'] == 0) or (sdl_mapping['type'] == 5) or (sdl_mapping['type'] >= 11):
                            left_joycon['dpad_up'] = "Y"
                            left_joycon['dpad_down'] = "A"
                            left_joycon['dpad_left'] = "X"
                            left_joycon['dpad_right'] = "B"
                        else:
                            left_joycon['dpad_up'] = "Y"
                            left_joycon['dpad_down'] = "A"
                            left_joycon['dpad_left'] = "X"
                            left_joycon['dpad_right'] = "B"

                        right_joycon = {}
                        right_joycon['button_plus'] = "Plus"
                        right_joycon['button_r'] = "RightShoulder"
                        right_joycon['button_zr'] = "RightTrigger"
                        right_joycon['button_sl'] = "Unbound"
                        right_joycon['button_sr'] = "Unbound"

                        if (sdl_mapping['type'] == 0) or (sdl_mapping['type'] == 5) or (sdl_mapping['type'] >= 11):
                            right_joycon['button_x'] = "X"
                            right_joycon['button_b'] = "B"
                            right_joycon['button_y'] = "Y"
                            right_joycon['button_a'] = "A"
                        else:
                            right_joycon['button_x'] = "Y"
                            right_joycon['button_b'] = "A"
                            right_joycon['button_y'] = "X"
                            right_joycon['button_a'] = "B"

                        cvalue['controller_type'] = "JoyconLeft"

                    elif (system.isOptSet(which_pad) and (system.config[which_pad] == "JoyconRight")):
                        left_joycon_stick = {}
                        left_joycon_stick['joystick'] = "Unbound"
                        left_joycon_stick['rotate90_cw'] = bool(1)
                        left_joycon_stick['invert_stick_x'] = bool(1)
                        left_joycon_stick['invert_stick_y'] = bool(1)
                        left_joycon_stick['stick_button'] = "Unbound"

                        right_joycon_stick = {}
                        right_joycon_stick['joystick'] = "Left"
                        right_joycon_stick['rotate90_cw'] = bool(0)
                        right_joycon_stick['invert_stick_x'] = bool(0)
                        right_joycon_stick['invert_stick_y'] = bool(0)
                        right_joycon_stick['stick_button'] = "LeftStick"

                        left_joycon = {}
                        left_joycon['button_minus'] = "Minus"
                        left_joycon['button_l'] = "LeftShoulder"
                        left_joycon['button_zl'] = "LeftTrigger"
                        left_joycon['button_sl'] = "Unbound"
                        left_joycon['button_sr'] = "Unbound"

                        left_joycon['dpad_up'] = "DpadUp"
                        left_joycon['dpad_down'] = "DpadDown"
                        left_joycon['dpad_left'] = "DpadLeft"
                        left_joycon['dpad_right'] = "DpadRight"

                        right_joycon = {}
                        right_joycon['button_plus'] = "Plus"
                        right_joycon['button_r'] = "RightShoulder"
                        right_joycon['button_zr'] = "RightTrigger"
                        right_joycon['button_sl'] = "LeftShoulder"
                        right_joycon['button_sr'] = "RightShoulder"

                        if (sdl_mapping['type'] == 0) or (sdl_mapping['type'] == 5) or (sdl_mapping['type'] >= 11):
                            right_joycon['button_x'] = "A"
                            right_joycon['button_b'] = "Y"
                            right_joycon['button_y'] = "X"
                            right_joycon['button_a'] = "B"
                        else:
                            right_joycon['button_x'] = "B"
                            right_joycon['button_b'] = "X"
                            right_joycon['button_y'] = "Y"
                            right_joycon['button_a'] = "A"
                        cvalue['controller_type'] = "JoyconRight"
                    else:
                        # Handle old settings that don't match above
                        left_joycon_stick = {}
                        left_joycon_stick['joystick'] = "Left"
                        left_joycon_stick['rotate90_cw'] = bool(0)
                        left_joycon_stick['invert_stick_x'] = bool(0)
                        left_joycon_stick['invert_stick_y'] = bool(0)
                        left_joycon_stick['stick_button'] = "LeftStick"

                        right_joycon_stick = {}
                        right_joycon_stick['joystick'] = "Right"
                        right_joycon_stick['rotate90_cw'] = bool(0)
                        right_joycon_stick['invert_stick_x'] = bool(0)
                        right_joycon_stick['invert_stick_y'] = bool(0)
                        right_joycon_stick['stick_button'] = "RightStick"

                        left_joycon = {}
                        left_joycon['button_minus'] = "Minus"
                        left_joycon['button_l'] = "LeftShoulder"
                        left_joycon['button_zl'] = "LeftTrigger"
                        left_joycon['button_sl'] = "Unbound"
                        left_joycon['button_sr'] = "Unbound"
                        left_joycon['dpad_up'] = "DpadUp"
                        left_joycon['dpad_down'] = "DpadDown"
                        left_joycon['dpad_left'] = "DpadLeft"
                        left_joycon['dpad_right'] = "DpadRight"

                        right_joycon = {}
                        right_joycon['button_plus'] = "Plus"
                        right_joycon['button_r'] = "RightShoulder"
                        right_joycon['button_zr'] = "RightTrigger"
                        right_joycon['button_sl'] = "Unbound"
                        right_joycon['button_sr'] = "Unbound"

                        if (sdl_mapping['type'] == 0) or (sdl_mapping['type'] == 5) or (sdl_mapping['type'] >= 11):
                            right_joycon['button_x'] = "X"
                            right_joycon['button_b'] = "B"
                            right_joycon['button_y'] = "Y"
                            right_joycon['button_a'] = "A"
                        else:
                            right_joycon['button_x'] = "Y"
                            right_joycon['button_b'] = "A"
                            right_joycon['button_y'] = "X"
                            right_joycon['button_a'] = "B"

                        cvalue['controller_type'] = "ProController"

                    cvalue['left_joycon_stick'] = left_joycon_stick
                    cvalue['right_joycon_stick'] = right_joycon_stick
                    cvalue['deadzone_left'] = 0.1
                    cvalue['deadzone_right'] = 0.1
                    cvalue['range_left'] = 1
                    cvalue['range_right'] = 1
                    cvalue['trigger_threshold'] = 0.5
                    cvalue['motion'] = motion
                    cvalue['rumble'] = rumble
                    cvalue['left_joycon'] = left_joycon
                    cvalue['right_joycon'] = right_joycon

                    cvalue['version'] = 1
                    cvalue['backend'] = "GamepadSDL2"
                    cvalue['id'] = controllernumber + '-' + str(convuuid)

                    cvalue['player_index'] = "Player" + \
                        str(int(controller.player))
                    input_config.append(cvalue)

            data['input_config'] = input_config

        # if we turn the auto_control_config off, then it's better to avoid conflicts with the sdl2 coming from ryujinx (which completely messes up xbox series x controllers with both bluetooth and dongle
    try:
        if system.config["ryu_auto_controller_config"] == "0":
            filename_sdl2 = os.environ["PYSDL2_DLL_PATH"] + "libSDL2.so"
            filename_sdl2_configgen = filename_sdl2 + "-configgen"
            if os.path.exists(filename_sdl2):
                os.replace(filename_sdl2, filename_sdl2_configgen)
    except:
        pass