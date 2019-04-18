# TODO Check all funcs return() correct args / error codes

import subprocess
import time
import traceback
import re
import requests as req

import hotspot_config as cfg

def adminMsg(out=""):
    """ Error message when admin privs are required. """

    cfg.exitMsg(out + "Admin privileges are required. Either:\n" +
                "1. Run command line window as Administrator -or-\n" +
                "2. Install the Microsoft Elevate PowerToy", cfg.ERRORS['ADMINREQ'])

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
        cfg.exitMsg("Failed to execute: " + cmd + "\n" + traceback.format_exc(), cfg.ERRORS['WINONLY'])
    return(proc.returncode, stdout, stderr)

def execShell(cmd:str, admin:bool=False, strip:bool=True) -> (int, str, str):
    """ Linux command line execution. Exits on error. """

    if admin:
        cmd = "/usr/bin/sudo " + cmd
    cfg.debugOut(out="Executing: " + cmd)
    retcode, stdout, stderr = runCmd(cmd)
    cfg.debugOut(retcode, stdout, stderr)
    if strip:
        stdout = stdout.replace("\n", "")
        stderr = stderr.replace("\n", "")
    return(retcode, stdout, stderr)

def execWin(cmd:str, admin:bool=False, strip:bool=True) -> (int, str):
    """ Executes a shell command, captures and returns output. Exits on error. """

    if admin and not cfg.ADMIN: adminMsg()
    cfg.debugOut(out="Executing: netsh " + cmd)
    retcode, stdout, stderr = runCmd("netsh " + cmd)
    cfg.debugOut(retcode, stdout, stderr)

    if ('requested operation requires elevation' in stdout): adminMsg(stdout)
    if strip: stdout = stdout.replace("\n", "")
    return(retcode, stdout.replace("\r", ""), stderr.replace("\r", ""))

def hotspotLogin(login_info) -> bool:
    """ Post to login page, check results. """

    try:
        response = req.post(login_info['login_url'], data=login_info['info'])
    except:
        return(False)

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
    if cfg.OS == "Windows":
        retcode, out, err = execWin("interface show interface name=\"" + interface + "\"")
        if re.search(r'state:\sEnabled', out) is not None and retcode == 0: return(True)
    elif cfg.OS == "Linux":
        retcode, out, err = execShell("/sbin/ip link show " + interface + " up")
        if re.search(r'state UP', out) is not None and retcode == 0: return(True)
    else: cfg.exitMsg(cfg.OS + " platform not supported.", cfg.ERRORS['BADPLAT'])
    if retcode != 0: cfg.infoMsg(out + err)
    return(False)

def enableIF(interface:str=cfg.IF) -> int:
    """ Enable a network interface, returns 0 on success or already enabled. """

    if checkIF(interface): return(0)
    retcode = 0
    if cfg.OS == "Windows":
        cmd = "interface set interface " + interface + " admin=enabled"
        retcode, out, err = execWin(cmd, admin=True)
    elif cfg.OS == "Linux":
        retcode, out, err = execShell("/sbin/ifconfig " + interface + " up", admin=True)
    else: cfg.exitMsg(cfg.OS + " platform not supported.", cfg.ERRORS['BADPLAT'])

    cfg.debugOut(out=out, err=err)
    return(retcode)

def disableIF(interface:str=cfg.IF) -> int:
    """ Disable a network interface, returns 0 on success or already disabled. """

    if not checkIF(interface): return(0)
    retcode = 0
    if cfg.OS == "Windows":
        cmd = "interface set interface " + interface + " admin=disabled"
        retcode, out, err = execWin(cmd, admin=True)
    elif cfg.OS == "Linux":
        retcode, out, err = execShell("/sbin/ifconfig " + interface + " down", admin=True)
    else: cfg.exitMsg(cfg.OS + " platform not supported.", cfg.ERRORS['BADPLAT'])

    cfg.debugOut(out=out, err=err)
    return(retcode)

def resetIF(interface:str=cfg.IF) -> int:
    """ Resets a network interface. """

    if not checkIF(interface): return(1)
    retcode = 0
    if cfg.OS == "Windows":
        retcode, out, err = execWin("winsock reset", admin=True)
    elif cfg.OS == "Linux":
        retcode, out, err = execShell("systemctl restart networking", admin=True)
    else: cfg.exitMsg(cfg.OS + " platform not supported.", cfg.ERRORS['BADPLAT'])

    cfg.debugOut(out=out, err=err)
    return(retcode)
    
def getNetworks(interface:str=cfg.IF) -> (int, str):
    """ Return a list of all available Wifi networks for a network interface. """

    retcode = 0
    if cfg.OS == "Windows":
        cmd = "wlan show network interface=" + interface
        retcode, out, err = execWin(cmd, strip=False)
        if "no such wireless interface" in out: return(cfg.ERRORS['BADIF'], out)
    elif cfg.OS == "Linux":
        # Alt: iw dev [interface] station dump
        retcode, out, err = execShell("/sbin/iwlist " + interface + " scan")
        if retcode == 255:
            return(cfg.ERRORS['BADIF'], err)
    else: cfg.exitMsg(cfg.OS + " platform not supported.", cfg.ERRORS['BADPLAT'])

    if retcode != 0:
        return(1, "Unable to retrieve list of available networks.")
    cfg.debugOut(out=out, err=err)
    return(retcode, out)

