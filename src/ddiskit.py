#!/usr/bin/python
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
from pprint import pprint

class Ddiskit:
    def cmd_prepare_sources(self, args, configs):
        try:
            sys.stdout.write("Writing new config file ... ")
            if os.path.isfile(args.config):
                sys.stdout.write("File Exist")
            else:
                with open('config', 'r') as fin:
                    read_data = fin.read()
                fin.close()
                fout = open(args.config, 'w')
                fout.write(read_data)
                fout.close()
                sys.stdout.write("OK")
            sys.stdout.write("\n")
            sys.stdout.flush()
        except IOError as e:
            sys.stdout.write(e.strerror)
            sys.stdout.write("\n")
            sys.stdout.flush()

        sys.stdout.write("Creating directory structure for RPM build ... ")
        try:
            os.makedirs("rpm")
            os.makedirs("rpm/SPEC")
            os.makedirs("rpm/SOURCE")
        except OSError as e:
            sys.stdout.write(e.strerror)
        else:
            sys.stdout.write("OK")
        sys.stdout.write("\n")
        sys.stdout.write("Done\n")
        sys.stdout.flush()

    def cmd_generate_spec(self, args, configs):
        if len(configs) == 0:
            sys.stdout.write(args.config)
            sys.stdout.write(" not found, use \"ddiskit prepare_sources\" for create\n")
            sys.exit(1)
        try:
            with open('../spec', 'r') as fin:
                read_data = fin.read()
                fin.close()
        except IOError as e:
            sys.stdout.write(e.strerror)
            sys.stdout.write("\n")
            sys.stdout.flush()
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
            sys.stdout.write(e.strerror)
            sys.stdout.write("\n")
            sys.stdout.flush()

    def cmd_build_rpm(self, args, configs):
        # build all rpms
        print "cmd_build_rpm"

    def cmd_build_iso(self, args, configs):
        # build iso added param for multi iso
        print "cmd_build_iso"
