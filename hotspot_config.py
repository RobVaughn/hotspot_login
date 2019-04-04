# Hotspot Login Configuration.
#
# DEBUG: Debug flag, set to True prints information.
# SILENT: Silent operation, True surpresses all output.
# MAX_ATTEMPTS: maximum number of attempts to connect to a hotspot.
# IF: interface to use by default in case of multiple.
#
# HOTSPOT_SSID: name of the hotspot used to connect if necessary.
# HOTSPOT_URL: URL for the hotspot login page.
# HOTSPOT_DEFAULT: default dictionary entry for hotspot if not specified on command line.
# LOGIN_INFO: indexed by a shorthand name, each entry must contain:
#   1. The SSID of the hotspot as 'ssid'.
#   2. The URL of the login page to authentic w/the hotspot.
#   3. All the input fields for the login page (check page source for field names.) The
#      first entry is the default when not specified on the command line. The submit button
#      might be superfluous but doesn't hurt to have.

from collections import OrderedDict

DEBUG = False
SILENT = False

MAX_ATTEMPTS = 3
IF = 'Wi-Fi'
ADMIN_ACCT = 'Administrator'
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
