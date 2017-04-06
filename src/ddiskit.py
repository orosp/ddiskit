#!/usr/bin/python
#
# ddiskit - tool for Red Hat Enterprise Linux Driver Update Disk creation
#
# Author: Petr Oros <poros@redhat.com>
# Copyright (C) 2016-2017 Red Hat, Inc.
#
# This software may be freely redistributed under the terms of the GNU
# General Public License version 3 (GPLv3).
from __future__ import print_function

import argparse
import functools
import os
import re
import shutil
import sys
import tarfile
import tempfile
import time
from datetime import datetime
from subprocess import PIPE, Popen
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

kernel_nvr_re = r"[0-9]\.[0-9]{1,2}\.[0-9]{1,2}-[0-9]{1,4}"
kernel_z_part_re = r"(\.[0-9]{1,3})+"
kernel_dist_re = r"\.el[0-9]"

kernel_y_re = "^%s%s$" % (kernel_nvr_re, kernel_dist_re)
kernel_z_re = "^%s%s%s$" % (kernel_nvr_re, kernel_z_part_re, kernel_dist_re)


def command(cmd, args, cmd_print_lvl=1, res_print_lvl=2, capture_output=True):
    """
    Execute shell command and return stdout string
    :param cmd: Command
    :return: String printed by cmd to stdout
    """
    if (args.verbosity >= cmd_print_lvl):
        print("Executing command: %r" % cmd)
    process = Popen(
        args=cmd,
        stdout=PIPE if capture_output else None
    )
    result = process.communicate()[0]
    if capture_output:
        result = result.decode()
    if args.verbosity >= res_print_lvl and capture_output:
        print(result)
    return result


def apply_config(data, configs):
    """
    Replace prepared tags by strings from config
    :param data: input content with tags for replace
    :param configs: configs readed from cfg file
    :return: Replaced content
    """
    # no firmware? -> remove all firmware definitions from spec file
    if configs["spec_file"]["firmware_include"] != "True":
        data = re.sub(re.compile(r'^%{FIRMWARE_BEGIN}.*?%{FIRMWARE_END}$',
                      re.DOTALL | re.MULTILINE), '', data)
    else:
        data = data.replace("%{FIRMWARE_BEGIN}\n", "")
        data = data.replace("%{FIRMWARE_END}\n", "")

    # apply configs on configs
    for section in ["global", "spec_file"]:
        for key in configs[section]:
            for section2 in ["global", "spec_file"]:
                for key2 in configs[section2]:
                    configs[section2][key2] = \
                        configs[section2][key2].replace("{" + key + "}",
                                                        configs[section][key])

    # apply all configs on specfile template
    for section in ["global", "spec_file"]:
        for key in configs[section]:
            data = data.replace("%{" + key.upper() + "}",
                                configs[section][key])

    # generic keys code
    # date of creation
    data = data.replace("%{DATE}", datetime.__format__(datetime.now(),
                        "%a %b %d %Y"))

    # kernel_requires
    if re.match(kernel_y_re, configs["spec_file"]["kernel_version"]):
        kernel_version = re.split(r'[\.-]',
                                  configs["spec_file"]["kernel_version"])
        kernel_version_str = "%s.%s.%s-" % (kernel_version[0],
                                            kernel_version[1],
                                            kernel_version[2])
        kernel_requires = "Requires:	kernel >= %s%s.%s\n" % \
            (kernel_version_str, kernel_version[3], kernel_version[4])
        kernel_requires += "Requires:	kernel < %s%s.%s" % \
            (kernel_version_str, int(kernel_version[3]) + 1, kernel_version[4])
    elif re.match(kernel_z_re, configs["spec_file"]["kernel_version"]):
        kernel_requires = "Requires:	kernel = " + \
            configs["spec_file"]["kernel_version"]
    data = data.replace("%{KERNEL_REQUIRES}", kernel_requires)

    # module_requires
    if "dependencies" in configs["spec_file"] and \
            configs["spec_file"]["dependencies"] != "":
        module_requires = "Requires:	" + configs["spec_file"]["dependencies"]
        data = data.replace("%{MODULE_REQUIRES}", module_requires)
    else:
        data = data.replace("%{MODULE_REQUIRES}\n", "")
    return data


