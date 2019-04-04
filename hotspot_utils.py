import subprocess
import time
import traceback
import re
import requests as req

import hotspot_config as cfg

def debugOut(msg:str) -> None:
    """ Checks if debugging is on and silent mode off, prints message. """

    if cfg.DEBUG and not cfg.SILENT:
        print(msg)

def execNetsh(cmd:str, admin:bool=False, strip:bool=True) -> (int, str):
    """ Executes a 'netsh' command, captures and returns output. Exits on error. """

    if admin:
        cmd = "runas /noprofile /user:" + cfg.ADMIN_ACCT + " '" + cmd + "'"
    debugOut("Executing: " + cmd)
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
        debugOut(err.returncode, err.output)
        return(err.returncode, err.output)
    except Exception:
        debugOut("Failed to execute: " + cmd + "\n" + traceback.format_exc())
        exit(8)

    if ("requested operation requires elevation" in stdout) and not cfg.SILENT:
            print(stdout + "1. Run command line window as Administrator -or-")
            print("2. Install the Microsoft Elevate PowerToy")
            exit(1)

    if strip: stdout = stdout.replace("\n", "")
    return(proc.returncode, stdout.replace("\r", ""))
    
def checkIF(interface:str=cfg.IF) -> bool:
    """ Check if a network interface is enabled. """

    cmd = "netsh interface show interface name=\"" + interface + "\""
    retcode, results = execNetsh(cmd)
    if retcode != 0: debugOut(results)
    return('state: Enabled' in results)

def enableIF(interface:str=cfg.IF) -> int:
    """ Enable a network interface, returns 0 on success or already enabled. """

    retcode = 0
    if not checkIF(interface):
        cmd = "netsh interface set interface " + interface + " admin=enabled"
        retcode, results = execNetsh(cmd)
    return(retcode)

def disableIF(interface:str=cfg.IF) -> int:
    """ Disable a network interface, returns 0 on success or already disabled. """

    retcode = 0
    if checkIF(interface):
        cmd = "netsh interface set interface " + interface + " admin=disabled"
        retcode, results = execNetsh(cmd)
    return(retcode)

def showNetwork(interface:str=cfg.IF) -> int:
    """ Show a list of all available Wifi networks for a network interface. """

    cmd = "netsh wlan show network interface=" + interface
    retcode, results = execNetsh(cmd, strip=False)
    if "no such wireless interface" in results:
        if not cfg.SILENT: print(results.replace("\n", ""))
        return(1)
    elif retcode != 0 and not cfg.SILENT:
        print("Unable to show available networks.")

    if not cfg.SILENT: print(results)
    return(retcode)

def checkConnection(ssid:str) -> bool:
    """ Returns 0 if connected to the Wifi hotspot. """

    cmd = "netsh wlan show interface"
    retcode, results = execNetsh(cmd, strip=False)
    if retcode != 0: debugOut(str(retcode) + " " + results)
    if re.search(r'SSID\s+:\s' + ssid + '\n' , results) is None:
        return(False)
    return(True)

def connectToNetwork(interface:str, ssid:str) -> bool:
    """ Connect inteface to a Wifi hotspot by name/SSID. """

    attempts = 1
    options = "interface=\"" + interface + "\" " + ssid
    while attempts <= cfg.MAX_ATTEMPTS:
        retcode, results = execNetsh("netsh wlan connect " + options)
        debugOut(str(retcode) + " " + results)
        time.sleep(5)
        if "completed successfully" in results: return(True)
        if "There is no profile" in results:
            if not cfg.SILENT: print(results)
            return(False)
        attempts += 1

    debugOut("Failed to connect to " + ssid + " after three attempts.")
    return(False)

def connect(login_info:str, interface:str) -> bool:
    """ Default behavior, enable interface (if needed), connect to network, pull data. """

    try:
        ssid = login_info['ssid']
    except KeyError:
        if not cfg.SILENT: print("Unknown hotspot.")
        exit(1)
    except: exit(2)

    # 1. Make sure IF is enabled.
    debugOut("Checking interface is enabled.")
    if enableIF(interface) is not 0:
        if not cfg.SILENT:
            print("Invalid interface: " + interface)
        return(False)
    
    # 2. Check if connected, if not connect.
    if not checkConnection(ssid):
        debugOut("Not connected, connecting to " + ssid + "...")
        success = connectToNetwork(interface, ssid)
        if success and not cfg.SILENT:
            print("Connected successfully.")
        else: return(False)

    # 3. Post credentials to login page.
    response = req.post(login_info['login_url'], data=login_info['info'])
    
    # 4. Retrieve HTML response, 200 means good.
    if response.status_code == 200:
        html = response.content
        debugOut(str(html[0:1000]))
    return(response.status_code == 200)
