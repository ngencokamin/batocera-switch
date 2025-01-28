# batocera-switch
## IMPORTANT NOTES
1. This script worked as-is up to Batocera 40, but broke in Batocera 41 due to changes in Batocera's Python path-handling and how imports work in the new version of Python that Batocera 41 uses. The main purpose of this fork is *specifically* to get batocera-switch working again on 41. I can't promise anything beyond that point.
2. Now that Batocera Pro is officially down + official downloads for Yuzu and Ryujinx have been removed, the easy install script no longer functions. I will be working on a new one after I have gotten this repository working on version 41.
3. Due to not wanting Nintendo to pile-driver me into dust with the force of 10,000 suns, you will have to provide your own copies of the Yuzu and/or Ryujinx binaries. Please do not ask me for them, or ask me where to find them. I believe in you.
4. This is ***only*** for x86_64 builds of Batocera.

## General
Extends Batocera and adds switch emulation as an UNSUPPORTED ADD-ON to BATOCERA.  

Master branch is tested and currently working on Batocera 37-40. If you have v35 or lower, please upgrade Batocera as we are no longer supporting these versions.

This version of the code requires a file system for userdata that supports symlinking (EXT4, BTRFS) and is for x86_64 only!!  

This version integrates work from foclabroc, Batocera Nation, and uureel.  It does not include the bios keys.  

Autoconfiguration of controllers is now handled via [pySDL](https://github.com/py-sdl/py-sdl2) and some python magic.

## Support
Feel free to open a GitHub issue if you need support and I will do my best to help out.

## TODO
- [x] Update README

- [x ] Add support for Batocera 41
  - [ x ] Update to use `batoceraPaths` not that `batoceraFiles` has been fully removed
  - [ x ] Update imports to not break with new Python version
  - [ ] Make sure I didn't break older versions
- [ x ] Update/create new easy install method now that Batocera Pro is deprecated
- [ ] Require user provide their own emulator binaries so Nintendo doesn't nuke me into oblivion

## EASY INSTALL

#### No easy install method for right now, will work on it next

~~From a terminal window, run the following:<br>~~
~~```curl -L switch.batocera.pro | bash```~~

~~After installing, place your prod.keys and title.keys in /share/bios/switch/  
If you wish to use Ryujinx you will also need to supply the firmware zip file~~~



## UPGRADING OLDER VERSIONS OF THIS ADD-ON NOT INSTALLED WITH THE EASY INSTALL METHOD
Delete the `/userdata/system/switch` folder and install this repo as normal.  There are folders in the old install that will break this version.  

## REPORTING ISSUES
Please use the controller issue templates for reporting controller issues.  For other issues, provide as much information as possible, and if it's a launch issue, please be sure to include the full outputs of the `/userdata/system/logs/es_launch_stdout.log` and `/userdata/system/logs/es_launch_stderr.log` log files. Also, please note that I am not the original author of this code, so my help will be slightly more limited for issues outside of porting it to work with Batocera 41.

## SPECIAL THANKS
Huge thanks to [ordovis](https://github.com/ordovice) for creating the original repository. They did all the hard work.

Additionally, I don't want to remove any other credits, so from the original README:

> Special thanks for foclabroc, Rion, and Darknior and multiple members of the [Batocera Nation Discord](https://discord.gg/cuw5Xt7M7d) for testing things especially with the migration to SDL, [RGS] for a controller donation, and anyone else who contributes and helps me make this better. 

## HOW TO SHOW APPRECIATION
Feel free to [buy me a coffee](https://buymeacoffee.com/ngencokamin), shoot me a message via email or on matrix (@radioambush:beeper.com), or just by playing a game you love and enjoying it.

Additionally, if you want to support the person who did all the work *besides* making it work on Batocera 41, I am including a link to [ordovis' Paypal](https://www.paypal.com/paypalme/ordovice) as well.

## UPDATE 2023-06-28
Controller auto configuration has been migrated to the same versions of SDL that yuzu and ryujinx are using, utilizing the [pySDL project](https://github.com/py-sdl/py-sdl2).