def check_config(configs):
    """
    Check config and repair non-critical mistakes.
    :param configs: config to check
    :return: Fixed config or None
    """
    config_critic = False
    print("Checking config ... ")
    for section in ["global", "spec_file"]:
        for key in configs[section]:
            if "ENTER_" in configs[section][key]:
                if key == "firmware_version" and \
                        configs["spec_file"]["firmware_include"] == "False":
                    continue
                else:
                    print("FAIL: key: %s value: %s is default value" %
                          (key, configs[section][key]))
                    config_critic = True
            elif key == "kernel_version":
                if re.match(kernel_y_re, configs[section][key]):
                    continue
                elif re.match(kernel_z_re, configs[section][key]):
                    print("WARNING: You are using z-stream kernel version! " +
                          "You shouldn't use it.")
                    print("         If you don't have good reason for it, " +
                          "please use y-stream kernel version")
                    continue
                else:
                    print("FAIL: Invalid kernel version in config file: " +
                          configs[section][key])
                    print("      Valid version is for example 3.10.0-123.el7")
                    config_critic = True
            elif key == "module_build_dir":
                if configs[section][key][0] == "/":
                    configs[section][key] = configs[section][key][1:]
                    print("WARNING: Leading \"/\" in module_build_dir, " +
                          "fixing ... OK")
                if configs[section][key][-1] == "/":
                    configs[section][key] = configs[section][key][0:-1]
                    print("WARNING: Trailing \"/\" in module_build_dir, " +
                          "fixing ... OK")

    if config_critic:
        print("Unrecoverable FAIL, please check your config file and run " +
              "ddiskit again.")
        return None
    print("Config check ... done")
    return configs


def do_build_rpm(args, configs, arch):
    """
    Second stage for build rpm
    :param args: unused (required for unify callback interface)
    :param configs: configs readed from cfg file
    """
    print("Start RPM build for "+arch+" ... ")
    cmd = ["rpmbuild", "--target", arch,
           "--define", "_topdir " + os.getcwd() + "/rpm",
           "-ba", "rpm/SPECS/%s.spec" % configs["spec_file"]["module_name"]]

    command(cmd, args, capture_output=False)


def do_build_srpm(args, configs):
    """
    Second stage for build rpm (here build only srpm)
    :param args: unused (required for unify callback interface)
    :param configs: configs readed from cfg file
    """
    print("Start SRPM build ... ")
    cmd = ["rpmbuild", "--define", "_topdir " + os.getcwd() + "/rpm",
           "-bs", "rpm/SPECS/%s.spec" % configs["spec_file"]["module_name"]]

    command(cmd, args, capture_output=False)


def cmd_prepare_sources(args, configs):
    """
    CMD prepare_sources callback
    :param args: argument parser arguments
    :param configs: configs readed from cfg file
    """
    try:
        print("Writing new config file (" + args.config + ")... ", end="")
        if os.path.isfile(args.config):
            print("File Exist")
        else:
            with open('/usr/share/ddiskit/templates/config', 'r') as fin:
                read_data = fin.read()
            fin.close()
            fout = open(args.config, 'w+')
            fout.write(read_data)
            fout.close()
            print("OK")
    except IOError as err:
        print(str(err))
        sys.exit(1)

    print("Creating directory structure for RPM build ... ", end="")
    dir_list = ["rpm", "rpm/BUILD", "rpm/BUILDROOT", "rpm/RPMS", "rpm/SOURCES",
                "rpm/SPECS", "rpm/SRPMS"]
    try:
        for dirs in dir_list:
            if not os.path.exists(dirs):
                os.makedirs(dirs)
    except OSError as err:
        print(str(err))
    else:
        print("OK")
    print("Creating directory for source code ... ", end="")
    dir_list = ["src", "src/patches", "src/firmware"]
    try:
        for dirs in dir_list:
            if not os.path.exists(dirs):
                os.makedirs(dirs)
    except OSError as err:
        print(str(err))
    else:
        print("OK")
    print("Put your module source code in src directory.")


