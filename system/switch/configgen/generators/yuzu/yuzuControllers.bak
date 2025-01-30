from __future__ import annotations

import xml.etree.cElementTree as ET
from typing import TYPE_CHECKING, Any

import pyudev

from configgen.batoceraPaths import mkdir_if_not_exists
from .yuzuPaths import YUZU_CONTROLLER_PROFILES

if TYPE_CHECKING:
    from pathlib import Path
    from configgen.controller import Controller, ControllerMapping
    from configgen.Emulator import Emulator


def generateControllerConfig(system: Emulator, playersControllers: ControllerMapping) -> None:
    # -= Switch controller types =-
    PRO = "Pro Controller"
    # TODO
    # Add other controller types

    API_SDL = "SDLController"

    DEFAULT_DEADZONE = '0.25'
    DEFAULT_RANGE = '1'

    buttonMappingsSDL = {
        PRO: {
            "1":  "1",
            "2":  "0",
            "3":  "3",
            "4":  "2",
            "5":  "9",
            "6":  "10",
            "7":  "42",
            "8":  "43",
            "9":  "6",
            "10": "4",
            # 11 is excluded
            "12": "11",
            "13": "12",
            "14": "13",
            "15": "14",
            "16": "7",
            "17": "8",
            "18": "45",
            "19": "39",
            "20": "44",
            "21": "38",
            "22": "47",
            "23": "41",
            "24": "46",
            "25": "40"
        }
    }
    
    def getOption(option: str, defaultValue: str) -> Any:
        if (system.isOptSet(option)):
            return system.config[option]
        else:
            return defaultValue

    def addTextElement(parent: ET.Element, name: str, value: str) -> None:
        element = ET.SubElement(parent, name)
        element.text = value

    def addAnalogControl(parent: ET.Element, name: str) -> None:
        element = ET.SubElement(parent, name)
        addTextElement(element, "deadzone", DEFAULT_DEADZONE)
        addTextElement(element, "range", DEFAULT_RANGE)

    def getConfigFileName(controller: int) -> Path:
        return YUZU_CONTROLLER_PROFILES / f"controller{controller}.xml"
    
    # Make controller directory if it doesn't exist
    mkdir_if_not_exists(YUZU_CONTROLLER_PROFILES)

    # Purge old controller files
    for counter in range(0,8):
        configFileName = getConfigFileName(counter)
        if configFileName.is_file():
            configFileName.unlink()

    ## CONTROLLER: Create the config xml files
    nplayer = 0

    # cemu assign pads by uuid then by index with the same uuid
    # so, if 2 pads have the same uuid, the index is not 0 but 1 for the 2nd one
    # sort pads by index
    pads_by_index = playersControllers
    dict(sorted(pads_by_index.items(), key=lambda kv: kv[1].index))
    guid_n: dict[int, int] = {}
    guid_count: dict[str, int] = {}
    for _, pad in pads_by_index.items():
        if pad.guid in guid_count:
            guid_count[pad.guid] += 1
        else:
            guid_count[pad.guid] = 0
        guid_n[pad.index] = guid_count[pad.guid]
    ###

    for playercontroller, pad in sorted(playersControllers.items()):
        root = ET.Element("emulated_controller")

        # Set type from controller combination
        type = PRO # default
        # TODO
        # Add other controller types
        
        addTextElement(root, "type", type)

        api = API_SDL

        # Create controller configuration
        controllerNode = ET.SubElement(root, 'controller')
        addTextElement(controllerNode, 'api', api)
        addTextElement(controllerNode, 'uuid', "{}_{}".format(guid_n[pad.index], pad.guid)) # controller guid
        addTextElement(controllerNode, 'display_name', pad.real_name) # controller name
        addTextElement(controllerNode, 'rumble', getOption('yuzu_enable_rumble', '0')) # % chosen
        addAnalogControl(controllerNode, 'axis')
        addAnalogControl(controllerNode, 'rotation')
        addAnalogControl(controllerNode, 'trigger')

        # Apply the appropriate button mappings
        mappingsNode = ET.SubElement(controllerNode, "mappings")
        mapping = buttonMappingsSDL[type]
        for key, value in mapping.items():
            entryNode = ET.SubElement(mappingsNode, "entry")
            addTextElement(entryNode, "mapping", key)
            addTextElement(entryNode, "button", value)

        # Save to file
        with getConfigFileName(nplayer).open('wb') as handle:
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ", level=0)
            tree.write(handle, encoding='UTF-8', xml_declaration=True)
            handle.close()

        nplayer+=1