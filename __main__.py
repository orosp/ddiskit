#!/usr/bin/python
#
# ddiskit - Red Hat tool for create Driver Update Disk
#
# Author: Petr Oros <poros@redhat.com>
# Copyright (C) 2016 Red Hat, Inc.
#
# This software may be freely redistributed under the terms of the GNU
# General Public License version 2 (GPLv2).
import sys
import argparse
from pprint import pprint

def parser_cli():
    root_parser = argparse.ArgumentParser(prog='ddiskit', description='Red Hat tool for create Driver Update Disk')
    root_parser.add_argument("-v", "--verbosity", action="count", default=0, help="Increase output verbosity")

    cmdparsers = root_parser.add_subparsers(title='Commands')

    # parser for the "generate_spec" command
    parser_generate_spec = cmdparsers.add_parser('generate_spec', help='Generate spec file')
    parser_generate_spec.add_argument("-c", "--config", default='', help="Config file")

    # parser for the "build_rpm" command
    parser_build_rpm = cmdparsers.add_parser('build_rpm', help='Build rpm')
    parser_build_rpm.add_argument("-c", "--config", default='', help="Config file")

    # parser for the "build_iso" command
    parser_build_iso = cmdparsers.add_parser('build_iso', help='Build iso')
    parser_build_iso.add_argument("-c", "--config", default='', help="Config file")

    args = root_parser.parse_args()
    return args

def main():
    args = parser_cli()
    pprint(args)
    sys.exit(1)

if __name__ == "__main__":
    main()