def cmd_generate_spec(args, configs):
    """
    CMD generate_spec callback
    :param args: argument parser arguments
    :param configs: configs readed from cfg file
    """
    if configs is None or len(configs) == 0:
        print(args.config, end="")
        print(" not found, use \"ddiskit prepare_sources\" to create it")
        sys.exit(1)

    spec_path = "rpm/SPECS/" + configs["spec_file"]["module_name"] + ".spec"
    if os.path.isfile(spec_path):
        print("File Exist %s!" % spec_path)
    try:
        with open('/usr/share/ddiskit/templates/spec', 'r') as fin:
            read_data = fin.read()
            fin.close()
    except IOError as err:
        print(str(err))
        sys.exit(1)

    cwd = os.getcwd()

    src_root = "src/"
    configs["spec_file"]["source_patches"] = ""
    configs["spec_file"]["source_patches_do"] = ""
    if os.path.isdir(src_root + "patches") and \
            os.listdir(src_root + "patches"):
        print("Found directory with patches, adding into spec file:")
        os.chdir(src_root + "patches")
        index = 0
        configs["spec_file"]["source_patches"] = "# Source code patches"
        for files in sorted(os.listdir(".")):
            print("  Patch" + str(index) + ": " + files)
            configs["spec_file"]["source_patches"] = \
                configs["spec_file"]["source_patches"] + \
                "\nPatch" + str(index) + ":\t" + files
            configs["spec_file"]["source_patches_do"] = \
                configs["spec_file"]["source_patches_do"] + "\n%patch" + \
                str(index) + " -p1"
            index = index + 1
    else:
        print("Patch directory not found or empty-> skipping")

    os.chdir(cwd)

    if os.path.isdir(src_root + "firmware") and \
            os.listdir(src_root + "firmware"):
        if configs["spec_file"]["firmware_include"] != "True":
            print("\n  WARNING: Firmware directory contain files, but " +
                  "firmware package is disabled by config!\n")
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
                        configs["spec_file"]["firmware_files"] + \
                        "/lib/firmware/" + file_root + str(file) + "\n"
                    configs["spec_file"]["firmware_files_install"] = \
                        configs["spec_file"]["firmware_files_install"] + \
                        "install -m 644 -D source/firmware/" + \
                        file_root + str(file) + \
                        " $RPM_BUILD_ROOT/lib/firmware/" + file_root + \
                        str(file) + "\n"
    else:
        print("Firmware directory not found or empty-> skipping")

    source_fail = False
    for arch in configs["spec_file"]["kernel_arch"].split():
        kernel_dir = "/usr/src/kernels/" + \
            configs["spec_file"]["kernel_version"] + "." + arch
        if not os.path.isdir(kernel_dir):
            print("WARNING: kernel source code not found: " + kernel_dir)
            source_fail = True
    if source_fail:
        print("         Probably will not possible to compile all rpms on " +
              "this system")
        print("         For fix install kernel-devel-" +
              configs["spec_file"]["kernel_version"] + " package")

    read_data = apply_config(read_data, configs)
    print("Writing spec into %s ... " % spec_path, end="")
    try:
        with open(spec_path, 'w') as fout:
            fout.write(read_data)
            fout.close()
    except IOError as err:
        print(str(err))
    else:
        print("OK")


def filter_tar_info(args, nvv):
    def filter_tar_info_args(ti, args, nvv):
        ti.mode = 0755 if ti.isdir() else 0644
        ti.uname = "nobody"
        ti.gname = "nobody"
        ti.uid = 0
        ti.gid = 0
        ti.mtime = time.time()

        if not args.tar_all and \
                any([x.startswith(".") for x in ti.name.split("/")]):
            if args.verbosity >= 1:
                print("  Skipping hidden file: %s" % ti.name)

            return None

        fn = os.path.basename(ti.name)

        if ti.isfile() and ti.name.split("/")[0] != "firmware" and \
                fn != "Kbuild" and fn != "Makefile" and \
                not fn.endswith(".c") and not fn.endswith(".h"):
            print("  Unexpected file: %s" % ti.name)

            if args.tar_strict:
                return None

        if args.verbosity >= 2:
            print("  Adding: %s" % ti.name)

        ti.name = os.path.join(nvv, ti.name)

        return ti

    return functools.partial(filter_tar_info_args, args=args, nvv=nvv)


