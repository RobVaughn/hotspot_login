# TODO print("Figure out admin priv stuff")
# TODO Check all funcs return() correct args / error codes
# 0	success
# 1	general error
# 2	usage error
# 3	execute error, traceback results printed
# 4	invalid network interace (adapter)
# 5     login failed

import subprocess
import time
import traceback
import re
import requests as req

import hotspot_config as cfg

def adminMsg(out):
    """ Error message when admin privs are required. """

    cfg.exitMsg(out + "Admin privileges are required. Either:\n" +
                "1. Run command line window as Administrator -or-\n" +
                "2. Install the Microsoft Elevate PowerToy")

def runCmd(cmd) -> (int, str, str):
    """ Executes a shell level command. """

    stdout = ""
    stderr = ""
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
        cfg.debugOut(err.returncode, err.output, err.error)
        return(err.returncode, err.output, err.error)
    except Exception:
        cfg.exitMsg("Failed to execute: " + cmd + "\n" + traceback.format_exc(), 3)
    return(proc.returncode, stdout, stderr)

def execShell(cmd:str, admin:bool=False, strip:bool=True) -> (int, str):
    """ Linux command line execution. Exits on error. """

    if admin:
        cmd = "/bin/sudo " + cmd
    cfg.debugOut(out="Executing: " + cmd)
    retcode, stdout, stderr = runCmd(cmd)
    cfg.debugOut(retcode, stdout, stderr)

    if ("requested operation requires elevation" in stdout):
        adminMsg(stdout)

    if strip: stdout = stdout.replace("\n", "")
    return(proc.returncode, stdout.replace("\r", ""))

def execWin(shellcmd:str, cmd:str, admin:bool=False, strip:bool=True) -> (int, str):
    """ Executes a shell command, captures and returns output. Exits on error. """

    if shellcmd is "Netsh":
        cmd = "netsh " + cmd
    else:
        cmd = "powershell.exe " + cmd

    if admin and not cfg.ADMIN: adminMsg("")
    cfg.debugOut(out="Executing: " + cmd)
    retcode, stdout, stderr = runCmd(cmd)
    cfg.debugOut(retcode, stdout, stderr)

    if ('requested operation requires elevation' in stdout): adminMsg(stdout)
    if strip: stdout = stdout.replace("\n", "")
    return(retcode, stdout.replace("\r", ""))

def hotspotLogin(login_info) -> bool:
    """ Post to login page, check results. """

    response = req.post(login_info['login_url'], data=login_info['info'])
    if response.status_code == 200:
        html = response.content
        cfg.debugOut(out=str(html[0:1000]))
    return(response.status_code == 200)

#
# API
#

def checkIF(interface:str=cfg.IF) -> bool:
    """ Check if a network interface is enabled. """

    retcode = 0
    if cfg.OS is "Windows":
        if cfg.EXEC is "Netsh":
            cmd = "interface show interface name=\"" + interface + "\""
            retcode, results = execWin(cfg.EXEC, cmd)
            if re.search(r'state:\sEnabled', results) is not None: return(True)
        elif cfg.EXEC is "PowerShell":
            cmd = "Get-NetAdapter -Name " + interface + " | Format-List -Property Status"
            retcode, results = execWin(cfg.EXEC, cmd)
            # TODO: finish PS
            return('Status : Up' in results)
    elif cfg.OS is "Linux":
        retcode, results = execShell("iw " + cfg.IF + " scan", admin=True)
        if ('is up' in results) or retcode == 0: return(True)
    else: cfg.exitMsg(cfg.OS + " platform not supported.", 3)
    return(False)

def enableIF(interface:str=cfg.IF) -> int:
    """ Enable a network interface, returns 0 on success or already enabled. """

    retcode = 0
    if not checkIF(interface):
        if cfg.OS is "Windows":
            if cfg.EXEC is "Netsh":
                cmd = "interface set interface " + interface + " admin=enabled"
            elif cfg.EXEC is "PowerShell":
                cmd = "Enable-NetAdapter -Name \"" + interface + "\" -Confirm:$false"
            retcode, results = execWin(cfg.EXEC, cmd, admin=True)
        elif cfg.OS is "Linux":
            retcode, results = execShell("ifconfig " + interface + " up", admin=True)
        else: cfg.exitMsg(cfg.OS + " platform not supported.", 3)
    return(retcode)

