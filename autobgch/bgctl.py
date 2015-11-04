#!/usr/bin/python3
import os, sys
import argparse

from autobgch.bgch_libs.ipc_util import *
from autobgch.bgch_libs.misc_util import *
from autobgch.bgch_libs.bgch_core import *
from autobgch.bgch_libs.daemon_util import *

def run():
    if not is_daemon_start(pidfile):
        print('bgchd is not running')
        sys.exit(0)

    arg_to_ipccmd = {'play':IpcCmd.IPC_PLAY, 'pause':IpcCmd.IPC_PAUSE, 'next':IpcCmd.IPC_NEXT, \
        'prev':IpcCmd.IPC_PREV, 'info':IpcCmd.IPC_INFO, 'config':IpcCmd.IPC_CONFIG}

    parser = argparse.ArgumentParser(description='controller program for bgchd')
    arggrp = parser.add_mutually_exclusive_group(required=True)
    arggrp.add_argument('-play', action='store_true', help='start playing')
    arggrp.add_argument('-pause', action='store_true', help='pause playing')
    arggrp.add_argument('-next', action='store_true', help='next wallpaper')
    arggrp.add_argument('-prev', action='store_true', help='previous wallpaper')
    arggrp.add_argument('-info', action='store_true', help='get current info of bgchd')
    arggrp.add_argument('-config', action='store_true', \
        help='change config of bgchd. ex. bgctl -config -dir BG_DIR -intv MIN_OR_SEC. check bgctl -config -h for detail')

    pargs = parser.parse_args(sys.argv[1:2])
    args_d = vars(pargs)
    cmd = ''
    for k in args_d.keys():
        if args_d[k] == True:
            cmd = k
            break

    if cmd == 'config':
        # create additional parser for config
        conf_parser = argparse.ArgumentParser(\
            usage='bgctl -config -dir BG_DIR -intv MIN_OR_SEC')
        conf_parser.add_argument('-dir', dest='bg_dir', type=str, help='wallpaper directory')
        conf_parser.add_argument('-intv', dest='intv', type=str, metavar='MIN_OR_SEC', \
            help='interval of changing wallpaper(i.e. 10s or 5m)')
        conf_args = conf_parser.parse_args(sys.argv[2:])
        if conf_args.bg_dir is None and conf_args.intv is None:
            print('you have to specify one of -dir and -intv at least')
            sys.exit(1)

        bg_dir = conf_args.bg_dir if conf_args.bg_dir is not None else ''
        intv = conf_args.intv if conf_args.intv is not None else ''

        data = '{0},{1}'.format(bg_dir, intv)
        payload = Payload(CMD=arg_to_ipccmd[cmd], DATA=data)
    else:
        if len(sys.argv) > 2:
            print('{0} doesn\'t support these arguments: {1}'.format(cmd, sys.argv[2:]))
            sys.exit(1)

        payload = payload = Payload(CMD=arg_to_ipccmd[cmd], DATA='')

    try:
        res_msg = send_ipcmsg_to_sv(payload)
    except Exception as err:
        print('Error: {0}'.format(err))
        print('bgchd is busy')
        sys.exit(1)
    else:
        res_p = get_payload_obj_from_ipcmsg(res_msg)

    if cmd == 'info':
        status, bgdir, cur_img, intv = res_p.DATA.split(',')

        status = int(status)
        if Stat(status) is Stat.PLAY:
            status = 'Playing'
        elif Stat(status) is Stat.PAUSE:
            status = 'Paused'

        print('Status: {0}'.format(status))
        print('Wallpaper Directory: {0}'.format(bgdir))
        print('Current Wallpaper: {0}'.format(cur_img))
        print('Interval: {0}'.format(intv))
    else:
        print(res_p.DATA)

if __name__ == '__main__':
    run()