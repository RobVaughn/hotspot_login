# Script to connect automatically to a wifi hotspot. Could be expanded to auto login when
# in range.

import argparse
import os, ctypes

import hotspot_config as cfg
import hotspot_utils as utils

def main():
    parser = argparse.ArgumentParser(description='Hotspot Login Utility')
    parser.add_argument('hotspot',
                        nargs=argparse.REMAINDER,
                        metavar='[hotspot [interface]]',
                        help='label for hotspot to connect to')

    # True/false flags.
    parser.add_argument('-q', '--silent',
                        action='store_true',
                        default=False,
                        help='supress all output')
    parser.add_argument('-f', '--force',
                        action='store_true',
                        default=False,
                        help='force addition to block list')
    parser.add_argument('-v', '--debug',
                        action='store_true',
                        default=False,
                        help='turn on debugging messages')

    # Operation flags.
    parser.add_argument('-t', '--test',
                        nargs='?',
                        const=cfg.DEFAULT_LOGIN,
                        action='store',
                        metavar='hotspot',
                        dest='test',
                        type=str,
                        help='test if a hotspot is logged into')
    parser.add_argument('-s', '--show',
                        nargs='?',
                        const=cfg.IF,
                        action='store',
                        metavar='interface',
                        dest='show',
                        type=str,
                        help='show available wifi networks')
    parser.add_argument('-c', '--check',
                        nargs='?',
                        const=cfg.IF,
                        action='store',
                        dest='check',
                        metavar='interface',
                        type=str,
                        help='check if an interface is connected to a network')
    parser.add_argument('-e', '--enable',
                        nargs='?',
                        const=cfg.IF,
                        action='store',
                        dest='enable',
                        metavar='interface',
                        type=str,
                        help='enable a network interface')
    parser.add_argument('-d', '--disable',
                        nargs='?',
                        const=cfg.IF,
                        action='store',
                        dest='disable',
                        metavar='interface',
                        type=str,
                        help='disable a network interface')
    parser.add_argument('-r', '--reset',
                        nargs='?',
                        const=cfg.IF,
                        action='store',
                        dest='reset',
                        metavar='interface',
                        type=str,
                        help='reset a network interface')
    parser.add_argument('-n', '--connected',
                        nargs='?',
                        const=cfg.LOGIN_INFO[cfg.DEFAULT_LOGIN]['ssid'],
                        action='store',
                        dest='connected',
                        metavar='SSID',
                        type=str,
                        help='check if connected to a hotspot')
    parser.add_argument('-x', '--disconnect',
                        nargs='?',
                        const=cfg.IF,
                        action='store',
                        dest='disconnect',
                        metavar='interface',
                        type=str,
                        help='disconnect from a hotspot')
    parser.add_argument('-b', '--block',
                        nargs="?",
                        action='store',
                        dest='block',
                        metavar='SSID',
                        help='block a wifi network by SSID [Windows only]')
    parser.add_argument('-u', '--unblock',
                        nargs="?",
                        action='store',
                        dest='unblock',
                        metavar='SSID',
                        help='unblock a wifi network by SSID [Windows only]')
    parser.add_argument('-bl', '--blocklist',
                        action='store_true',
                        help='show list of blocked SSIDs [Windows only]')
    args = parser.parse_args()

    if (args.silent): cfg.SILENT = True
    if (args.debug): cfg.DEBUG = True
    if not cfg.SILENT and cfg.DEBUG: print(args)

    # $0 -t [hotspot]
    if args.test is not None:
        if not utils.hotspotLogin(cfg.LOGIN_INFO[args.test]):
            exit(5)
        exit(0)
        
    # $0 -s [interface]
    if args.show:
        retcode, results = utils.getNetworks(args.show)
        if not cfg.SILENT: print(results)
        exit(retcode)

    # $0 -c [interface]
    elif args.check:
        cfg.debugOut("args.check", args.check)
        if utils.checkIF(args.check):
            if not cfg.SILENT:
                print("Interface " + args.check + " is connected.")
                exit(0)
        if not cfg.SILENT: print("Interface " + args.check + " is not connected.")
        exit(1)

    # $0 -e [interface]
    elif args.enable:
        retcode = utils.enableIF(args.enable)
        if retcode == 0 and not cfg.SILENT: print("Interface " + args.enable + " is enabled.")
        elif not cfg.SILENT: print("Interface " + args.enable + " cannot be enabled.")
        exit(retcode)

    # $0 -d [interface]
    elif args.disable:
        retcode = utils.disableIF(args.disable)
        if retcode == 0 and not cfg.SILENT: print("Interface " + args.disable + " is disabled.")
        elif not cfg.SILENT: print("Interface " + args.disable + " cannot be disabled.")
        exit(retcode)

    # $0 -r [interface]
    elif args.reset:
        retcode = utils.resetIF(args.reset)
        if retcode == 0 and not cfg.SILENT: print("Interface " + args.reset + " has been reset.")
        elif not cfg.SILENT: print("Interface " + args.reset + " can't be reset.")
        exit(retcode)

    # $0 -n [interface]
    elif args.connected:
        if utils.checkConnection(args.connected):
            if not cfg.SILENT: print("Connected to " + args.connected + ".")
            exit(0)
        else:
            if not cfg.SILENT: print("Not connected to " + args.connected + ".")
        exit(1)

    # $0 -x [interface]
    elif args.disconnect:
        if utils.disconnectFrom(args.disconnect):
            if not cfg.SILENT: print("Disconnected " + args.disconnect + ".")
            exit(0)
        else:
            if not cfg.SILENT: print("Cannot disconnect " + args.disconnect + ".")
        exit(1)

    # TODO check these:
    # $0 [-f] -b [SSID]
    elif args.block is not None:
        if len(args.block) < 1 or len(args.block) > 1:
            cfg.exitMsg("Argparse shouldn't let this happen, one arg only.", 2)
        if utils.addBlocklist(args.block[0], args.force):
            cfg.exitMsg("Added " + args.block[0] + " to block list.", 0)
        else:
            cfg.exitMsg("Unable to find " + args.block[0] + " in the network list.", 1)

    # $0 [-f] -u [interface]
    elif args.unblock is not None:
        if len(args.unblock) < 1 or len(args.unblock) > 1:
            cfg.exitMsg("Argparse shouldn't let this happen, one arg only.", 2)
        if utils.delBlocklist(args.unblock[0]):
            cfg.exitMsg("Removed " + args.unblock[0] + " from block list.", 0)
        else:
            cfg.exitMsg("Unable to find " + args.unblock[0] + " in the block list.", 1)

    # $0 -bl
    elif args.blocklist:
        retcode, results = utils.getBlocklist()
        if not cfg.SILENT: print(results)
        exit(retcode)

    # Default usage: $0 [hotspot] [-i [interface]]
    else:
        hotspot = cfg.DEFAULT_LOGIN
        interface = cfg.IF
        if len(args.hotspot) > 0:
            hotspot = args.hotspot[0]
        if len(args.hotspot) > 1:
            interface = args.hotspot[1]

        try:
            success = utils.connect(cfg.LOGIN_INFO[hotspot], interface)
        except KeyError:
            print("Unknown hotspot: " + hotspot)
            exit(1)
        except: exit(2)

        if success and not cfg.SILENT:
            print("Logged in.")
            exit(0)
        else: exit(5)

    if not cfg.SILENT: parser.print_help()
    exit(1)

if __name__ == '__main__':
    try:
        cfg.ADMIN = os.getuid() == 0
    except AttributeError:
        cfg.ADMIN = ctypes.windll.shell32.IsUserAnAdmin() != 0
    if cfg.ADMIN and cfg.OS is "Windows":
        cfg.ADMIN_ACCT = "Administrator"
    elif cfg.ADMIN and cfg.OS is "Linux":
        cfg.ADMIN_ACCT = "root"
    
    if cfg.DEBUG and not cfg.SILENT: print("OS:", cfg.OS, "Admin: ", cfg.ADMIN)

    main()