def disableIF(interface:str=cfg.IF) -> int:
    """ Disable a network interface, returns 0 on success or already disabled. """

    retcode = 0
    if checkIF(interface):
        if cfg.OS is "Windows":
            if cfg.EXEC is "Netsh":
                cmd = "interface set interface " + interface + " admin=disabled"
            elif cfg.EXEC is "PowerShell":
                cmd = "Disable-NetAdapter -Name \"" + interface + "\" -Confirm:$false"
            retcode, results = execWin(cfg.EXEC, cmd, admin=True)
        elif cfg.OS is "Linux":
            retcode, results = execShell("ifconfig " + interface + " down", admin=True)
        else: cfg.exitMsg(cfg.OS + " platform not supported.", 3)
    return(retcode)

def resetIF(interface:str=cfg.IF) -> int:
    """ Resets a network interface. """

    retcode = 0
    if cfg.OS is "Windows":
        if cfg.EXEC is "Netsh":
            cmd = "winsock reset"
        elif cfg.EXEC is "PowerShell":
            cmd = "Restart-NetAdapter -Name \"" + interface + "\" -Confirm:$false"
        retcode, results = execWin(cfg.EXEC, cmd, admin=True)
    elif cfg.OS is "Linux":
        retcode, results = execShell("ifconfig " + interface + " reset", admin=True)
    else: cfg.exitMsg(cfg.OS + " platform not supported.", 3)

    cfg.debugOut(out=results)
    return(retcode)
    
def getNetworks(interface:str=cfg.IF) -> (int, str):
    """ Return a list of all available Wifi networks for a network interface. """

    retcode = 0
    # No native PowerShell method to show networks, so use 'netsh' on Windows.
    if cfg.OS is "Windows":
        cmd = "wlan show network interface=" + interface
        retcode, results = execWin("Netsh", cmd, strip=False)
        if "no such wireless interface" in results:
            # TODO
            #cfg.infoMsg(results.replace("\n", ""))
            return(4, results)
    elif cfg.OS is "Linux":
        retcode, results = execShell(cmd, strip=False)
        print("TODO: Linux show network.")
    else: cfg.exitMsg(cfg.OS + " platform not supported.", 3)

    if retcode != 0:
        return(1, "Unable to retrieve list of available networks.")
    return(retcode, results)

def getBlocklist() -> (int, str):
    """ Get a list of all blocked SSIDs (filtered from network list.) """

    retcode = 0
    # TODO? No native PowerShell method to show networks, so use 'netsh' on Windows.
    if cfg.OS is "Windows":
        cmd = "wlan show filters permission=block"
        retcode, results = execWin("Netsh", cmd, strip=False)
    elif cfg.OS is "Linux":
        retcode, results = execShell(cmd, strip=False)
        print("TODO: Linux show blocklist.")
    else: cfg.exitMsg(cfg.OS + " platform not supported.", 3)

    if retcode != 0:
        return(1, "Unable to retrieve list of blocked networks.")
    return(retcode, results)

def addBlocklist(ssid:str, force=False) -> bool:
    """ Adds an SSID to the block list so it's not displayed. """

    retcode = 0
    retcode, results = getNetworks()
    if retcode != 0:
        cfg.exitMsg("Unable to retrieve a list of networks.", 1)
    if re.search(r'SSID\s+[0-9+]\s:\s' + ssid + '\n', results) is None and not force:
        return(False)

    retcode = 0
    # TODO? No native PowerShell method to show networks, so use 'netsh' on Windows.
    if cfg.OS is "Windows":
        cmd = "wlan add filter permission=block ssid=\"" + ssid + "\" networktype=infrastructure"
        retcode, results = execWin("Netsh", cmd, admin=True)
    elif cfg.OS is "Linux":
        retcode, results = execShell(cmd)
        print("TODO: Linux add blocklist.")
    else: cfg.exitMsg(cfg.OS + " platform not supported.", 3)

    if retcode != 0:
        cfg.exitMsg("Unable to add " + ssid + " to block list.", 1)

    cfg.debugOut(out=results)
    return(True)

