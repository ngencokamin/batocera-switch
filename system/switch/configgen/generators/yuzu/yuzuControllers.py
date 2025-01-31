from __future__ import annotations

import configparser
from typing import TYPE_CHECKING, Any

import pyudev
import os
import logging
import subprocess

from configgen.batoceraPaths import mkdir_if_not_exists
from .yuzuPaths import YUZU_CONFIG

if TYPE_CHECKING:
    from pathlib import Path
    from configgen.controller import Controller, ControllerMapping
    from configgen.Emulator import Emulator


eslog = logging.getLogger(__name__)

def generateControllerConfig(system: Emulator, playersControllers: ControllerMapping, yuzu_config_file):

    # pads
    os.environ["PYSDL2_DLL_PATH"] = "/userdata/system/switch/extra/sdl/"

    # Define buttons and axis
    yuzuButtons = {
        "button_a":      "a",
        "button_b":      "b",
        "button_x":      "x",
        "button_y":      "y",
        "button_dup":     "up",
        "button_ddown":   "down",
        "button_dleft":   "left",
        "button_dright":  "right",
        "button_l":      "pageup",
        "button_r":      "pagedown",
        "button_plus":  "start",
        "button_minus": "select",
        "button_sl":     "pageup",
        "button_sr":     "pagedown",
        "button_zl":     "l2",
        "button_zr":     "r2",
        "button_lstick":     "l3",
        "button_rstick":     "r3",
        "button_home":   "hotkey"
    }

    yuzuAxis = {
        "lstick":    "joystick1",
        "rstick":    "joystick2"
    }

    # Open Configuration File for Writing
    yuzu_config = configparser.RawConfigParser()
    yuzu_config.optionxform = str

    # Not including line checking if it exists bc it
    # should have been created in Yuzu generator before
    # this was called
    yuzu_config.read(yuzu_config_file)

    # Write to config
    if not yuzu_config.has_section("Controls"):
        yuzu_config.add_section("Controls")

    # Rumble
    if system.isOptSet("yuzu_enable_rumble"):
        yuzu_config.set("Controls", "vibration_enabled",
                        system.config["yuzu_enable_rumble"])
        yuzu_config.set("Controls", "vibration_enabled\\default",
                        system.config["yuzu_enable_rumble"])
    else:
        yuzu_config.set("Controls", "vibration_enabled", "true")
        yuzu_config.set("Controls", "vibration_enabled\\default", "true")

    # Controller Applet
    # Enabled breaks multiplayer games like Mario Kart for some Yuzu versions
    if system.isOptSet("yuzu_controller_applet"):
        yuzu_config.set("LibraryApplet", "controller_applet_mode",
                        system.config["yuzu_controller_applet"])
        yuzu_config.set("LibraryApplet", "controller_applet_mode\\default",
                        system.config["yuzu_controller_applet"])
    else:
        yuzu_config.set("LibraryApplet", "controller_applet_mode", "false")
        yuzu_config.set("LibraryApplet",
                        "controller_applet_mode\\default", "false")

    # Actual Controls
    # Check if auto config is enabled
    if ((system.isOptSet('yuzu_auto_controller_config') and not (system.config["yuzu_auto_controller_config"] == "0")) or not system.isOptSet('yuzu_auto_controller_config')):

        known_reversed_guids = ["03000000c82d00000631000014010000"]
        # These are controllers that use Batocera mappings for some reason
        use_batocera_guids = ["050000005e0400008e02000030110000",
                              "030000005e0400008e02000014010000", "0000000053696e64656e206c69676800"]
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
                    controller.name))
                eslog.debug("Controller index: {}".format(controller.index))
                eslog.debug("Controller real_name: {}".format(
                    controller.real_name))
                eslog.debug("Controller dev: {}".format(controller.device_path))
                eslog.debug("Controller player: {}".format(controller.player_number))
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
        ret = sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_GAMECONTROLLER)
        assert ret == 0, _check_error_msg()

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
                    guidstring = ((bytes(buff)).decode()).split('\x00', 1)[0]
                    eslog.debug("Joystick GUID: {}".format(guidstring))
                    joy_path = joystick.SDL_JoystickPathForIndex(i)
                    eslog.debug("Joystick Path: {}".format(joy_path.decode()))
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
                pad = sdl2.SDL_JoystickOpen(i)
                cont = sdl2.SDL_GameControllerOpen(i)
                # iid = sdl2.SDL_JoystickInstanceID(pad)
                # gc = sdl2.SDL_GameControllerMappingForDeviceIndex(i)

                gc_a = sdl2.SDL_GameControllerGetBindForButton(
                    cont, sdl2.SDL_CONTROLLER_BUTTON_A)
                if (gc_a.bindType == sdl2.SDL_CONTROLLER_BINDTYPE_HAT):
                    button_b = "hat:" + str(gc_a.value.hat.hat)
                else:
                    button_b = gc_a.value.button

                gc_b = sdl2.SDL_GameControllerGetBindForButton(
                    cont, sdl2.SDL_CONTROLLER_BUTTON_B)
                if (gc_b.bindType == sdl2.SDL_CONTROLLER_BINDTYPE_HAT):
                    button_a = "hat:" + str(gc_b.value.hat.hat)
                else:
                    button_a = gc_b.value.button

                gc_x = sdl2.SDL_GameControllerGetBindForButton(
                    cont, sdl2.SDL_CONTROLLER_BUTTON_X)
                if (gc_x.bindType == sdl2.SDL_CONTROLLER_BINDTYPE_HAT):
                    button_y = "hat:" + str(gc_x.value.hat.hat)
                else:
                    button_y = gc_x.value.button

                gc_y = sdl2.SDL_GameControllerGetBindForButton(
                    cont, sdl2.SDL_CONTROLLER_BUTTON_Y)
                if (gc_y.bindType == sdl2.SDL_CONTROLLER_BINDTYPE_HAT):
                    button_x = "hat:" + str(gc_y.value.hat.hat)
                else:
                    button_x = gc_y.value.button

                gc_dup = sdl2.SDL_GameControllerGetBindForButton(
                    cont, sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP)
                if (gc_dup.bindType == sdl2.SDL_CONTROLLER_BINDTYPE_HAT):
                    button_dup = "hat:" + str(gc_dup.value.hat.hat)
                else:
                    button_dup = gc_dup.value.button

                gc_ddown = sdl2.SDL_GameControllerGetBindForButton(
                    cont, sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN)
                if (gc_ddown.bindType == sdl2.SDL_CONTROLLER_BINDTYPE_HAT):
                    button_ddown = "hat:" + str(gc_ddown.value.hat.hat)
                else:
                    button_ddown = gc_ddown.value.button

                gc_dleft = sdl2.SDL_GameControllerGetBindForButton(
                    cont, sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT)
                if (gc_dleft.bindType == sdl2.SDL_CONTROLLER_BINDTYPE_HAT):
                    button_dleft = "hat:" + str(gc_ddown.value.hat.hat)
                else:
                    button_dleft = gc_dleft.value.button

                gc_dright = sdl2.SDL_GameControllerGetBindForButton(
                    cont, sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT)
                if (gc_dright.bindType == sdl2.SDL_CONTROLLER_BINDTYPE_HAT):
                    button_dright = "hat:" + str(gc_ddown.value.hat.hat)
                else:
                    button_dright = gc_dright.value.button

                gc_l = sdl2.SDL_GameControllerGetBindForButton(
                    cont, sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER)
                if (gc_l.bindType == sdl2.SDL_CONTROLLER_BINDTYPE_HAT):
                    button_l = "hat:" + str(gc_l.value.hat.hat)
                else:
                    button_l = gc_l.value.button

                gc_r = sdl2.SDL_GameControllerGetBindForButton(
                    cont, sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER)
                if (gc_r.bindType == sdl2.SDL_CONTROLLER_BINDTYPE_HAT):
                    button_r = "hat:" + str(gc_r.value.hat.hat)
                else:
                    button_r = gc_r.value.button

                gc_lstick = sdl2.SDL_GameControllerGetBindForButton(
                    cont, sdl2.SDL_CONTROLLER_BUTTON_LEFTSTICK)
                button_lstick = gc_lstick.value.button

                gc_rstick = sdl2.SDL_GameControllerGetBindForButton(
                    cont, sdl2.SDL_CONTROLLER_BUTTON_RIGHTSTICK)
                button_rstick = gc_rstick.value.button

                gc_home = sdl2.SDL_GameControllerGetBindForButton(
                    cont, sdl2.SDL_CONTROLLER_BUTTON_GUIDE)
                button_home = gc_home.value.button

                gc_minus = sdl2.SDL_GameControllerGetBindForButton(
                    cont, sdl2.SDL_CONTROLLER_BUTTON_BACK)
                button_minus = gc_minus.value.button

                gc_plus = sdl2.SDL_GameControllerGetBindForButton(
                    cont, sdl2.SDL_CONTROLLER_BUTTON_START)
                button_plus = gc_plus.value.button

                gc_zl = sdl2.SDL_GameControllerGetBindForAxis(
                    cont, sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT)
                if (gc_zl.bindType == sdl2.SDL_CONTROLLER_BINDTYPE_AXIS):
                    button_zl = "axis"
                    axis_button_zl = gc_zl.value.axis
                else:
                    button_zl = gc_zl.value.button
                    axis_button_zl = "noaxis"

                gc_zr = sdl2.SDL_GameControllerGetBindForAxis(
                    cont, sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT)
                if (gc_zr.bindType == sdl2.SDL_CONTROLLER_BINDTYPE_AXIS):
                    button_zr = "axis"
                    axis_button_zr = gc_zr.value.axis
                else:
                    button_zr = gc_zr.value.button
                    axis_button_zr = "noaxis"

                gc_axis_lstick_x = sdl2.SDL_GameControllerGetBindForAxis(
                    cont, sdl2.SDL_CONTROLLER_AXIS_LEFTX)
                axis_lstick_x = gc_axis_lstick_x.value.axis

                gc_axis_rstick_x = sdl2.SDL_GameControllerGetBindForAxis(
                    cont, sdl2.SDL_CONTROLLER_AXIS_RIGHTX)
                axis_rstick_x = gc_axis_rstick_x.value.axis

                joy_guid = joystick.SDL_JoystickGetDeviceGUID(i)
                buff = create_string_buffer(33)
                joystick.SDL_JoystickGetGUIDString(joy_guid, buff, 33)
                joy_path = joystick.SDL_JoystickPathForIndex(i)
                buff[2] = b'0'
                buff[3] = b'0'
                buff[4] = b'0'
                buff[5] = b'0'
                buff[6] = b'0'
                buff[7] = b'0'
                guidstring = ((bytes(buff)).decode()).split('\x00', 1)[0]
                if (joy_path.decode() == 'nintendo_joycons_combined'):
                    outputpath = 'nintendo_joycons_combined'
                else:
                    command = "udevadm info --query=path --name=" + joy_path.decode()
                    outputpath = (((subprocess.check_output(command, shell=True)).decode()).partition(
                        '/input/')[0]).partition('/hidraw')[0]
                pad_type = sdl2.SDL_GameControllerTypeForIndex(i)
                controllername = (
                    sdl2.SDL_GameControllerNameForIndex(i)).decode()

                if ("Steam" in controllername):
                    pad_type = 1
                if ("Xin-Mo Xin-Mo Dual Arcade" in controllername):
                    pad_type = 1
                # Fix for Steam controller assignment
                controller_value = {
                    "index": i,
                    'path': outputpath,
                    "guid": guidstring,
                    # "instance" : iid,
                    "type": pad_type,
                    "button_a": button_a,
                    "button_b": button_b,
                    "button_x": button_x,
                    "button_y": button_y,
                    "button_dup": button_dup,
                    "button_ddown": button_ddown,
                    "button_dleft": button_dleft,
                    "button_dright": button_dright,
                    "button_l": button_l,
                    "button_r": button_r,
                    "button_sl": button_l,
                    "button_sr": button_r,
                    "button_lstick": button_lstick,
                    "button_rstick": button_rstick,
                    "button_minus": button_minus,
                    "button_plus": button_plus,
                    "button_home": button_home,
                    "button_zl": button_zl,
                    "button_zr": button_zr,
                    "axis_button_zl": axis_button_zl,
                    "axis_button_zr": axis_button_zr,
                    "axis_lstick_x": axis_lstick_x,
                    "axis_rstick_x": axis_rstick_x
                }
                sdl_devices.append(controller_value)
                sdl2.SDL_GameControllerClose(cont)
                sdl2.SDL_JoystickClose(pad)
        sdl2.SDL_Quit()

        eslog.debug("Joysticks: {}".format(sdl_devices))
        cguid = [0 for x in range(10)]
        lastplayer = 0
        for index in playersControllers :
            controller = playersControllers[index]


            if(controller.guid != "050000007e0500000620000001800000" and controller.guid != "050000007e0500000720000001800000"):
                #don't run the code for Joy-Con (L) or Joy-Con (R) - Batocera adds these and only works with a pair
                which_pad = "p" + str(lastplayer+1) + "_pad"

                if debugcontrollers:
                    eslog.debug("Controller configName: {}".format(controller.name))
                    eslog.debug("Controller index: {}".format(controller.index))
                    eslog.debug("Controller real_name: {}".format(controller.real_name))                
                    eslog.debug("Controller dev: {}".format(controller.device_path))
                    eslog.debug("Controller player: {}".format(controller.player_number))
                    eslog.debug("Controller GUID: {}".format(controller.guid))
                    eslog.debug("Which Pad: {}".format(which_pad))


                if(playersControllers[index].real_name == 'Nintendo Switch Combined Joy-Cons'):  #works in Batocera v37
                    outputpath = "nintendo_joycons_combined"
                    sdl_mapping = next((item for item in sdl_devices if (item["path"] == outputpath or item["path"] == '/devices/virtual')),None)
                else:
                    command = "udevadm info --query=path --name=" + playersControllers[index].device_path
                    outputpath = ((subprocess.check_output(command, shell=True)).decode()).partition('/input/')[0]
                    sdl_mapping = next((item for item in sdl_devices if item["path"] == outputpath),None)

                if(controller.guid in known_reversed_guids):
                    eslog.debug("Swapping type for GUID")
                    if(sdl_mapping['type'] == 0):
                        sdl_mapping['type'] = 1
                    else:
                        sdl_mapping['type'] = 0          
                
                eslog.debug("Mapping: {}".format(sdl_mapping))

                if(controller.guid in use_batocera_guids):
                    inputguid = controller.guid
                    sdl_mapping = None
                    #Force the non-SDL controller branch
                else:
                    inputguid = sdl_mapping['guid']

                controllernumber = str(lastplayer)
                portnumber = cguid.count(inputguid)
                cguid[int(controllernumber)] = inputguid

                if debugcontrollers:
                    eslog.debug("Controller number: {}".format(controllernumber))
                    eslog.debug("Controller port: {}".format(portnumber))
                    eslog.debug("Controller cguid: {}".format(cguid[int(controllernumber)]))                


                if(sdl_mapping == None):
                    eslog.debug("Batocera controller Branch")
                    if (system.isOptSet(which_pad) and (system.config[which_pad] == "2")):
                        eslog.debug("Controller Type: Left Joycon")
                        #2 = Left Joycon
                        #Switch and generic controllers aren't swapping ABXY
                        yuzuButtons = {
                            "button_a":      "a", #notused on left joycon
                            "button_b":      "b", #notused on left joycon
                            "button_x":      "x", #notused on left joycon
                            "button_y":      "y", #notused on left joycon
                            "button_dup":     "y",
                            "button_ddown":   "a",
                            "button_dleft":   "b",
                            "button_dright":  "x",
                            "button_l":      "pageup",
                            "button_r":      "pagedown", #notused on left joycon
                            "button_plus":  "start", #notused on left joycon
                            "button_minus": "select",
                            "button_sl":     "pageup",
                            "button_sr":     "pagedown",
                            "button_lstick":     "l3",
                            "button_rstick":     "r3", #notused on left joycon
                            "button_home":   "hotkey", #notused on left joycon
                            "button_screenshot": "hotkey", #Added to left joycon to act as "home"
                            "button_zl": "l2",
                            "button_zr": "r2" #notused on left joycon
                        }

                        yuzuAxis = {
                            "lstick":    "joystick1",
                            "rstick":    "joystick1"
                        }

                        #Configure buttons and triggers
                        for x in yuzuButtons:
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"{}"'.format(setButton(yuzuButtons[x], inputguid, controller.inputs,portnumber)))
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x + "\\default", "false")

                        for x in yuzuAxis:
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"{}"'.format(setAxis(yuzuAxis[x], inputguid, controller.inputs, portnumber, 1)))
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x + "\\default", "false")


                    elif (system.isOptSet(which_pad) and (system.config[which_pad] == "3")):
                        eslog.debug("Controller Type: Right Joycon")
                        #3 = Right Joycon
                        #Switch and generic controllers aren't swapping ABXY
                        yuzuButtons = {
                            "button_a":      "b", 
                            "button_b":      "y", 
                            "button_x":      "a", 
                            "button_y":      "x", 
                            "button_dup":     "y", #notused on right joycon
                            "button_ddown":   "a", #notused on right joycon
                            "button_dleft":   "b", #notused on right joycon
                            "button_dright":  "x", #notused on right joycon
                            "button_l":      "pageup", #notused on right joycon
                            "button_r":      "pagedown",
                            "button_plus":  "start", #notused on left joycon
                            "button_minus": "select",
                            "button_sl":     "pageup",
                            "button_sr":     "pagedown",
                            "button_lstick":     "l3", #notused on right joycon
                            "button_rstick":     "r3", 
                            "button_home":   "hotkey", 
                            "button_screenshot": "hotkey", #Added to left joycon to act as "home"
                            "button_zl": "l2",
                            "button_zr": "r2"
                        }

                        yuzuAxis = {
                            "lstick":    "joystick1",
                            "rstick":    "joystick1"
                        }

                        #Configure buttons and triggers
                        for x in yuzuButtons:
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"{}"'.format(setButton(yuzuButtons[x], inputguid, controller.inputs,portnumber)))
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x + "\\default", "false")

                        for x in yuzuAxis:
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"{}"'.format(setAxis(yuzuAxis[x], inputguid, controller.inputs, portnumber,2)))
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x + "\\default", "false")

                    else:
                        eslog.debug("Controller Type: Non-Joycon")
                        #0 = Pro Controller, 1 = Dual Joycons, 4 = Handheld Mode,  (and other cases not yet defined)
                        #Switch and generic controllers aren't swapping ABXY
                        yuzuButtons = {
                            "button_a":      "a",
                            "button_b":      "b",
                            "button_x":      "x",
                            "button_y":      "y",
                            "button_dup":     "up",
                            "button_ddown":   "down",
                            "button_dleft":   "left",
                            "button_dright":  "right",
                            "button_l":      "pageup",
                            "button_r":      "pagedown",
                            "button_plus":  "start",
                            "button_minus": "select",
                            "button_sl":     "pageup",
                            "button_sr":     "pagedown",
                            "button_lstick":     "l3",
                            "button_rstick":     "r3",
                            "button_home":   "hotkey",
                            "button_zl": "l2",
                            "button_zr": "r2"
                        }

                        yuzuAxis = {
                            "lstick":    "joystick1",
                            "rstick":    "joystick2"
                        }

                        #Configure buttons and triggers
                        for x in yuzuButtons:
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"{}"'.format(setButton(yuzuButtons[x], inputguid, controller.inputs,portnumber)))
                    
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x + "\\default", "false")                           

                        for x in yuzuAxis:
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"{}"'.format(setAxis(yuzuAxis[x], inputguid, controller.inputs, portnumber,0)))     
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x + "\\default", "false")

                    #Enable motion no matter what, as enabling won't hurt things if it doesn't exist
                    yuzu_config.set("Controls", "player_" + controllernumber + "_motionleft", '"engine:sdl,motion:0,port:{},guid:{}"'.format(portnumber,inputguid))
                    yuzu_config.set("Controls", "player_" + controllernumber + "_motionright", '"engine:sdl,motion:0,port:{},guid:{}"'.format(portnumber,inputguid))

                    yuzu_config.set("Controls", "player_" + controllernumber + "_connected", "true")
                    if (controllernumber == "0"):
                        yuzu_config.set("Controls", "player_" + controllernumber + "_connected\\default", "true")
                    else:
                        yuzu_config.set("Controls", "player_" + controllernumber + "_connected\\default", "false")

                    if system.isOptSet(which_pad):
                        yuzu_config.set("Controls", "player_" + controllernumber + "_type", system.config["p1_pad"])
                        #yuzu_config.set("Controls", "player_0_type", system.config["p1_pad"])
                    else:
                        yuzu_config.set("Controls", "player_" + controllernumber + "_type", "0")

                    yuzu_config.set("Controls", "player_" + controllernumber + "_type\\default", "true")

                    if system.isOptSet("yuzu_enable_rumble"):
                        yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled", system.config["yuzu_enable_rumble"])
                        yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled\\default", system.config["yuzu_enable_rumble"])
                    else:
                        yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled", "true")
                        yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled\\default", "true")

                    lastplayer = int(controllernumber) + 1

                elif (sdl_mapping['type'] == 13):
                    #we have real joycons
                    eslog.debug("Joycon Branch")
                    yuzuPad1Buttons = {
                            "button_l":      64, 
                            "button_minus":  65536,
                            "button_lstick": 524288,
                            "button_screenshot": 2097152,
                            "button_dup":    2, 
                            "button_ddown":  1,
                            "button_dleft":  8,
                            "button_dright": 4,
                            "button_zl": 128
                        }
                    
                    yuzuPad2Buttons = {
                            "button_a":      2048, #notused on left joycon
                            "button_b":      1024, #notused on left joycon
                            "button_x":      512, #notused on left joycon
                            "button_y":      256, #notused on left joycon
                            "button_r":      16384, #notused on left joycon
                            "button_plus":   131072, #notused on left joycon
                            "button_rstick": 262144, #notused on left joycon
                            "button_home":   1048576,  #notused on left joycon
                            "button_zr": 32768 #notused on left joycon
                        }

                    if (system.isOptSet(which_pad) and (system.config[which_pad] == "2")):
                        eslog.debug("Controller Type: Left Joycon")
                        pad1 = 1
                        pad2 = 1
                        lastplayer = int(controllernumber)+1
                        
                        #Configure buttons and triggers
                        for x in yuzuPad1Buttons:
                            eslog.debug("Left Joycon {}".format(x))
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"pad:{},button:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,yuzuPad1Buttons[x],portnumber,pad1))
                        for x in yuzuPad2Buttons:
                            eslog.debug("Left Joycon {}".format(x))
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"pad:{},button:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad2,yuzuPad2Buttons[x],portnumber,pad2))

                        #sl and sr of left pad
                        eslog.debug("Left Joycon SL")
                        yuzu_config.set("Controls", "player_" + controllernumber + "_button_sl", '"pad:{},button:32,port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,portnumber,pad1))
                        yuzu_config.set("Controls", "player_" + controllernumber + "_button_sr", '"pad:{},button:16,port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,portnumber,pad1))

                        #set joysticks
                        yuzu_config.set("Controls", "player_" + controllernumber + "_lstick", '"axis_y:1,axis_x:0,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,portnumber,pad1))
                        yuzu_config.set("Controls", "player_" + controllernumber + "_rstick", '"axis_y:3,axis_x:2,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad2,portnumber,pad2))
                        
                        #Enable motion no matter what, as enabling won't hurt things if it doesn't exist
                        yuzu_config.set("Controls", "player_" + controllernumber + "_motionleft", '"motion:0,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,portnumber,pad1))
                        yuzu_config.set("Controls", "player_" + controllernumber + "_motionright", '"motion:1,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad2,portnumber,pad2))
                        yuzu_config.set("Controls", "player_" + controllernumber + "_connected", "true")
                        
                        if (controllernumber == "0"):
                            yuzu_config.set("Controls", "player_" + controllernumber + "_connected\\default", "true")
                        else:
                            yuzu_config.set("Controls", "player_" + controllernumber + "_connected\\default", "false")

                        #Forcing to left joycon
                        yuzu_config.set("Controls", "player_" + controllernumber + "_type", "2")
                        yuzu_config.set("Controls", "player_" + controllernumber + "_type\\default", "false")
                        if system.isOptSet("yuzu_enable_rumble"):
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled", system.config["yuzu_enable_rumble"])
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled\\default", system.config["yuzu_enable_rumble"])
                        else:
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled", "true")
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled\\default", "true")

                        eslog.debug("Controller Type: Right Joycon after Left")
                        pad1 = 2
                        pad2 = 2
                        controllernumber = str(lastplayer)
                        lastplayer = int(controllernumber)+1

                        #Configure buttons and triggers
                        for x in yuzuPad1Buttons:
                            eslog.debug("Right Joycon {}".format(x))
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"pad:{},button:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,yuzuPad1Buttons[x],portnumber,pad1))
                        for x in yuzuPad2Buttons:
                            eslog.debug("Right Joycon {}".format(x))
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"pad:{},button:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad2,yuzuPad2Buttons[x],portnumber,pad2))

                        #sl and sr of right pad
                        eslog.debug("Right Joycon SL")
                        yuzu_config.set("Controls", "player_" + controllernumber + "_button_sl", '"pad:{},button:8192,port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,portnumber,pad1))
                        yuzu_config.set("Controls", "player_" + controllernumber + "_button_sr", '"pad:{},button:4096,port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,portnumber,pad1))

                        #set joysticks
                        yuzu_config.set("Controls", "player_" + controllernumber + "_lstick", '"axis_y:1,axis_x:0,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,portnumber,pad1))
                        yuzu_config.set("Controls", "player_" + controllernumber + "_rstick", '"axis_y:3,axis_x:2,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad2,portnumber,pad2))
                        
                        #Enable motion no matter what, as enabling won't hurt things if it doesn't exist
                        yuzu_config.set("Controls", "player_" + controllernumber + "_motionleft", '"motion:0,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,portnumber,pad1))
                        yuzu_config.set("Controls", "player_" + controllernumber + "_motionright", '"motion:1,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad2,portnumber,pad2))



                        yuzu_config.set("Controls", "player_" + controllernumber + "_connected", "true")
                        if (controllernumber == "0"):
                            yuzu_config.set("Controls", "player_" + controllernumber + "_connected\\default", "true")
                        else:
                            yuzu_config.set("Controls", "player_" + controllernumber + "_connected\\default", "false")

                        #Forcing to right joycons
                        yuzu_config.set("Controls", "player_" + controllernumber + "_type", "3")
                        yuzu_config.set("Controls", "player_" + controllernumber + "_type\\default", "false")
                        if system.isOptSet("yuzu_enable_rumble"):
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled", system.config["yuzu_enable_rumble"])
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled\\default", system.config["yuzu_enable_rumble"])
                        else:
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled", "true")
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled\\default", "true")



                    
                    elif (system.isOptSet(which_pad) and (system.config[which_pad] == "3")):
                        eslog.debug("Controller Type: Right Joycon")
                        pad1 = 2
                        pad2 = 2

                        lastplayer = int(controllernumber)+1

                        #Configure buttons and triggers
                        for x in yuzuPad1Buttons:
                            eslog.debug("Right Joycon {}".format(x))
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"pad:{},button:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,yuzuPad1Buttons[x],portnumber,pad1))
                        for x in yuzuPad2Buttons:
                            eslog.debug("Right Joycon {}".format(x))
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"pad:{},button:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad2,yuzuPad2Buttons[x],portnumber,pad2))

                        #sl and sr of right pad
                        eslog.debug("Right Joycon SL")
                        yuzu_config.set("Controls", "player_" + controllernumber + "_button_sl", '"pad:{},button:8192,port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,portnumber,pad1))
                        yuzu_config.set("Controls", "player_" + controllernumber + "_button_sr", '"pad:{},button:4096,port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,portnumber,pad1))

                        #set joysticks
                        yuzu_config.set("Controls", "player_" + controllernumber + "_lstick", '"axis_y:1,axis_x:0,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,portnumber,pad1))
                        yuzu_config.set("Controls", "player_" + controllernumber + "_rstick", '"axis_y:3,axis_x:2,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad2,portnumber,pad2))
                        
                        #Enable motion no matter what, as enabling won't hurt things if it doesn't exist
                        yuzu_config.set("Controls", "player_" + controllernumber + "_motionleft", '"motion:0,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,portnumber,pad1))
                        yuzu_config.set("Controls", "player_" + controllernumber + "_motionright", '"motion:1,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad2,portnumber,pad2))



                        yuzu_config.set("Controls", "player_" + controllernumber + "_connected", "true")
                        if (controllernumber == "0"):
                            yuzu_config.set("Controls", "player_" + controllernumber + "_connected\\default", "true")
                        else:
                            yuzu_config.set("Controls", "player_" + controllernumber + "_connected\\default", "false")

                        #Forcing to right joycons
                        yuzu_config.set("Controls", "player_" + controllernumber + "_type", "3")
                        yuzu_config.set("Controls", "player_" + controllernumber + "_type\\default", "false")
                        if system.isOptSet("yuzu_enable_rumble"):
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled", system.config["yuzu_enable_rumble"])
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled\\default", system.config["yuzu_enable_rumble"])
                        else:
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled", "true")
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled\\default", "true")


                        eslog.debug("Controller Type: Left Joycon After Right")
                        pad1 = 1
                        pad2 = 1
                        controllernumber = str(lastplayer)
                        lastplayer = int(controllernumber)+1
                        
                        #Configure buttons and triggers
                        for x in yuzuPad1Buttons:
                            eslog.debug("Left Joycon {}".format(x))
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"pad:{},button:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,yuzuPad1Buttons[x],portnumber,pad1))
                        for x in yuzuPad2Buttons:
                            eslog.debug("Left Joycon {}".format(x))
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"pad:{},button:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad2,yuzuPad2Buttons[x],portnumber,pad2))

                        #sl and sr of left pad
                        eslog.debug("Left Joycon SL")
                        yuzu_config.set("Controls", "player_" + controllernumber + "_button_sl", '"pad:{},button:32,port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,portnumber,pad1))
                        yuzu_config.set("Controls", "player_" + controllernumber + "_button_sr", '"pad:{},button:16,port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,portnumber,pad1))

                        #set joysticks
                        yuzu_config.set("Controls", "player_" + controllernumber + "_lstick", '"axis_y:1,axis_x:0,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,portnumber,pad1))
                        yuzu_config.set("Controls", "player_" + controllernumber + "_rstick", '"axis_y:3,axis_x:2,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad2,portnumber,pad2))
                        
                        #Enable motion no matter what, as enabling won't hurt things if it doesn't exist
                        yuzu_config.set("Controls", "player_" + controllernumber + "_motionleft", '"motion:0,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,portnumber,pad1))
                        yuzu_config.set("Controls", "player_" + controllernumber + "_motionright", '"motion:1,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad2,portnumber,pad2))
                        yuzu_config.set("Controls", "player_" + controllernumber + "_connected", "true")
                        
                        if (controllernumber == "0"):
                            yuzu_config.set("Controls", "player_" + controllernumber + "_connected\\default", "true")
                        else:
                            yuzu_config.set("Controls", "player_" + controllernumber + "_connected\\default", "false")

                        #Forcing to left joycon
                        yuzu_config.set("Controls", "player_" + controllernumber + "_type", "2")
                        yuzu_config.set("Controls", "player_" + controllernumber + "_type\\default", "false")
                        if system.isOptSet("yuzu_enable_rumble"):
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled", system.config["yuzu_enable_rumble"])
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled\\default", system.config["yuzu_enable_rumble"])
                        else:
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled", "true")
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled\\default", "true")

                    else:
                        eslog.debug("Controller Type: Dual Joycons")
                        pad1 = 1
                        pad2 = 2
                        lastplayer = int(controllernumber)+1

                        #Configure buttons and triggers
                        for x in yuzuPad1Buttons:
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"pad:{},button:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,yuzuPad1Buttons[x],portnumber,pad1))
                        for x in yuzuPad2Buttons:
                            yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"pad:{},button:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad2,yuzuPad2Buttons[x],portnumber,pad2))

                        #sl and sr not connected for dual joycon mode
                        yuzu_config.set("Controls", "player_" + controllernumber + "button_sl", '[empty]')
                        yuzu_config.set("Controls", "player_" + controllernumber + "button_sr", '[empty]')

                        #set joysticks
                        yuzu_config.set("Controls", "player_" + controllernumber + "_lstick", '"axis_y:1,axis_x:0,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,portnumber,pad1))
                        yuzu_config.set("Controls", "player_" + controllernumber + "_rstick", '"axis_y:3,axis_x:2,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad2,portnumber,pad2))
                        
                        #Enable motion no matter what, as enabling won't hurt things if it doesn't exist
                        yuzu_config.set("Controls", "player_" + controllernumber + "_motionleft", '"motion:0,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad1,portnumber,pad1))
                        yuzu_config.set("Controls", "player_" + controllernumber + "_motionright", '"motion:1,pad:{},port:{},guid:0000000000000000000000000000000{},engine:joycon"'.format(pad2,portnumber,pad2))

                        yuzu_config.set("Controls", "player_" + controllernumber + "_connected", "true")
                        if (controllernumber == "0"):
                            yuzu_config.set("Controls", "player_" + controllernumber + "_connected\\default", "true")
                        else:
                            yuzu_config.set("Controls", "player_" + controllernumber + "_connected\\default", "false")

                        #Forcing to dual joycons
                        yuzu_config.set("Controls", "player_" + controllernumber + "_type", "1")
                        yuzu_config.set("Controls", "player_" + controllernumber + "_type\\default", "false")
                        if system.isOptSet("yuzu_enable_rumble"):
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled", system.config["yuzu_enable_rumble"])
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled\\default", system.config["yuzu_enable_rumble"])
                        else:
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled", "true")
                            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled\\default", "true")
                        
                else:
                    eslog.debug("SDL controller Branch")
                    if (system.isOptSet(which_pad) and (system.config[which_pad] == "2")):
                        eslog.debug("Controller Type: Left Joycon")
                        #2 = Left Joycon
                        #Switch and generic controllers aren't swapping ABXY
                        if (sdl_mapping['type'] == 0):
                            yuzuButtons = {
                                "button_a":      sdl_mapping['button_b'], #notused on left joycon
                                "button_b":      sdl_mapping['button_a'], #notused on left joycon
                                "button_x":      sdl_mapping['button_y'], #notused on left joycon
                                "button_y":      sdl_mapping['button_x'], #notused on left joycon
                                "button_l":      sdl_mapping['button_l'], 
                                "button_r":      sdl_mapping['button_r'], #notused on left joycon
                                "button_plus":   sdl_mapping['button_plus'], #notused on left joycon
                                "button_minus":  sdl_mapping['button_minus'],
                                "button_sl":     sdl_mapping['button_sl'], 
                                "button_sr":     sdl_mapping['button_sr'],
                                "button_lstick": sdl_mapping['button_lstick'],
                                "button_rstick": sdl_mapping['button_rstick'], #notused on left joycon
                                "button_home":   sdl_mapping['button_home'],  #notused on left joycon
                                "button_screenshot": sdl_mapping['button_home'], #Added to left joycon to act as "home"
                                "button_dup":    sdl_mapping['button_x'], 
                                "button_ddown":  sdl_mapping['button_b'],
                                "button_dleft":  sdl_mapping['button_a'],
                                "button_dright": sdl_mapping['button_y'],
                                "button_zl": sdl_mapping['button_zl'],
                                "button_zr": sdl_mapping['button_zr'] #notused on left joycon
                            }
                        else:
                            yuzuButtons = {
                                "button_a":      sdl_mapping['button_a'], #notused on left joycon
                                "button_b":      sdl_mapping['button_b'], #notused on left joycon
                                "button_x":      sdl_mapping['button_x'], #notused on left joycon
                                "button_y":      sdl_mapping['button_y'], #notused on left joycon
                                "button_l":      sdl_mapping['button_l'], 
                                "button_r":      sdl_mapping['button_r'], #notused on left joycon
                                "button_plus":   sdl_mapping['button_plus'], #notused on left joycon
                                "button_minus":  sdl_mapping['button_minus'],
                                "button_sl":     sdl_mapping['button_sl'], 
                                "button_sr":     sdl_mapping['button_sr'],
                                "button_lstick": sdl_mapping['button_lstick'],
                                "button_rstick": sdl_mapping['button_rstick'], #notused on left joycon
                                "button_home":   sdl_mapping['button_home'],  #notused on left joycon
                                "button_screenshot": sdl_mapping['button_home'], #Added to left joycon to act as "home"
                                "button_dup":    sdl_mapping['button_y'], 
                                "button_ddown":  sdl_mapping['button_a'],
                                "button_dleft":  sdl_mapping['button_b'],
                                "button_dright": sdl_mapping['button_x'],
                                "button_zl": sdl_mapping['button_zl'],
                                "button_zr": sdl_mapping['button_zr'] #notused on left joycon
                            }

                        yuzuAxis = {
                            "lstick":    int(sdl_mapping['axis_lstick_x']),
                            "rstick":    int(sdl_mapping['axis_rstick_x'])
                        }

                        yuzuAxisButtons = {
                            "button_zl": sdl_mapping['axis_button_zl'],
                            "button_zr": sdl_mapping['axis_button_zr']
                        }

                        yuzuHat = {
                            "button_dup":     'up',
                            "button_ddown":   'down',
                            "button_dleft":   'left',
                            "button_dright":  'right'
                        }

                        #Configure buttons and triggers
                        for x in yuzuButtons:
                            if("hat" in str(yuzuButtons[x])):
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"{},direction:{},guid:{},port:{},engine:sdl"'.format(yuzuButtons[x],yuzuHat[x],inputguid,portnumber))
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x + "\\default", "false")

                            elif("axis" in str(yuzuButtons[x])):
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"engine:sdl,invert:+,port:{},guid:{},axis:{},threshold:0.500000"'.format(portnumber,inputguid,yuzuAxisButtons[x]))
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x + "\\default", "false")

                            else:
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"button:{},guid:{},port:{},engine:sdl"'.format(yuzuButtons[x],inputguid,portnumber))
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x + "\\default", "false")

                        #set joysticks
                        for x in yuzuAxis:
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"engine:sdl,port:{},guid:{},axis_x:{},offset_x:-0.011750,axis_y:{},offset_y:-0.027467,invert_x:-,invert_y:+,deadzone:0.150000,range:0.950000"'.format(portnumber,inputguid,yuzuAxis[x]+1,yuzuAxis[x]))
                    elif (system.isOptSet(which_pad) and (system.config[which_pad] == "3")):
                        eslog.debug("Controller Type: Right Joycon")
                        #2 = Left Joycon
                        #Switch and generic controllers aren't swapping ABXY
                        if (sdl_mapping['type'] == 0):
                            yuzuButtons = {
                                "button_a":      sdl_mapping['button_a'], #was b
                                "button_b":      sdl_mapping['button_x'], #was a
                                "button_x":      sdl_mapping['button_b'], #was y
                                "button_y":      sdl_mapping['button_y'], #was x
                                "button_l":      sdl_mapping['button_l'], #notused on right joycon
                                "button_r":      sdl_mapping['button_r'],
                                "button_plus":   sdl_mapping['button_plus'],
                                "button_minus":  sdl_mapping['button_minus'], #notused on right joycon
                                "button_sl":     sdl_mapping['button_sl'], 
                                "button_sr":     sdl_mapping['button_sr'],
                                "button_lstick": sdl_mapping['button_lstick'], #notused on right joycon
                                "button_rstick": sdl_mapping['button_lstick'], #mapping to left stick
                                "button_home":   sdl_mapping['button_home'], 
                                #"button_screenshot": sdl_mapping['button_home'],
                                "button_dup":    sdl_mapping['button_x'],  #notused on right joycon
                                "button_ddown":  sdl_mapping['button_b'], #notused on right joycon
                                "button_dleft":  sdl_mapping['button_a'], #notused on right joycon
                                "button_dright": sdl_mapping['button_y'], #notused on right joycon
                                "button_zl": sdl_mapping['button_zl'], #notused on right joycon
                                "button_zr": sdl_mapping['button_zr'] 
                            }
                        else:
                            yuzuButtons = {
                                "button_a":      sdl_mapping['button_b'], 
                                "button_b":      sdl_mapping['button_y'],
                                "button_x":      sdl_mapping['button_a'],
                                "button_y":      sdl_mapping['button_x'],
                                "button_l":      sdl_mapping['button_l'], #notused on right joycon
                                "button_r":      sdl_mapping['button_r'],
                                "button_plus":   sdl_mapping['button_plus'],
                                "button_minus":  sdl_mapping['button_minus'], #notused on right joycon
                                "button_sl":     sdl_mapping['button_sl'], 
                                "button_sr":     sdl_mapping['button_sr'],
                                "button_lstick": sdl_mapping['button_lstick'], #notused on right joycon
                                "button_rstick": sdl_mapping['button_lstick'], #mapping to left stick
                                "button_home":   sdl_mapping['button_home'], 
                                #"button_screenshot": sdl_mapping['button_home'],
                                "button_dup":    sdl_mapping['button_x'],  #notused on right joycon
                                "button_ddown":  sdl_mapping['button_b'], #notused on right joycon
                                "button_dleft":  sdl_mapping['button_a'], #notused on right joycon
                                "button_dright": sdl_mapping['button_y'], #notused on right joycon
                                "button_zl": sdl_mapping['button_zl'], #notused on right joycon
                                "button_zr": sdl_mapping['button_zr'] 
                            }

                        yuzuAxis = {
                            "lstick":    int(sdl_mapping['axis_lstick_x']), #notused on right joycon
                            "rstick":    int(sdl_mapping['axis_lstick_x']) #mapping to left stick
                        }

                        yuzuAxisButtons = {
                            "button_zl": sdl_mapping['axis_button_zl'],
                            "button_zr": sdl_mapping['axis_button_zr']
                        }

                        yuzuHat = {
                            "button_dup":     'up',
                            "button_ddown":   'down',
                            "button_dleft":   'left',
                            "button_dright":  'right'
                        }

                        #Configure buttons and triggers
                        for x in yuzuButtons:
                            if("hat" in str(yuzuButtons[x])):
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"{},direction:{},guid:{},port:{},engine:sdl"'.format(yuzuButtons[x],yuzuHat[x],inputguid,portnumber))
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x + "\\default", "false")
                            elif("axis" in str(yuzuButtons[x])):
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"engine:sdl,invert:+,port:{},guid:{},axis:{},threshold:0.500000"'.format(portnumber,inputguid,yuzuAxisButtons[x]))
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x + "\\default", "false")
                            else:
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"button:{},guid:{},port:{},engine:sdl"'.format(yuzuButtons[x],inputguid,portnumber))
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x + "\\default", "false")

                        #set joysticks
                        for x in yuzuAxis:
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"engine:sdl,port:{},guid:{},axis_x:{},offset_x:-0.011750,axis_y:{},offset_y:-0.027467,invert_x:+,invert_y:-,deadzone:0.150000,range:0.950000"'.format(portnumber,inputguid,yuzuAxis[x]+1,yuzuAxis[x]))
                            
                    else:
                        #0 = Pro Controller, 1 = Dual Joycons, 4 = Handheld Mode,  (and other cases not yet defined)
                        #Switch and generic controllers aren't swapping ABXY
                        if (sdl_mapping['type'] == 0):
                            yuzuButtons = {
                                "button_a":      sdl_mapping['button_b'],
                                "button_b":      sdl_mapping['button_a'],
                                "button_x":      sdl_mapping['button_y'],
                                "button_y":      sdl_mapping['button_x'],
                                "button_l":      sdl_mapping['button_l'],
                                "button_r":      sdl_mapping['button_r'],
                                "button_plus":   sdl_mapping['button_plus'],
                                "button_minus":  sdl_mapping['button_minus'],
                                "button_sl":     sdl_mapping['button_sl'],
                                "button_sr":     sdl_mapping['button_sr'],
                                "button_lstick": sdl_mapping['button_lstick'],
                                "button_rstick": sdl_mapping['button_rstick'],
                                "button_home":   sdl_mapping['button_home'],
                                "button_dup":    sdl_mapping['button_dup'],
                                "button_ddown":  sdl_mapping['button_ddown'],
                                "button_dleft":  sdl_mapping['button_dleft'],
                                "button_dright": sdl_mapping['button_dright'],
                                "button_zl": sdl_mapping['button_zl'],
                                "button_zr": sdl_mapping['button_zr']
                            }
                        else:
                            yuzuButtons = {
                                "button_a":      sdl_mapping['button_a'],
                                "button_b":      sdl_mapping['button_b'],
                                "button_x":      sdl_mapping['button_x'],
                                "button_y":      sdl_mapping['button_y'],
                                "button_l":      sdl_mapping['button_l'],
                                "button_r":      sdl_mapping['button_r'],
                                "button_plus":   sdl_mapping['button_plus'],
                                "button_minus":  sdl_mapping['button_minus'],
                                "button_sl":     sdl_mapping['button_sl'],
                                "button_sr":     sdl_mapping['button_sr'],
                                "button_lstick": sdl_mapping['button_lstick'],
                                "button_rstick": sdl_mapping['button_rstick'],
                                "button_home":   sdl_mapping['button_home'],
                                "button_dup":    sdl_mapping['button_dup'],
                                "button_ddown":  sdl_mapping['button_ddown'],
                                "button_dleft":  sdl_mapping['button_dleft'],
                                "button_dright": sdl_mapping['button_dright'],
                                "button_zl": sdl_mapping['button_zl'],
                                "button_zr": sdl_mapping['button_zr']
                            }

                        yuzuAxis = {
                            "lstick":    int(sdl_mapping['axis_lstick_x']),
                            "rstick":    int(sdl_mapping['axis_rstick_x'])
                        }

                        yuzuAxisButtons = {
                            "button_zl": sdl_mapping['axis_button_zl'],
                            "button_zr": sdl_mapping['axis_button_zr']
                        }

                        yuzuHat = {
                            "button_dup":     'up',
                            "button_ddown":   'down',
                            "button_dleft":   'left',
                            "button_dright":  'right'
                        }

                        #Configure buttons and triggers
                        for x in yuzuButtons:
                            if("hat" in str(yuzuButtons[x])):
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"{},direction:{},guid:{},port:{},engine:sdl"'.format(yuzuButtons[x],yuzuHat[x],inputguid,portnumber))
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x + "\\default", "false")
                            elif("axis" in str(yuzuButtons[x])):
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"engine:sdl,invert:+,port:{},guid:{},axis:{},threshold:0.500000"'.format(portnumber,inputguid,yuzuAxisButtons[x]))
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x + "\\default", "false")
                            else:
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"button:{},guid:{},port:{},engine:sdl"'.format(yuzuButtons[x],inputguid,portnumber))
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x + "\\default", "false")

                        #set joysticks
                        for x in yuzuAxis:
                                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '"engine:sdl,port:{},guid:{},axis_x:{},offset_x:-0.011750,axis_y:{},offset_y:-0.027467,invert_x:+,invert_y:+,deadzone:0.150000,range:0.950000"'.format(portnumber,inputguid,yuzuAxis[x],yuzuAxis[x]+1))
                                    


                    #Enable motion no matter what, as enabling won't hurt things if it doesn't exist
                    yuzu_config.set("Controls", "player_" + controllernumber + "_motionleft", '"engine:sdl,motion:0,port:{},guid:{}"'.format(portnumber,inputguid))
                    yuzu_config.set("Controls", "player_" + controllernumber + "_motionright", '"engine:sdl,motion:0,port:{},guid:{}"'.format(portnumber,inputguid))

                    yuzu_config.set("Controls", "player_" + controllernumber + "_connected", "true")
                    if (controllernumber == "0"):
                        yuzu_config.set("Controls", "player_" + controllernumber + "_connected\\default", "true")
                    else:
                        yuzu_config.set("Controls", "player_" + controllernumber + "_connected\\default", "false")

                    if system.isOptSet(which_pad):
                        yuzu_config.set("Controls", "player_" + controllernumber + "_type", system.config["p1_pad"])
                        #yuzu_config.set("Controls", "player_0_type", system.config["p1_pad"])
                    else:
                        yuzu_config.set("Controls", "player_" + controllernumber + "_type", "0")


                    yuzu_config.set("Controls", "player_" + controllernumber + "_button_screenshot", "[empty]")
                    yuzu_config.set("Controls", "player_" + controllernumber + "_button_screenshot\\default", "false")
                    yuzu_config.set("Controls", "player_" + controllernumber + "_type\\default", "true")


                    if system.isOptSet("yuzu_enable_rumble"):
                        yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled", system.config["yuzu_enable_rumble"])
                        yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled\\default", system.config["yuzu_enable_rumble"])
                    else:
                        yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled", "true")
                        yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled\\default", "true")

                    lastplayer = int(controllernumber) + 1

        
        
        #lastplayer = lastplayer + 1
        eslog.debug("Last Player {}".format(lastplayer))
        for y in range(lastplayer, 9):
            controllernumber = str(y)
            eslog.debug("Setting Controller: {}".format(controllernumber))
            for x in yuzuButtons:
                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '""')
            for x in yuzuAxis:
                yuzu_config.set("Controls", "player_" + controllernumber + "_" + x, '""')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_a", '"toggle:0,code:67,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_a\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_b", '"toggle:0,code:88,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_b\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_ddown", '"toggle:0,code:16777237,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_ddown\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_dleft", '"toggle:0,code:16777234,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_dleft\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_dright", '"toggle:0,code:16777236,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_dright\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_dup", '"toggle:0,code:16777235,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_dup\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_home", '"toggle:0,code:0,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_home\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_l", '"toggle:0,code:81,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_l\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_lstick", '"toggle:0,code:70,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_lstick\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_minus", '"toggle:0,code:78,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_minus\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_plus", '"toggle:0,code:77,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_plus\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_r", '"toggle:0,code:69,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_r\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_rstick", '"toggle:0,code:71,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_rstick\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_screenshot", '"toggle:0,code:0,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_screenshot\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_sl", '"toggle:0,code:81,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_sl\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_sr", '"toggle:0,code:69,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_sr\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_x", '"toggle:0,code:86,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_x\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_y", '"toggle:0,code:90,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_y\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_zl", '"toggle:0,code:82,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_zl\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_zr", '"toggle:0,code:84,engine:keyboard"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_button_zr\\default", "true")

            yuzu_config.set("Controls", "player_" + controllernumber + "_lstick", '"modifier_scale:0.500000,modifier:toggle$00$1code$016777248$1engine$0keyboard,right:toggle$00$1code$068$1engine$0keyboard,left:toggle$00$1code$065$1engine$0keyboard,down:toggle$00$1code$083$1engine$0keyboard,up:toggle$00$1code$087$1engine$0keyboard,engine:analog_from_button"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_lstick\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_rstick", '"modifier_scale:0.500000,modifier:toggle$00$1code$00$1engine$0keyboard,right:toggle$00$1code$076$1engine$0keyboard,left:toggle$00$1code$074$1engine$0keyboard,down:toggle$00$1code$075$1engine$0keyboard,up:toggle$00$1code$073$1engine$0keyboard,engine:analog_from_button"')
            yuzu_config.set("Controls", "player_" + controllernumber + "_rstick\\default", "true")


            yuzu_config.set("Controls", "player_" + controllernumber + "_connected", "false")
            yuzu_config.set("Controls", "player_" + controllernumber + "_connected\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_type", "0")
            yuzu_config.set("Controls", "player_" + controllernumber + "_type\\default", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled", "true")
            yuzu_config.set("Controls", "player_" + controllernumber + "_vibration_enabled\\default", "true")
    
    with open(yuzu_config_file, 'w') as configfile:
        eslog.debug("Writing controls to config")
        yuzu_config.write(configfile)

@staticmethod
def setButton(key, padGuid, padInputs,controllernumber):

    # it would be better to pass the joystick num instead of the guid because 2 joysticks may have the same guid
    if key in padInputs:
        input = padInputs[key]
        #eslog.debug("Mapping: {}".format(input))

        if input.type == "button":
            return ("button:{},guid:{},port:{},engine:sdl").format(input.id, padGuid, controllernumber)
        elif input.type == "hat":
            return ("hat:{},direction:{},guid:{},port:{},engine:sdl").format(input.id, hatdirectionvalue(input.value), padGuid, controllernumber)
        elif input.type == 'axis':
            return ("threshold:0.500000,axis:{},pad:0,port:{},guid:{},engine:sdl").format(input.id, controllernumber, padGuid)

@staticmethod
def setAxis(key, padGuid, padInputs,controllernumber, axisReversed):
    inputx = -1
    inputy = -1

    if key == "joystick1":
        try:
            inputx = padInputs["joystick1left"]
        except:
            inputx = ["0"]
    elif key == "joystick2":
        try:
            inputx = padInputs["joystick2left"]
        except:
            inputx = ["0"]

    if key == "joystick1":
        try:
            inputy = padInputs["joystick1up"]
        except:
            inputy = ["0"]
    elif key == "joystick2":
        try:
            inputy = padInputs["joystick2up"]
        except:
            inputy = ["0"]

    if(axisReversed == 1):
        #Left Joycon
        try:
            return ("engine:sdl,port:{},guid:{},axis_x:{},offset_x:-0.011750,axis_y:{},offset_y:-0.027467,invert_x:-,invert_y:+,deadzone:0.150000,range:0.950000").format(controllernumber, padGuid, inputy.id, inputx.id)
        except:
            return ("0")
    if(axisReversed == 2):
        #Right Joycon
        try:
            return ("engine:sdl,port:{},guid:{},axis_x:{},offset_x:-0.011750,axis_y:{},offset_y:-0.027467,invert_x:+,invert_y:1,deadzone:0.150000,range:0.950000").format(controllernumber, padGuid, inputy.id, inputx.id)
        except:
            return ("0")
    else:
        try:
            return ("engine:sdl,port:{},guid:{},axis_x:{},offset_x:-0.011750,axis_y:{},offset_y:-0.027467,invert_x:+,invert_y:+,deadzone:0.150000,range:0.950000").format(controllernumber, padGuid, inputx.id, inputy.id)
        except:
            return ("0")

@staticmethod
def hatdirectionvalue(value):
    if int(value) == 1:
        return "up"
    if int(value) == 4:
        return "down"
    if int(value) == 2:
        return "right"
    if int(value) == 8:
        return "left"
    return "unknown"