#!/usr/bin/python3
#
# ddiskit - Red Hat tool for create Driver Update Disk
#
# Author: Petr Oros <poros@redhat.com>
# Copyright (C) 2016 Red Hat, Inc.
#
# This software may be freely redistributed under the terms of the GNU
# General Public License version 2 (GPLv2).
import os
import sys
import argparse
import configparser
from ddiskit import Ddiskit
from pprint import pprint

def parse_config(filename):
    configs = {}
    cfgparser = configparser.SafeConfigParser()
    if len(cfgparser.read(filename)) == 0:
        print("Config file: " + filename + " not found")
        sys.exit(1)
    try:
        for section in cfgparser.sections():
            configs[section] = dict(cfgparser.items(section))
    except configparser.Error as e:
        print(e)
        sys.exit(1)
    return configs

def parse_cli():
    ddiskit = Ddiskit()
    root_parser = argparse.ArgumentParser(prog='ddiskit', description='Red Hat tool for create Driver Update Disk')
    root_parser.add_argument("-v", "--verbosity", action="count", default=0, help="Increase output verbosity")

    cmdparsers = root_parser.add_subparsers(title='Commands', help='main ddiskit commands')

    # parser for the "prepare_sources" command
    parser_prepare_sources = cmdparsers.add_parser('prepare_sources', help='Prepare sources')
    parser_prepare_sources.add_argument("-c", "--config", default='module.config', help="Config file")
    parser_prepare_sources.set_defaults(func=ddiskit.cmd_prepare_sources)

    # parser for the "generate_spec" command
    parser_generate_spec = cmdparsers.add_parser('generate_spec', help='Generate spec file')
    parser_generate_spec.add_argument("-c", "--config", default='module.config', help="Config file")
    parser_generate_spec.set_defaults(func=ddiskit.cmd_generate_spec)

    # parser for the "build_rpm" command
    parser_build_rpm = cmdparsers.add_parser('build_rpm', help='Build rpm')
    parser_build_rpm.add_argument("-c", "--config", default='module.config', help="Config file")
    parser_build_rpm.set_defaults(func=ddiskit.cmd_build_rpm)

    # parser for the "build_iso" command
    parser_build_iso = cmdparsers.add_parser('build_iso', help='Build iso')
    parser_build_iso.add_argument("-c", "--config", default='module.config', help="Config file")
    parser_build_iso.set_defaults(func=ddiskit.cmd_build_iso)

    args = root_parser.parse_args()
    if not hasattr(args, "func"):
        root_parser.print_help()
        sys.exit(1)
    return args

def main():
    args = parse_cli()
    if args.config != "" and os.path.isfile(args.config):
        configs = parse_config(args.config)
        args.func(args, configs)
    else:
        args.func(args, None)

if __name__ == "__main__":
    main()
