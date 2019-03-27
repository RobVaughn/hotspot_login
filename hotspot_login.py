# Script to connect automatically to a wifi hotspot. Could be expanded to save a list of
# hotspots, user/password combos for lookup to auto login when in range.

import argparse

import hotspot_config as cfg
import hotspot_utils as utils

def main():

    parser = argparse.ArgumentParser(description='Hotspot Login Utility')
    parser.add_argument('hotspot',
                        nargs=argparse.REMAINDER,
                        default=None,
                        metavar='ssid',
                        help='SSID of hotspot to connect to')
    parser.add_argument('-q', '--silent',
                        action='store_true',
                        default=False)
    parser.add_argument('-s', '--show',
                        nargs=argparse.REMAINDER,
                        default=None,
                        metavar='interface',
                        help='show available wifi networks')
    parser.add_argument('-c', '--check',
                        nargs=argparse.REMAINDER,
                        default=None,
                        metavar='interface',
                        help='check if an interface is connected to a network')
    parser.add_argument('-e', '--enable',
                        nargs=argparse.REMAINDER,
                        default=None,
                        help='enable a network interface')
    parser.add_argument('-d', '--disable',
                        nargs=argparse.REMAINDER,
                        default=None,
                        help='disable a network interface')
    parser.add_argument('-n', '--connected',
                        nargs=argparse.REMAINDER,
                        default=None,
                        metavar='SSID',
                        help='check if connected to a hotspot')
    args = parser.parse_args()
    if cfg.DEBUG and not cfg.SILENT: print(args)

    if (args.silent):
        cfg.SILENT = True

    if args.show is not None:
        if len(args.show) == 0: interface = cfg.IF
        else: interface = args.show[0]
        exit(utils.showNetwork(interface))

    elif args.check is not None:
        if len(args.check) == 0: interface = cfg.IF
        else: interface = args.check[0]

        response = "Interface " + interface
        connected = utils.checkIF(interface)
        if not connected: response += " not"
        if not cfg.SILENT: print(response + " connected.")

        if connected: exit(0)
        else: exit(1)

    elif args.enable is not None:
        if len(args.enable) == 0: interface = cfg.IF
        else: interface = args.enable[0]
        response = "Interface " + interface + " is"
        retcode = utils.enableIF(interface)
        if retcode == 0:
            if not cfg.SILENT: print(response, "enabled.")
        else:
            if not cfg.SILENT: print(response, "disabled.")
        exit(retcode)

    elif args.disable is not None:
        if len(args.disable) == 0: interface = cfg.IF
        else: interface = args.disable[0]
        return(utils.disableIF(interface))

    elif args.connected is not None:
        if len(args.connected) == 0:
            ssid = cfg.LOGIN_INFO[cfg.DEFAULT_LOGIN]['ssid']
        else:
            ssid = args.connected[0]
        retcode = utils.checkConnection(ssid)
        if retcode == 0:
            if not cfg.SILENT: print("Connected to: " + ssid)
        else:
            if not cfg.SILENT: print("Not connected to: " + ssid)
        exit(retcode)

    else:
        if len(args.hotspot) <= 1:
            hotspot = cfg.DEFAULT_LOGIN
            interface = cfg.IF
        elif len(args.hotspot) > 1:
            hotspot = args.hotspot[0]
            flag = args.hotspot[1]
            if flag != "-i" and flag != "--interface" or len(args.hotspot) != 3 and not cfg.SILENT:
                parser.print_help()
                exit(1)
            if len(args.hotspot) == 3:
                interface = args.hotspot[2]
            else:
                interface = cfg.IF
        
        exit(utils.connect(cfg.LOGIN_INFO[hotspot], interface))

    if not cfg.SILENT: parser.print_help()
    exit(1)

if __name__ == '__main__':
    main()