def cmd_build_rpm(args, configs):
    """
    CMD build_rpm callback
    :param args: argument parser arguments
    :param configs: configs readed from cfg file
    """
    warning = False
    if configs is None or len(configs) == 0:
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
        print("Makefile not found -> Please create one in " + src_root +
              saved_root)
        sys.exit(1)
    else:
        print("Checking makefile ... OK")

    nvv = configs["spec_file"]["module_name"] + "-" + \
        configs["global"]["module_vendor"] + "-" + \
        configs["spec_file"]["module_version"]
    archive = "rpm/SOURCES/" + nvv + ".tar.bz2"
    print("Writing archive " + archive + " ...")

    cwd = os.getcwd()

    try:
        tar = tarfile.open(archive, "w:bz2")
        os.chdir(src_root)
        for files in os.listdir("."):
            if "patches" == files or files.endswith(".rpm"):
                if args.verbosity >= 1:
                    print("  Skipping: %s" % files)
                continue
            if "firmware" == files:
                if os.path.isdir("firmware") and os.listdir("firmware"):
                    if configs["spec_file"]["firmware_include"] != "True":
                        warning = True
                        print("  WARNING: Firmware directory contains " +
                              "files, but firmware package is disabled by " +
                              "config!")
                        continue
                else:
                    if args.verbosity >= 1:
                        print("  Skipping: %s" % files)
                    continue
            tar.add(os.path.normpath(files), filter=filter_tar_info(args, nvv))
        tar.close()
    except Exception as err:
        print(str(err))
    else:
        if not warning:
            print("Finish writing archive.")

    os.chdir(cwd)

    if os.path.isdir(src_root + "patches") and \
            os.listdir(src_root + "patches"):
        print("Copying patches into rpm/SOURCES:")
        os.chdir(src_root + "patches")
        for files in os.listdir("."):
            shutil.copyfile(files, "../../rpm/SOURCES/" + files)
            print("  Copying: " + files)
    else:
        print("Patch directory not found or empty -> skipping")

    os.chdir(cwd)

    build_arch = os.uname()[4]
    kernel_dir = "/usr/src/kernels/" + \
        configs["spec_file"]["kernel_version"] + "." + build_arch
    if not args.srpm and build_arch in configs["spec_file"]["kernel_arch"]:
        if not os.path.isdir(kernel_dir):
            print("WARNING: kernel source code not found: %s" % kernel_dir)
            print("         Building SRPM only")
            do_build_srpm(args, configs)
        else:
            do_build_rpm(args, configs, build_arch)
    else:
        do_build_srpm(args, configs)
        if not args.srpm:
            print("Because you are not on target architecture, " +
                  "building only SRPM")


def cmd_build_iso(args, configs):
    """
    CMD build_iso callback
    :param args: argument parser arguments
    :param configs: configs readed from cfg file
    """
    arch_list = []
    rpm_files = []
    for content in args.filelist:
        try:
            if os.path.isfile(content):
                arch = command(['rpm', '-q', '--qf', '%{ARCH}', '-p',
                                str(content)], args)
                if arch not in arch_list:
                    arch_list.append(arch)
                    rpm_files.append(str(content))
                print("Including: " + str(content))
            elif os.path.exists(content):
                print("Listing content: " + str(content))
                for root, dirs, files in os.walk(content):
                    for file in files:
                        if not file.endswith(".rpm"):
                            continue
                        if configs and \
                                configs["global"]["include_srpm"] != "True" \
                                and ".src." in str(file):
                            print("Source rpms are disabled by config. " +
                                  "Skipping: " + str(root) + "/" + str(file))
                        elif "debuginfo" in str(file):
                            # TODO
                            print("Debuginfo is not supported. Skipping: " +
                                  str(root) + "/" + str(file))
                        else:
                            print("Including: " + str(root) + "/" + str(file))
                            arch = command(['rpm', '-q', '--qf', '%{ARCH}',
                                            '-p', str(root) + "/" + str(file)],
                                           args)
                            arch = re.sub(re.compile(r'i[0-9]86',
                                          re.IGNORECASE), 'i386', arch)
                            if arch not in arch_list:
                                arch_list.append(arch)
                            rpm_files.append(str(root) + "/" + str(file))
        except OSError as err:
            print(str(err))

    dir_tmp = tempfile.mkdtemp()
    saved_umask = os.umask(0o077)
    tmp_dirs = ["disk", "disk/rpms", "disk/src"]
    try:
        for dirs in tmp_dirs:
            if not os.path.exists(dir_tmp + "/" + dirs):
                os.makedirs(dir_tmp + "/" + dirs)
    except OSError as err:
        print(str(err))

    for arch in arch_list:
        if not os.path.exists(dir_tmp + "/disk/rpms/" + arch):
            os.makedirs(dir_tmp + "/disk/rpms/" + arch)

    for file in rpm_files:
        if ".src." in file:
            shutil.copyfile(file, dir_tmp + "/disk/src/" +
                            os.path.basename(file))
        else:
            for arch in arch_list:
                if '.' + arch + '.' in \
                        os.path.basename(re.sub(re.compile(r'i[0-9]86',
                                         re.IGNORECASE), 'i386', file)):
                    shutil.copyfile(file, dir_tmp + "/disk/rpms/" + arch +
                                    "/" + os.path.basename(file))

    for arch in arch_list:
        command(['createrepo', '--pretty', dir_tmp + "/disk/rpms/" + arch],
                args, res_print_lvl=0, capture_output=False)

    try:
        with open(dir_tmp + "/disk/rhdd3", 'w') as fout:
            fout.write("Driver Update Disk version 3")
            fout.close()
    except IOError as err:
        print(str(err))

    if args.isofile is None:
        # Try to use info from config for constructing file name
        try:
            args.isofile = "dd-" + \
                configs["spec_file"]["module_name"] + "-" + \
                configs["spec_file"]["module_version"] + "-" + \
                configs["spec_file"]["module_rpm_release"] + "." + \
                configs["spec_file"]["rpm_dist"] + ".iso"
        except TypeError:
            args.isofile = "dd.iso"

    command(['mkisofs', '-V', 'OEMDRV', '-input-charset', 'UTF-8', '-R',
             '-uid', '0', '-gid', '0', '-dir-mode', '0555',
             '-file-mode', '0444', '-o', args.isofile, dir_tmp + '/disk'],
            args, res_print_lvl=0, capture_output=False)
    os.umask(saved_umask)

    for root, dirs, files in os.walk(dir_tmp, topdown=False):
        for file in files:
            os.remove(os.path.join(root, file))
        for cdir in dirs:
            os.rmdir(os.path.join(root, cdir))
    os.rmdir(dir_tmp)


