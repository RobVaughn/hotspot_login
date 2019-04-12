# hotspot_login
A network utility script to manage network interfaces and log into wi-fi hotspot if not connected, without opening your browser. You can enable, disable, reset and test network adapters, check if connected or logged in, show available hotspots and add/remove SSIDs to/from a blocklist. Blocked SSIDs aren't displayed when all are listed (helpful in areas with a lot of access points.)
```
# python .\hotspot_login.py -h
usage: hotspot_login.py [-h] [-q] [-f] [-v] [-t] [-s [SSID]] [-c [interface]]
                        [-e [interface]] [-d [interface]] [-r [interface]]
                        [-n [SSID]] [-b [SSID]] [-u [SSID]] [-bl]
                        ...

Hotspot Login Utility

positional arguments:
  [hotspot [interface]]
                        label for hotspot to connect to

optional arguments:
  -h, --help            show this help message and exit
  -q, --silent          supress all output
  -f, --force           force addition to block list
  -v, --debug           turn on debugging messages
  -t, --test            test if a hotspot is logged into
  -s [SSID], --show [SSID]
                        show available wifi networks
  -c [interface], --check [interface]
                        check if an interface is connected to a network
  -e [interface], --enable [interface]
                        enable a network interface
  -d [interface], --disable [interface]
                        disable a network interface
  -r [interface], --reset [interface]
                        reset a network interface
  -n [SSID], --connected [SSID]
                        check if connected to a hotspot
  -b [SSID], --block [SSID]
                        block a wifi network by SSID
  -u [SSID], --unblock [SSID]
                        unblock a wifi network by SSID
  -bl, --blocklist      show list of blocked SSIDs
  ```

Error Code | Cause
--- | -------------
0 | success
1 | general error
2 | usage error
3 | execute error, traceback results printed
4 | invalid network interace (adapter)
5 | hotspot login failed

Notes:

1. Warning: the unit tests for enableIF() and disableIF(), which change the state of the network interface, can cause some laptop adapters to lock up, such as the Qualcomm Atheros series, if cycled too quickly when testing. The 'runas' command to use Administrator account doesn't work for either accounts w/Admin privs or the Administrator account (if you have it enabled.) As such the tests:
   1. Require Administrator privs to run (PowerShell -> Run as Administrator.)
   1. Are disabled by default unless a flag is set to run them.

History:

A friend asked if I could write a script to connect his RaspPi to hotspot(s) automatically. Decided to start with a Windows version which I could use to connect to hotspots w/o using a browser (although Windows will sometimes automagically open a browser/tab and redirect to a login page.)

Started as just a small "POST login info" script but after looking at a lot of half-finished Python projects and modules, and finding few decent examples, it expanded into a more general CLI utility to handle clicking through lots of Windows menus to enable interfaces, etc.

Was going to use my standard 'getopt' module to handle the command line, which I may still add. Decided to go more 'Pythonic' and use the 'argparse' module. Unfortunately the documentation is poor, good usage examples are few, and it's in many ways overkill for handling some simple flags with optional arguments. The built-in 'help' functionality is nice but getting it to look right was far more trouble than it's worth, IMHO. Found far more comments like the above than example code, and I don't have much use for being able to automatically sum integers on the command line. I'll be writing a 'getopts' version to compare how much code is actually involved, using a standard module I'd written a year ago.

Ran into a couple Windows-specific rough patches: after deciding to standardize on the 'netsh' CLI util, I found it often didn't return non-zero exit codes on failure, and enabling/disabling an interface (something I need to do sometimes if I haven't rebooted my laptop in a few months) requires elevated status to Administrator. Tried using a 'runas' wrapper to run as my account w/admin perms, but this didn't work, nor did doing same with the Administrator account which I'd enabled. Only running in a cmd/Powershell window started with 'Run as Adminstrator' privs, or using the Microsoft Elevate PowerToy add-on, works.

Once I get the Windows version tested and a Linux port finished, I'll revisit the issue and try using WMI and/or Powershell commands instead.
