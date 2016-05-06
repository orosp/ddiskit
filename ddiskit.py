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
            sys.stdout.write("Writing module.config ... ")
            if os.path.isfile("module.config"):
                sys.stdout.write("File Exist")
            else:
                with open('config', 'r') as fin:
                    read_data = fin.read()
                fin.close()
                fout = open('module.config', 'w')
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
        # parse config file and create spec file(s)
        print "cmd_generate_spec"

    def cmd_build_rpm(self, args, configs):
        # build all rpms
        print "cmd_build_rpm"

    def cmd_build_iso(self, args, configs):
        # build iso added param for multi iso
        print "cmd_build_iso"