def parse_config(filename):
    """
    Parser for config file
    :param filename: input file
    :return: parsed config
    """
    configs = {}
    cfgparser = configparser.SafeConfigParser()
    if len(cfgparser.read(filename)) == 0:
        print("Config file: " + filename + " not found")
        sys.exit(1)
    try:
        for section in cfgparser.sections():
            configs[section] = dict(cfgparser.items(section))
    except configparser.Error as err:
        print(str(err))
        sys.exit(1)
    return configs


def parse_cli():
    """
    Commandline argument parser
    :return: commandline arguments
    """
    root_parser = argparse.ArgumentParser(prog='ddiskit',
                                          description='Red Hat tool for ' +
                                          'create Driver Update Disk')
    root_parser.add_argument("-v", "--verbosity", action="count", default=0,
                             help="Increase output verbosity")

    cmdparsers = root_parser.add_subparsers(title='Commands',
                                            help='main ddiskit commands')

    # parser for the "prepare_sources" command
    parser_prepare_sources = cmdparsers.add_parser('prepare_sources',
                                                   help='Prepare sources')
    parser_prepare_sources.add_argument("-c", "--config",
                                        default='module.config',
                                        help="Config file")
    parser_prepare_sources.set_defaults(func=cmd_prepare_sources)

    # parser for the "generate_spec" command
    parser_generate_spec = cmdparsers.add_parser('generate_spec',
                                                 help='Generate spec file')
    parser_generate_spec.add_argument("-c", "--config",
                                      default='module.config',
                                      help="Config file")
    parser_generate_spec.set_defaults(func=cmd_generate_spec)

    # parser for the "build_rpm" command
    parser_build_rpm = cmdparsers.add_parser('build_rpm', help='Build rpm')
    parser_build_rpm.add_argument("-c", "--config", default='module.config',
                                  help="Config file")
    parser_build_rpm.add_argument("-a", "--tar-all", action='store_true',
                                  default=False,
                                  help="Tar all files, including hidden ones")
    parser_build_rpm.add_argument("-e", "--tar-strict", action='store_true',
                                  default=False,
                                  help="Tar only expected files")
    parser_build_rpm.add_argument("-s", "--srpm", action='store_true',
                                  default=False, help="Build src RPM")
    parser_build_rpm.set_defaults(func=cmd_build_rpm)

    # parser for the "build_iso" command
    parser_build_iso = cmdparsers.add_parser('build_iso', help='Build iso')
    parser_build_iso.add_argument("-c", "--config", default='module.config',
                                  help="Config file")
    parser_build_iso.add_argument("-i", "--isofile", default=None,
                                  help="Output file name")
    parser_build_iso.add_argument("filelist", nargs="*",
                                  default=["rpm/RPMS/", "rpm/SRPMS/"],
                                  help="RPM list, separated by space and " +
                                  "can use directory path")
    parser_build_iso.set_defaults(func=cmd_build_iso)

    args = root_parser.parse_args()
    if not hasattr(args, "func"):
        root_parser.print_help()
        sys.exit(1)
    return args


def main():
    args = parse_cli()
    if args.config != "" and os.path.isfile(args.config):
        configs = check_config(parse_config(args.config))
        if configs is None:
            sys.exit(1)
        args.func(args, configs)
    else:
        args.func(args, None)


if __name__ == "__main__":
    main()
