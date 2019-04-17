# Hotspot Login Configuration.
#
# DEBUG: Debug flag, set to True prints information.
# SILENT: Silent operation, True surpresses all output.
# TESTING: If set to True, uses a default network interface for Vbox testing.
#
# MAX_ATTEMPTS: maximum number of attempts to connect to a hotspot.
# NAPTIME: wait time before retrying to connect in seconds.
#
# DEFAULT_LOGIN: default LOGIN_INFO entry.
# LOGIN_INFO: indexed by a shorthand name, each entry must contain:
#   1. The SSID of the hotspot as 'ssid'.
#   2. The URL of the login page to authentic w/the hotspot.
#   3. All the input fields for the login page (check page source for field names.) The
#      first entry is the default when not specified on the command line. The submit button
#      might be superfluous but doesn't hurt to have.

import platform, subprocess, re
from collections import OrderedDict

DEBUG = False
SILENT = False
TESTING = True

MAX_ATTEMPTS = 3
NAPTIME = 5

DEFAULT_LOGIN='svi'
LOGIN_INFO = OrderedDict()
LOGIN_INFO['svi'] = {
    "ssid": "SuperValueInn",
    "login_url": "http://10.1.1.1:8002/index.php?zone=mtrx",
    "info": {
        "zone": "mtrx",
        "redirurl": "http://gizmodo.com",
        "auth_user": "super",
        "auth_pass": "password",
        "accept": "submit" }
}
LOGIN_INFO['ecafe'] = {
    "ssid": "RedECafe",
    "login_url": "http://10.0.0.1/login.php",
    "info": {
        "username": "ecafe",
        "password": "coffeeisgood",
        "login": "submit" }
}
LOGIN_INFO['library'] = {
    "ssid": "MultCoLibrary-kenton",
    "login_url": "http://multcolib.org/kenton/login/login.html",
    "info": {
        "library_branch": "kenton",
        "library_card": "12345678",
        "library_pin": "1234",
        "login": "submit" }
}
LOGIN_INFO['test'] = {
    "ssid": "NoSuchSSID",
    "login_url": "http://thissitedoesnotexistforcertain.com/login.html",
    "info": {
        "field1": "nonsense",
        "field2": "morenonsense" }
}

# Helper functions.

def debugOut(retcode:int=0, out:str=None, err:str=None) -> None:
    if DEBUG and not SILENT:
        print("DEBUG:", retcode, end='')
        if out is not None: print("\tstdout:", out)
        if err is not None: print("\tstderr:", err)

def infoMsg(msg:str) -> None:
    if not SILENT: print(msg)

def exitMsg(msg:str, retcode:int=1) -> None:
    """ Prints a message if not running silent, exits w/error code."""

    if not SILENT:
        print(msg)
        exit(retcode)

# Interface and operating system settings.

ADMIN = False
ADMIN_ACCT = None
OS = platform.system()
PLATFORM = platform.platform()

# TODO: these are overly simplistic approaches, could be much more thorough. For later.
if OS == "Windows":
    IF = 'Wi-Fi'
elif OS == "Linux":
    results = subprocess.check_output(['iw', 'dev'], shell=True)
    ifs = results.decode('ascii')
    regex = re.compile(r'wlan[0-9]\s')
    matches = regex.findall(ifs)
    if matches is None or TESTING:
        IF = "wlan0"
    else:
        IF = matches[0]
else:
    exitMsg("Unsupported operating system: "+ OS +", exiting.", 2)
debugOut("OS: "+ OS +" IF: " + IF) 
