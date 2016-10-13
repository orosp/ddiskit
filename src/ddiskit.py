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
import re
import sys
import shutil
import tarfile
import argparse
import tempfile
import configparser
from datetime import datetime
from pprint import pprint
from subprocess import PIPE, Popen

def command(cmd):
    process = Popen(
        args=cmd,
        stdout=PIPE,
        shell=True
    )
    return process.communicate()[0].decode()

def apply_config(data, configs):
    # if have no firmware -> remove all firmware defintions from spec file
    if configs["spec_file"]["firmware_include"] != "True":
        data = re.sub(r'^%{FIRMWARE_BEGIN}.*?%{FIRMWARE_END}$', '', data, flags=re.DOTALL | re.M)
    else:
        data = data.replace("%{FIRMWARE_BEGIN}\n", "")
        data = data.replace("%{FIRMWARE_END}\n", "")

    # apply configs on configs
    for section in ["global", "spec_file"]:
        for key in configs[section]:
            for section2 in ["global", "spec_file"]:
                for key2 in configs[section2]:
                    configs[section2][key2] = \
                      configs[section2][key2].replace("{" + key + "}", configs[section][key])

    # apply all configs on specfile template
    for section in ["global", "spec_file"]:
        for key in configs[section]:
            data = data.replace("%{" + key.upper() + "}", configs[section][key])

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
    dir_list = ["src", "src/patches", "src/firmware"]
    try:
        for dirs in dir_list:
            if not os.path.exists(dirs):
                os.makedirs(dirs)
    except OSError as e:
        print(e.strerror)
    else:
        print("OK")
    print("Your module source code put in src directory.")
    print("Creating directory for final iso files ... ", end="")
    try:
        if not os.path.exists("iso"):
            os.makedirs("iso")
    except OSError as e:
        print(e.strerror)
    else:
        print("OK")

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

    if os.path.isdir(src_root + "firmware") and os.listdir(src_root + "firmware"):
        if configs["spec_file"]["firmware_include"] != "True":
            print ("\n  WARNING: Firmware directory contain files, but firmware package is disabled by config!!!\n")
        else:
            configs["spec_file"]["firmware_files"] = ""
            configs["spec_file"]["firmware_files_install"] = ""
            print("Found directory with firmware, adding into spec file:")
            for root, dirs, files in os.walk(src_root + "firmware/"):
                for file in files:
                    file_root = root.replace(src_root + "firmware/", "")
                    if len(file_root) > 0:
                        file_root = file_root + "/"
                    print("  Firmware: " + file_root + str(file))
                    configs["spec_file"]["firmware_files"] = \
                        configs["spec_file"]["firmware_files"] + "/lib/firmware/" + file_root + str(file) + "\n"
                    configs["spec_file"]["firmware_files_install"] = \
                        configs["spec_file"]["firmware_files_install"] + "install -m 644 -D source/firmware/" + \
                        file_root + str(file) + " $RPM_BUILD_ROOT/lib/firmware/" + file_root + str(file) + "\n"
    else:
        print("Firmware directory not found or empty-> skipping")

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
            if "patches" in files or "rpm" in files:
                continue
            if "firmware" in files and os.path.isdir("firmware") and os.listdir("patches"):
                tar.add(files, arcname=nvv + "/lib/" + files, recursive=True)
            else:
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

