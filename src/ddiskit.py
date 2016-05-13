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

class Ddiskit:
    def cmd_prepare_sources(self, args, configs):
        try:
            print("Writing new config file ... ", end="")
            if os.path.isfile(args.config):
                print("File Exist")
            else:
                with open('config', 'r') as fin:
                    read_data = fin.read()
                fin.close()
                fout = open(args.config, 'w')
                fout.write(read_data)
                fout.close()
                print("OK")
        except IOError as e:
            print(e.strerror)

        print("Creating directory structure for RPM build ... ", end="")
        try:
            os.makedirs("rpm")
            os.makedirs("rpm/SPEC")
            os.makedirs("rpm/SOURCE")
        except OSError as e:
            print(e.strerror)
        else:
            print("OK")
        print("Done")

    def cmd_generate_spec(self, args, configs):
        if len(configs) == 0:
            print(args.config, end="")
            print(" not found, use \"ddiskit prepare_sources\" for create")
            sys.exit(1)
        try:
            with open('../spec', 'r') as fin:
                read_data = fin.read()
                fin.close()
        except IOError as e:
            print(e.strerror)
        # apply global configs
        for content in configs["global"]:
            read_data = read_data.replace('"' + content[0].upper() + '"', content[1])

        # apply spec configs
        for content in configs["spec_file"]:
            read_data = read_data.replace('"' + content[0].upper() + '"', content[1])

        # apply firmawe spec configs
        for content in configs["firmware_spec_file"]:
            read_data = read_data.replace('"' + content[0].upper() + '"', content[1])

        try:
            with open('template.spec', 'w') as fout:
                fout.write(read_data)
                fout.close()
        except IOError as e:
            print(e.strerror)

    def cmd_build_rpm(self, args, configs):
        # build all rpms
        print("cmd_build_rpm")

    def cmd_build_iso(self, args, configs):
        # build iso added param for multi iso
        print("cmd_build_iso")
