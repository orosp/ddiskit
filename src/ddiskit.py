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
from datetime import datetime
from pprint import pprint

class Ddiskit:
    def apply_config(self, data, configs):
        # apply global configs
        for key in configs["global"]:
            data = data.replace("%{" + key.upper() + "}", configs["global"][key])

        # apply spec configs
        for key in configs["spec_file"]:
            data = data.replace("%{" + key.upper() + "}", configs["spec_file"][key])

        # apply firmawe spec configs
        for key in configs["firmware_spec_file"]:
            data = data.replace("%{" + key.upper() + "}", configs["firmware_spec_file"][key])

        # generic keys for spec
        data = data.replace("%{DATE}", datetime.__format__(datetime.now(), "%a %b %d %Y"))
        return data

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
        print("Creating directory for source code ... ", end="")
        try:
            if not os.path.exists("src"):
                os.makedirs("src")
        except OSError as e:
            print(e.strerror)
        else:
            print("OK")
        print("Done")
        print("Your module source code put in src directory.")

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

        read_data = self.apply_config(read_data, configs)

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
        # STAGE1 (prepare source)
            # generate module.files & makefile
            # pack source in src and write it into rpm/SOURCES
            # copy module.files & makefile & patch into rpm/SOURCES
        
        # STAGE2 (generate build outputs)
            # apply patches
            # build module
            # generate greylist & module.symvers and write into rpm/SOURCES
            # add new files into spes
        
        # STAGE3 (build rpm with rpmbuild -ba & rpmbuild -ba firmware)
            # here begin work driven by specfile
            # apply patches
            # build module
            # sign module
            # run depmod
            # run find requires
            # run find provides
            # write rpm, srpm
        print("cmd_build_rpm")

    def cmd_build_iso(self, args, configs):
        # get all files form rpm/SRPMS, rpm/RPMS
        # build iso
        print("cmd_build_iso")
