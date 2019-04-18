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
    parser.add_argument('-s', '--show',
                        nargs='?',
                        const=cfg.IF,
                        action='store',
                        metavar='interface',
                        dest='show',
                        type=str,
                        help='show available wifi networks')
    parser.add_argument('-t', '--test',
                        nargs='?',
                        const=cfg.DEFAULT_LOGIN,
                        action='store',
                        metavar='hotspot',
                        dest='test',
                        type=str,
                        help='test if a hotspot is logged into')
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
    cfg.debugOut(args)

    # $0 -s [interface]
    if args.show:
        retcode, results = utils.getNetworks(args.show)
        cfg.exitMsg(results, retcode)

    # $0 -t [hotspot]
    elif args.test is not None:
        try:
            login_info = cfg.LOGIN_INFO[args.test]
        except KeyError:
            cfg.exitMsg("Unknown hotspot " + args.test, cfg.ERRORS['USAGE'])
        except:
            cfg.exitMsg("Invalid usage.", cfg.ERRORS['USAGE'])

        if not utils.hotspotLogin(login_info):
            cfg.exitMsg("Not logged into " + login_info['ssid'], cfg.ERRORS['LOGINFAIL'])
        cfg.exitMsg("Logged into " + login_info['ssid'], cfg.ERRORS['SUCCESS'])
        
    # $0 -c [interface]
    elif args.check:
        if utils.checkIF(args.check):
            cfg.exitMsg("Interface " + args.check + " is connected.", cfg.ERRORS['SUCCESS'])
        cfg.exitMsg("Interface " + args.check + " is not connected.", cfg.ERRORS['GENERAL'])

    # $0 -e [interface]
    elif args.enable:
        retcode = utils.enableIF(args.enable)
        if retcode == 0:
            cfg.exitMsg("Interface " + args.enable + " is enabled.", retcode)
        cfg.exitMsg("Interface " + args.enable + " cannot be enabled.", retcode)

    # $0 -d [interface]
    elif args.disable:
        retcode = utils.disableIF(args.disable)
        if retcode == 0:
            cfg.exitMsg("Interface " + args.disable + " is disabled.", retcode)
        cfg.exitMsg("Interface " + args.disable + " cannot be disabled.", retcode)

    # $0 -r [interface]
    elif args.reset:
        retcode = utils.resetIF(args.reset)
        if retcode == 0:
            cfg.exitMsg("Interface " + args.reset + " has been reset.", retcode)
        cfg.exitMsg("Interface " + args.reset + " can't be reset.", retcode)

    # $0 -n [interface]
    elif args.connected:
        if utils.checkConnection(args.connected):
            cfg.exitMsg("Connected to " + args.connected + ".", cfg.ERRORS['SUCCESS'])
        cfg.exitMsg("Not connected to " + args.connected + ".", cfg.ERRORS['GENERAL'])

    # $0 -x [interface]
    elif args.disconnect:
        if utils.disconnectFrom(args.disconnect):
            cfg.exitMsg("Disconnected " + args.disconnect + ".", cfg.ERRORS['SUCCESS'])
        cfg.exitMsg("Cannot disconnect " + args.disconnect + ".", cfg.ERRORS['GENERAL'])

    # $0 [-f] -b [SSID]
    elif args.block is not None:
        if utils.addBlocklist(args.block, args.force):
            cfg.exitMsg("Added " + args.block + " to block list.", cfg.ERRORS['SUCCESS'])
        cfg.exitMsg("Unable to find " + args.block + " in the network list.", cfg.ERRORS['GENERAL'])

    # $0 [-f] -u [interface]
    elif args.unblock is not None:
        if utils.delBlocklist(args.unblock):
            cfg.exitMsg("Removed " + args.unblock + " from block list.", cfg.ERRORS['SUCCESS'])
        cfg.exitMsg("Unable to find " + args.unblock + " in the block list.", cfg.ERRORS['GENERAL'])

    # $0 -bl
    elif args.blocklist:
        retcode, out, err = utils.getBlocklist()
        cfg.exitMsg(out + err, retcode)

    # Default usage: $0 [hotspot] [-i [interface]]
    hotspot = cfg.DEFAULT_LOGIN
    interface = cfg.IF
    if len(args.hotspot) > 0:
        hotspot = args.hotspot[0]
    if len(args.hotspot) > 1:
        interface = args.hotspot[1]

    try:
        success = utils.connect(cfg.LOGIN_INFO[hotspot], interface)
    except KeyError:
        cfg.exitMsg("Unknown hotspot: " + hotspot, cfg.ERRORS['GENERAL'])
    except: exit(cfg.ERRORS['USAGE'])

    if success:
        cfg.exitMsg("Logged in.", cfg.ERRORS['SUCCESS'])
    else: exit(cfg.ERRORS['LOGINFAIL'])

    cfg.exitMsg(parser.print_help(), cfg.ERRORS['USAGE'])

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
