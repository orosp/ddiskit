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
import shutil
import tarfile
from datetime import datetime
from pprint import pprint

def apply_config(data, configs):
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

def do_build_rpm(args, configs):
    print("Start RPM build ... ")
    for arch in ["x86_64"]:
        cmd = "rpmbuild --nodeps --target " + arch
        # --------------^^^^^^^^ ----FOR DEBUG ONLY !!!!!!!!!!!
        cmd +=  " --define \"_topdir " + os.getcwd() + "/rpm\""
        cmd +=  " -ba " + "rpm/SPECS/" + configs["spec_file"]["module_name"] + ".spec"
    os.system(cmd)

def cmd_prepare_sources(args, configs):
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
    print("Your module source code put in src directory.")

def cmd_generate_spec(args, configs):
    if len(configs) == 0:
        print(args.config, end="")
        print(" not found, use \"ddiskit prepare_sources\" for create")
        sys.exit(1)
    if os.path.isfile("rpm/SPECS/" + configs["spec_file"]["module_name"] + ".spec"):
        print("File Exist rpm/SPECS/" + configs["spec_file"]["module_name"] + ".spec!")
    try:
        with open('../templates/spec', 'r') as fin:
            read_data = fin.read()
            fin.close()
    except IOError as e:
        print(e.strerror)

    src_root = "src/"
    configs["spec_file"]["source_patches"] = ""
    configs["spec_file"]["source_patches_do"] = ""
    if os.path.isdir(src_root + "patches") and os.listdir(src_root + "patches"):
        print("Found directory with patches, adding into spec file:")
        os.chdir(src_root + "patches")
        index = 0
        configs["spec_file"]["source_patches"] = "# Source code patches"
        for files in os.listdir("."):
            print("  Patch" + str(index) + ": " + files)
            configs["spec_file"]["source_patches"] = \
              configs["spec_file"]["source_patches"] + "\nPatch" + str(index) + ":\t" + files
            configs["spec_file"]["source_patches_do"] = \
              configs["spec_file"]["source_patches_do"] + "\n%patch" + str(index) + " -p1" 
            index = index + 1
        os.chdir("../../")
    else:
        print("Patch directory not found or empty-> skipping")

    read_data = apply_config(read_data, configs)
    print("Writing spec into rpm/SPECS/" + configs["spec_file"]["module_name"] + ".spec ... ", end="")
    try:
        with open("rpm/SPECS/" + configs["spec_file"]["module_name"] + ".spec", 'w') as fout:
            fout.write(read_data)
            fout.close()
    except IOError as e:
        print(e.strerror)
    else:
        print("OK")

def cmd_build_rpm(args, configs):
    if len(configs) == 0:
        print(args.config, end="")
        print(" not found, use \"ddiskit prepare_sources\" for create")
        sys.exit(1)

    try:
        with open('../templates/files', 'r') as fin:
            read_data = fin.read()
            fin.close()
    except IOError as e:
        print(e.strerror)
    print("Writing rpm/SOURCES/" + configs["spec_file"]["module_name"] + ".files file ... ", end="")

    read_data = apply_config(read_data, configs)

    try:
        with open("rpm/SOURCES/" + configs["spec_file"]["module_name"] + ".files", 'w') as fout:
            fout.write(read_data)
            fout.close()
    except IOError as e:
        print(e.strerror)
    print("OK")

    # check Makefile
    saved_root = ""
    makefile_found = False
    src_root = "src/"
    for root, dirs, files in os.walk(src_root):
        if len(root) > len(saved_root):
            saved_root = root
        if "Makefile" in files:
            makefile_found = True
    saved_root = saved_root.replace(src_root, "")

    if not makefile_found:
        try:
            with open('../templates/makefile', 'r') as fin:
                read_data = fin.read()
                fin.close()
        except IOError as e:
            print(e.strerror)

        read_data = apply_config(read_data, configs)
        print("Makefile not found -> Using generic version")
        try:
            with open(src_root + saved_root + "/Makefile", 'w') as fout:
                fout.write(read_data)
                fout.close()
        except IOError as e:
            print(e.strerror)
    else:
        print("Checking makefile ... OK")

    nvv = configs["spec_file"]["module_name"] + "-" + \
        configs["global"]["module_vendor"] + "-" + \
        configs["spec_file"]["module_version"]
    archive = "rpm/SOURCES/" + nvv + ".tar.bz2"
    print("Writing archive " + archive + " ... ", end="")
    try:
        tar = tarfile.open(archive, "w:bz2")
        os.chdir(src_root)
        for files in os.listdir("."):
            if "patches" not in files:
                tar.add(files, arcname=nvv + "/" + files, recursive=True)
        tar.close()
        os.chdir("..")
    except Exception as e:
        print(str(e))
    else:
        print("OK")

    if os.path.isdir(src_root + "patches") and os.listdir(src_root + "patches"):
        print("Copying patches into rpm/SOURCES:")
        os.chdir(src_root + "patches")
        for files in os.listdir("."):
            shutil.copyfile(files, "../../rpm/SOURCES/" + files)
            print("  Copying: " + files)
        os.chdir("../../")
    else:
        print("Patch directory not found or empty-> skipping")

    do_build_rpm(args, configs)

    # Stage 2) Generate build outputs for final rpm
    #   a) Copy patches
    #   b) Build module
    #   c) Generate greylist & module.symvers and write into rpm/SOURCES

    # STAGE3 (build rpm with rpmbuild -ba & rpmbuild -ba firmware)
        # here begin work driven by specfile
        # apply patches
        # build module
        # sign module
        # run depmod
        # run find requires
        # run find provides
        # write rpm, srpm

def cmd_build_iso(args, configs):
    # Collect rpms/srpms for all arches
    # Prepare iso filesystem
    # Prepare repository
    # Add rpms/srpms into repository
    # Write repository into iso
    print("cmd_build_iso")