def getBlocklist() -> (int, str, str):
    """ Get a list of all blocked SSIDs (filtered from network list.) """

    if cfg.OS != "Windows":
        cfg.exitMsg("SSID blocking only available on Windows.", cfg.ERRORS['WINONLY'])

    retcode = 0
    retcode, out, err = execWin("wlan show filters permission=block", strip=False)
    if retcode != 0:
        return(cfg.ERRORS['GENERAL'], out + err) # TODO? "Unable to retrieve list of blocked networks.")
    return(retcode, out, err)

def addBlocklist(ssid:str, force=False) -> bool:
    """ Adds an SSID to the block list so it's not displayed. """

    if cfg.OS != "Windows":
        cfg.exitMsg("SSID blocking only available on Windows.", cfg.ERRORS['WINONLY'])

    retcode = 0
    retcode, out = getNetworks()
    if retcode != 0:
        cfg.exitMsg("Unable to retrieve a list of networks.")
    if re.search(r'SSID\s+[0-9+]\s:\s' + ssid + '\n', out) is None and not force:
        return(False)

    retcode = 0
    cmd = "wlan add filter permission=block ssid=\"" + ssid + "\" networktype=infrastructure"
    retcode, out, err = execWin(cmd, admin=True)
    if retcode != 0:
        cfg.exitMsg(err) # TODO?"Unable to add " + ssid + " to block list.", 1)

    cfg.debugOut(out=out, err=err)
    return(True)

def delBlocklist(ssid:str) -> bool:
    """ Removes an SSID from the block list. """

    if cfg.OS != "Windows":
        cfg.exitMsg("SSID blocking only available on Windows.", cfg.ERRORS['WINONLY'])

    retcode = 0
    retcode, out = getBlocklist()
    if retcode != 0:
        cfg.exitMsg("Unable to retrieve the block list.")
    if re.search(r'SSID:\s+\"'+ ssid, out) is None:
        return(False)

    retcode = 0
    cmd = "wlan delete filter permission=block ssid=\"" + ssid + "\" networktype=infrastructure"
    retcode, out, err = execWin(cmd, admin=True)
    if retcode != 0:
        cfg.exitMsg(err) # TODO? "Unable to remove " + ssid + " from block list.", 1)

    cfg.debugOut(out=out, err=err)
    return(True)

def checkConnection(ssid:str) -> bool:
    """ Returns True if connected to the Wifi hotspot. """

    if cfg.OS == "Windows":
        retcode, out, err = execWin("wlan show interface", strip=False)
        if re.search(r'SSID\s+:\s+' + ssid + '\n', out) is not None and retcode == 0:
            return(True)
    elif cfg.OS == "Linux":
        retcode, out, err = execShell("/sbin/iw dev " + cfg.IF + " link")
        if re.search(r'^Connected', out) is not None and retcode == 0:
            return(True)
    else: cfg.exitMsg(cfg.OS + " platform not supported.", 3)
    if retcode != 0: cfg.infoMsg(out + err)
    return(False)

def connectToNetwork(ssid:str, interface:str=cfg.IF) -> bool:
    """ Connect inteface to a Wifi hotspot by name/SSID, returns True on success. """

    retcode = 0
    attempts = 1
    options = "interface=\"" + interface + "\" " + ssid
    while attempts <= cfg.MAX_ATTEMPTS:
        if cfg.OS == "Windows":
            retcode, out, err = execWin("wlan connect " + options)
            if "completed successfully" in out and retcode == 0: return(True)
        elif cfg.OS == "Linux":
            retcode, out, err = execShell("/sbin/iw " + interface + "connect -w " + ssid, admin=True)
            if retcode == 0: return(True)
        else: cfg.exitMsg(cfg.OS + " platform not supported.", 3)
            
        cfg.debugOut(retcode, out=out, err=err)
        time.sleep(cfg.NAPTIME)
        attempts += 1

    cfg.infoMsg("Failed to connect to " + ssid + " after three attempts.")
    return(False)

def disconnectFrom(interface:str=cfg.IF) -> bool:
    """ Disconnect a network interface from an access point. """

    if cfg.OS == "Windows":
        retcode, out, err = execWin("wlan disconnect interface=\"" + interface +"\"")
        if retcode != 0: cfg.debugOut(retcode, out=out, err=err)
        if re.search(r'request was completed successfully', out) is not None and retcode == 0:
            return(True)
    elif cfg.OS == "Linux":
        retcode, out, err = execShell("/sbin/iw dev " + cfg.IF + " disconnect", admin=True)
        if re.search(r'^Disconnected', out) is not None and retcode == 0:
            return(True)
    else: cfg.exitMsg(cfg.OS + " platform not supported.", 3)
    return(False)
    
def connect(login_info:str, interface:str=cfg.IF) -> bool:
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
        success = connectToNetwork(ssid, interface)
        if success: cfg.infoMsg("Connected successfully.")
        else: return(False)

    cfg.debugOut(out="3. Logging into hotspot.")
    if hotspotLogin(login_info): return(True)
    return(False)