def delBlocklist(ssid:str) -> bool:
    """ Removes an SSID from the block list. """

    retcode, results = getBlocklist()
    if retcode != 0:
        cfg.exitMsg("Unable to retrieve the block list.", 1)
    if re.search(r'SSID:\s+\"'+ ssid, results) is None:
        return(False)

    retcode = 0
    # TODO? No native PowerShell method to show networks, so use 'netsh' on Windows.
    if cfg.OS is "Windows":
        cmd = "wlan delete filter permission=block ssid=\"" + ssid + "\" networktype=infrastructure"
        retcode, results = execWin("Netsh", cmd, admin=True)
    elif cfg.OS is "Linux":
        retcode, results = execShell(cmd)
        print("TODO: Linux add blocklist.")
    else: cfg.exitMsg(cfg.OS + " platform not supported.", 3)

    if retcode != 0:
        cfg.exitMsg("Unable to remove " + ssid + " from block list.", 1)

    cfg.debugOut(out=results)
    return(True)

def checkConnection(ssid:str) -> bool:
    """ Returns True if connected to the Wifi hotspot. """

    if cfg.OS is "Windows":
        if cfg.EXEC is "Netsh":
            cmd = "wlan show interface"
        elif cfg.EXEC is "PowerShell":
            cmd = "TODO"
        retcode, results = execWin(cfg.EXEC, cmd, strip=False)
        if retcode != 0: cfg.debugOut(retcode, out=results)
        if re.search(r'SSID\s+:\s+' + ssid + '\n', results) is not None:
            return(True)
    elif cfg.OS is "Linux":
        retcode, results = execShell("iw " + cfg.IF + " link")
        if re.search(r'^Connected', results) is None:
            return(True)
    else: cfg.exitMsg(cfg.OS + " platform not supported.", 3)
    return(False)

def connectToNetwork(interface:str, ssid:str) -> bool:
    """ Connect inteface to a Wifi hotspot by name/SSID, returns True on success. """

    attempts = 1
    options = "interface=\"" + interface + "\" " + ssid
    while attempts <= cfg.MAX_ATTEMPTS:
        if cfg.OS is "Windows":
            retcode, results = execWin(cfg.EXEC, "wlan connect " + options)
        elif cfg.OS is "Linux":
            retcode, results = execShell("TODO" + options)
        else: cfg.exitMsg(cfg.OS + " platform not supported.", 3)
            
        cfg.debugOut(retcode, out=results)
        time.sleep(cfg.NAPTIME)

        if cfg.OS is "Windows" and cfg.EXEC is "Netsh":
            if "completed successfully" in results: return(True)
            elif "There is no profile" in results:
                cfg.infoMsg(results)
                return(False)
        elif cfg.OS is "Windows" and cfg.EXEC is "PowerShell":
            print("TODO: PS connect to network.")
        elif cfg.OS is "Linux":
            print("TODO: Linux connect to network.")
        else: cfg.exitMsg(cfg.OS + " platform not supported.", 3)

        attempts += 1

    cfg.infoMsg("Failed to connect to " + ssid + " after three attempts.")
    return(False)

def connect(login_info:str, interface:str) -> bool:
    """ Default behavior, enable interface (if needed), connect to network, pull data. """

    try:
        ssid = login_info['ssid']
    except KeyError:
        cfg.exitMsg("Unknown hotspot.")
    except:
        cfg.exitMsg("Invalid SSID / hotspot")

    cfg.debugOut(out="1. Checking interface is enabled.")
    if enableIF(interface) is not 0:
        cfg.infoMsg("Invalid interface: " + interface)
        return(False)

    cfg.debugOut(out="2. Checking if connected to a hotspot.")
    if not checkConnection(ssid):
        cfg.debugOut(out="Not connected, connecting to " + ssid + "...")
        success = connectToNetwork(interface, ssid)
        if success: cfg.infoMsg("Connected successfully.")
        else: return(False)

    cfg.debugOut(out="3. Logging into hotspot.")
    if hotspotLogin(login_info): return(True)
    return(False)