def cmd_build_iso(args, configs):
    arch_list = []
    rpm_files = []
    rpm_greylist = []
    for content in args.filelist:
        try:
            if os.path.isfile(content):
                arch = command('rpm -q --qf "%{ARCH}" -p '+ str(root)+"/"+str(file))
                if arch not in arch_list:
                    arch_list.append(arch)
                    rpm_files.append(str(root)+"/"+str(file))
                print("Including: " + str(content))
            elif os.path.exists(content):
                print("Listing content: " + str(content))
                for root, dirs, files in os.walk(content):
                    for file in files:
                        if configs["global"]["include_srpm"] != "True" and ".src." in str(file):
                            print ("Source rpms are disabled by config. Skipping: " + str(root)+"/"+str(file))
                        else:
                            print ("Including: " + str(root)+"/"+str(file))
                            arch = command('rpm -q --qf "%{ARCH}" -p '+ str(root)+"/"+str(file))
                            arch = re.sub(r'i[0-9]86', 'i386', arch, flags=re.IGNORECASE)
                            if arch not in arch_list:
                                arch_list.append(arch)
                            rpm_files.append(str(root)+"/"+str(file))
        except OSError as e:
            print(e.strerror)

    dir_tmp = tempfile.mkdtemp()
    saved_umask = os.umask(0o077)
    tmp_dirs = ["disk", "disk/rpms", "disk/src", "greylists"]
    try:
        for dir in tmp_dirs:
            if not os.path.exists(dir_tmp+"/"+dir):
                os.makedirs(dir_tmp+"/"+dir)
    except OSError as e:
        print(e.strerror)

    for arch in arch_list:
        if not os.path.exists(dir_tmp+"/disk/rpms/"+arch):
            os.makedirs(dir_tmp+"/disk/rpms/"+arch)

    for file in rpm_files:
        if ".src." in file:
            shutil.copyfile(file, dir_tmp+"/disk/src/"+os.path.basename(file))
        else:
            for arch in arch_list:
                if '.'+arch+'.' in os.path.basename(re.sub(r'i[0-9]86', 'i386', file, flags=re.IGNORECASE)):
                    shutil.copyfile(file, dir_tmp+"/disk/rpms/"+arch+"/"+os.path.basename(file))
                    print (command('rpm2cpio '+file+' | cpio -i --quiet --to-stdout greylist.'+arch))
                    #rpm_greylist.append(extract_greylist(file))

    for arch in arch_list:
        print (command('createrepo --pretty '+dir_tmp+"/disk/rpms/"+arch))

    try:
        with open(dir_tmp+"/disk/rhdd3", 'w') as fout:
            fout.write("Driver Update Disk version 3")
            fout.close()
    except IOError as e:
        print(e.strerror)

    print (command('mkisofs -V OEMDRV -R -uid 0 -gid 0 -dir-mode 0555 -file-mode 0444 -o '+args.isofile+' '+dir_tmp+'/disk'))
    os.umask(saved_umask)

    for root, dirs, files in os.walk(dir_tmp, topdown=False):
        for file in files:
            os.remove(os.path.join(root, file))
        for dir in dirs:
            os.rmdir(os.path.join(root, dir))
    os.rmdir(dir_tmp)

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
    root_parser = argparse.ArgumentParser(prog='ddiskit', description='Red Hat tool for create Driver Update Disk')
    root_parser.add_argument("-v", "--verbosity", action="count", default=0, help="Increase output verbosity")

    cmdparsers = root_parser.add_subparsers(title='Commands', help='main ddiskit commands')

    # parser for the "prepare_sources" command
    parser_prepare_sources = cmdparsers.add_parser('prepare_sources', help='Prepare sources')
    parser_prepare_sources.add_argument("-c", "--config", default='module.config', help="Config file")
    parser_prepare_sources.set_defaults(func=cmd_prepare_sources)

    # parser for the "generate_spec" command
    parser_generate_spec = cmdparsers.add_parser('generate_spec', help='Generate spec file')
    parser_generate_spec.add_argument("-c", "--config", default='module.config', help="Config file")
    parser_generate_spec.set_defaults(func=cmd_generate_spec)

    # parser for the "build_rpm" command
    parser_build_rpm = cmdparsers.add_parser('build_rpm', help='Build rpm')
    parser_build_rpm.add_argument("-c", "--config", default='module.config', help="Config file")
    parser_build_rpm.set_defaults(func=cmd_build_rpm)

    # parser for the "build_iso" command
    parser_build_iso = cmdparsers.add_parser('build_iso', help='Build iso')
    parser_build_iso.add_argument("-c", "--config", default='module.config', help="Config file")
    parser_build_iso.add_argument("-i", "--isofile", default='dd.iso', help="Output file name")
    parser_build_iso.add_argument("filelist", nargs="*", default=["rpm/RPMS/", "rpm/SRPMS/"], help="RPM list, separated by space and can use directory path")
    
    parser_build_iso.set_defaults(func=cmd_build_iso)

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
