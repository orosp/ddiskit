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
from pprint import pprint

class Ddiskit:
    def cmd_prepare_sources(self, args, configs):
        try:
            print("Writing new config file (" + args.config + ")... ", end="")
            if os.path.isfile(args.config):
                print("File Exist")
            else:
                with open('../templates/config', 'r') as fin:
                    read_data = fin.read()
                fin.close()
                fout = open(args.config, 'w')
                fout.write(read_data)
                fout.close()
                print("OK")
        except IOError as e:
            print(e.strerror)

        print("Creating directory structure for RPM build ... ", end="")
        dir_list = ["rpm", "rpm/BUILD", "rpm/BUILDROOT", "rpm/RPMS", "rpm/SOURCES", "rpm/SPECS", "rpm/SRPMS"]
        try:
            for dirs in dir_list:
               if not os.path.exists(dirs):
                  os.makedirs(dirs)
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
        if os.path.isfile("rpm/SPECS/" + configs["spec_file"]["module_name"] + ".spec"):
            print("File Exist rpm/SPECS/tg3.spec!")
        try:
            with open('../templates/spec', 'r') as fin:
                read_data = fin.read()
                fin.close()
        except IOError as e:
            print(e.strerror)
        print("Generating new spec file ... ", end="")

        # apply global configs
        for key in configs["global"]:
            read_data = read_data.replace("%{" + key.upper() + "}", configs["global"][key])

        # apply spec configs
        for key in configs["spec_file"]:
            read_data = read_data.replace("%{" + key.upper() + "}", configs["spec_file"][key])

        # apply firmawe spec configs
        for key in configs["firmware_spec_file"]:
            read_data = read_data.replace("%{" + key.upper() + "}", configs["firmware_spec_file"][key])
        print("OK")
        print("Writing spec rpm/SPECS/" + configs["spec_file"]["module_name"] + ".spec ... ", end="")
        try:
            with open("rpm/SPECS/" + configs["spec_file"]["module_name"] + ".spec", 'w') as fout:
                fout.write(read_data)
                fout.close()
        except IOError as e:
            print(e.strerror)
        print("OK")
        print("Done")

    def cmd_build_rpm(self, args, configs):
        # build all rpms
        print("cmd_build_rpm")

    def cmd_build_iso(self, args, configs):
        # build iso added param for multi iso
        print("cmd_build_iso")
