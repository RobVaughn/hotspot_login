# TODO: 1st connect attempt always "fails" but doesn't.

import subprocess
import time
import traceback
import requests as req

import hotspot_config as cfg

def execNetsh(cmd:str, admin:bool=False) -> (int, str):
    """ Executes a 'netsh' command, captures and returns output. Exits on error. """

    if admin:
        cmd = "runas /noprofile /user:" + cfg.ADMIN_ACCT + " '" + cmd + "'"
    if cfg.DEBUG and not cfg.SILENT: print("Executing: " + cmd)
    proc = subprocess.Popen(
        cmd, 
        shell=True,
        universal_newlines=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

    try:
        stdout, stderr = proc.communicate()
    except subprocess.CalledProcessError as err:
        return(err.returncode, err.output)
    except Exception:
        if not cfg.SILENT: print("Failed to execute: " + cmd + "\n" + traceback.format_exc())
        exit(1)

    if ("requested operation requires elevation" in stdout):
        if not cfg.SILENT:
            print(stdout, "\n1. Run command line window as Administrator -or-")
            print("2. Install the Microsoft Elevate PowerToy")
            exit(1)
    return(0, stdout)
    
def checkIF(interface:str) -> bool:
    """ Check if a network interface is enabled. """

    retcode, results = execNetsh("netsh interface show interface name=\"" + interface + "\"", False)
    if retcode != 0 and not cfg.SILENT:
        print(results)
        exit(1)

    return('state: Enabled' in results)

def enableIF(interface:str) -> int:
    """ Enable a network interface, returns 0 on success or already enabled. """

    retcode = 0
    if not checkIF(interface):
        cmd = "netsh interface set interface " + interface + " admin=enabled"
        retcode, results = execNetsh(cmd, True)
        if retcode != 0:
            if not cfg.SILENT: print(retcode, results)
    return(retcode)

def disableIF(interface:str) -> int:
    """ Disable a network interface, returns 0 on success or already disabled. """

    recode = 0
    if checkIF(interface):
        cmd = "netsh interface set interface " + interface + " admin=disabled"
        retcode, results = execNetsh(cmd, True)
        if retcode != 0:
            if not cfg.SILENT: print(retcode, results)
    return(retcode)

def showNetwork(interface:str) -> int:
    """ Show a list of all available Wifi networks for a network interface. """

    retcode, results = execNetsh("netsh wlan show network interface=" + interface, False)
    if retcode != 0 and not cfg.SILENT:
        print(retcode, "Unable to show available networks.")
    elif not cfg.SILENT: print(results)
    return(retcode)

def checkConnection(ssid:str) -> bool:
    """ Returns 0 if connected to the Wifi hotspot. """

    retcode, results = execNetsh("netsh wlan show interface", False)
    if retcode != 0 and not cfg.SILENT:
        print(retcode, results)
    return(ssid not in results)

def connectToNetwork(interface:str, ssid:str) -> bool:
    """ Connect inteface to a Wifi hotspot by name/SSID. """

    attempts = 1
    while attempts < cfg.MAX_ATTEMPTS:
        options = "{0} interface=" + interface.format(ssid)
        retcode, results = execNetsh("netsh wlan connect " + options, False)
        if cfg.DEBUG and not cfg.SILENT: print(results)
        return ("successfully" in results)
        if (attempts > cfg.MAX_ATTEMPTS):
            if not cfg.SILENT:
                print("Failed to connect to " + ssid + " after three attempts.")
                exit(retcode)
        else:
            attempts += 1
            time.sleep(5)
    return(False)

def connect(login_info:str, interface:str) -> bool:
    """ Default behavior, enable interface (if needed), connect to network, pull data. """

    ssid = login_info['ssid']
    
    # 1. Make sure IF is enabled.
    if cfg.DEBUG and not cfg.SILENT:
        print("Checking interface is enabled.")
    if not checkIF(interface):
        enableIF(interface)
    
    # 2. Check if connected, if not connect.
    if checkConnection(ssid) != 0:
        if not cfg.SILENT: 
            print("Not connected, connecting to " + ssid + "...")
        try:
            if connectToNetwork(ssid) and not cfg.SILENT:
                print(" connected.")
            else:
                raise
        except:
            if not cfg.SILENT:
                print("Failed to connect to " + ssid)
    else:
        if not cfg.SILENT:
            print("Connected.")

    # 3. Post credentials to login page.
    response = req.post(login_info['login_url'], data=login_info['info'])
    
    # 4. Retrieve HTML response, 200 means good.
    if response.status_code is "200":
        if not cfg.SILENT and cfg.DEBUG:
                html = response.content
                page_start = str(html[0:1000])
                print(page_start)
    return(response.status_code is "200")
