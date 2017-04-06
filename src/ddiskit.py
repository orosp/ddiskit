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

RES_DIR = "/usr/share/ddiskit/"
TEMPLATE_DIR = "{res_dir}/templates"
PROFILE_DIR = "{res_dir}/profiles"

CONFIG_TEMPLATE = "config"
SPEC_TEMPLATE = "spec"

DEFAULT_CFG = "ddiskit.config"
SYSTEM_CFG = "/etc/ddiskit.config"
USER_CFG = "~/.ddiskitrc"

# Default configuration, put here values which can be overwritten by anything,
# but should be defined somewhere.
default_config = {
    "defaults": {
        "res_dir": RES_DIR,
        "template_dir": TEMPLATE_DIR,
        "profile_dir": PROFILE_DIR,
        "config_template": CONFIG_TEMPLATE,
        "spec_template": SPEC_TEMPLATE,
        },
    "global": {
        "module_vendor": "ENTER_MODULE_VENDOR",
        "module_author": "ENTER_MODULE_AUTHOR",
        "module_author_email": "ENTER_MODULE_AUTHOR_EMAIL",
        },
    }

kernel_nvr_re = r"[0-9]\.[0-9]{1,2}\.[0-9]{1,2}-[0-9]{1,4}"
kernel_z_part_re = r"(\.[0-9]{1,3})+"
kernel_dist_re = r"\.el([6-9]|[1-9][0-9])"

kernel_y_re = "^%s%s$" % (kernel_nvr_re, kernel_dist_re)
kernel_z_re = "^%s%s%s$" % (kernel_nvr_re, kernel_z_part_re, kernel_dist_re)

config_var_re = re.compile(r"{([^{}]*)}")


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
    ret = process.returncode
    if capture_output:
        result = result.decode()
    if args.verbosity >= res_print_lvl:
        if capture_output:
            print(result)
        if args.verbosity >= cmd_print_lvl:
            print("  Return code:", ret)
    return (ret, result)


def config_get(configs, key, section="defaults", default=None,
               max_subst_depth=8):
    """
    Retrieve a value from configuration dict and perform substitution on it.

    So, let's reimplement ConfigParser's interpolation, in a better(tm) way.

    There are three main differences:
     * Syntax. ConfigParser uses %(name)s and ddiskit historically sticks with
       {name}.
     * Support for cross-section references, {section.name}.
     * It doesn't fail on exceeding of substitution depth

    :param configs:         Dict of dicts containing current configuration.
    :param key:             Key to return value for. Can be in dot-less form
                            (in this case value of "section" parameter is used)
                            or in the form "section.key".
    :param section:         Section where key is resides. By default it has
                            value "defaults", which makes retrieving
                            arguments/defaults less verbose:
                            config_get(configs, "arg_name")
    :param default:         Default value which is used in case section/key is
                            absent.
    :param max_subst_depth: Maximum number of substitution rounds performed.
                            Providing value of 0 in this argument allows
                            retrieving raw value.
    :return:                Value of the requested key (or default), with
                            substitution performed no more than max_subst_depth
                            times.
    """
    def config_subst(m):
        """
        Callback for performing substitution in the configuration value.

        :param m: Match object, containing information about substring matching
                  variable substitution regex.
        :return:  Value to substitute it with: configuration value in case it
                  exists or unchanged value in case it does not.
        """
        key = map(str.lower, m.group(1).split('.', 1))

        if len(key) == 1:
            if section in configs and key[0] in configs[section]:
                return configs[section][key[0]]
        else:
            if key[0] in configs and key[1] in configs[key[0]]:
                return configs[key[0]][key[1]]

        return m.group(0)

    if key.find(".") >= 0:
        section, key = key.split(".", 1)

    val = default
    section = section.lower()
    key = key.lower()

    if section in configs and key in configs[section]:
        val = configs[section][key]

    if not isinstance(val, str):
        return val

    while max_subst_depth > 0:
        max_subst_depth -= 1
        new_val, cnt = config_var_re.subn(config_subst, val)

        if cnt == 0 or new_val == val:
            break

        val = new_val

    return val


def config_set(configs, key, val, section="defaults"):
    """
    Set value in configuration dict.

    :param configs: Dict of dicts containing current configuration.
    :param key:     Key to change. Can be in dot-less form (in this case value
                    of "section" parameter is used) or in the "section.key"
                    form.
    :param val:     New value.
    :param section: Section where key is resides. By default it has value
                    "defaults", which makes updating arguments/defaults less
                    verbose: config_set(configs, "arg_name", val)
    :return:        Updated configuration dict.
    """
    if key.find(".") >= 0:
        section, key = key.split(".", 1)

    section = section.lower()
    key = key.lower()

    if section not in configs:
        configs[section] = {}
    if key not in configs[section]:
        configs[section][key] = val

    return configs


def config_humble_set(configs, key, val, section="spec_file"):
    """
    Set value in case it is not set already. Used primarily for "spec_file"
    section.

    Implemented as a wrapper around config_get()/config_set(), which makes it
    somewhat less efficient, but not too much.

    :param configs: Dict of dicts containing current configuration.
    :param key:     Key to change. Can be in dot-less form (in this case value
                    of "section" parameter is used) or in the "section.key"
                    form.
    :param val:     New value.
    :param section: Section where key is resides. By default it has value
                    "spec_file", which makes providing fallback values for spec
                    file less verbose:
                    config_humble_set(configs, "arg_name", val)
    :return:        Updated configuration dict.
    """
    if config_get(configs, key, section, max_subst_depth=0) is None:
        config_set(configs, key, val, section)

    return configs


def apply_config(data, configs):
    """
    Replace prepared tags by strings from config
    :param data: input content with tags for replace
    :param configs: configs readed from cfg file
    :return: Replaced content
    """
    # no firmware? -> remove all firmware definitions from spec file
    have_fw = config_get(configs, "spec_file.firmware_include") == "True"
    config_set(configs, "spec_file.firmware_begin", "%%if %d" % int(have_fw))
    config_set(configs, "spec_file.firmware_end", "%endif")

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
    print("Config check ... OK")
    return configs


def get_config_name(cfg, extension=".cfg"):
    """
    Get config name based on provided config option. Uses the following
    heuristic (based on the one used in mock): if config options ends with
    config file extension, this is path to file (and then dirname and extension
    should be stripped), otherwise it is config name. In order to be cautious,
    it leaves only base name first in any case.

    :param cfg: Config name passed as the command-line argument
    :param extension: Configuration file extension
    """
    cfg = os.path.basename(cfg)
    if extension != "" and cfg.endswith(extension):
        cfg = cfg[:-len(extension)]

    return cfg


def get_config_path(cfg, default_dir=".", rel_dir=".", extension=".cfg"):
    """
    Get path to config based on provided configuration "name".

    It uses the following heuristic: if configuration name does not have
    slashes and does not end with expected extension (or this extension is
    empty) then it is considered that this name refers to the file in "default
    directory", otherwise it is interpreted as a path to file (relative to some
    path provided in rel_dir).

    :param cfg:         Configuration file name.
    :param default_dir: Default directory for these configuration files.
    :param rel_dir:     Path configuration file should be relative to in case
                        path provided instead of name.
    :param extension:   Expected configuration file extension.
    :return:            Path to the configuration file.
    """
    if "/" not in cfg and (extension == "" or not cfg.endswith(extension)):
        cfg = os.path.basename(cfg)
        cfg = os.path.join(default_dir, cfg + extension)
    else:
        cfg = os.path.join(rel_dir, cfg)

    cfg = os.path.normpath(cfg)

    return cfg


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
            template_dir = config_get(configs, "template_dir")
            config_template = config_get(configs, "config_template")
            with open(get_config_path(config_template, extension="",
                      default_dir=template_dir), 'r') as fin:
                read_data = fin.read()
                with open(args.config, 'w+') as fout:
                    fout.write(read_data)
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
        template_dir = config_get(configs, "template_dir")
        spec_template = config_get(configs, "spec_template")
        with open(get_config_path(spec_template, extension="",
                  default_dir=template_dir), 'r') as fin:
            read_data = fin.read()
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
        if not args.srpm:
            print("Because you are not on target architecture, " +
                  "building only SRPM")
        do_build_srpm(args, configs)


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
                ret, arch = command(['rpm', '-q', '--qf', '%{ARCH}', '-p',
                                    str(content)], args)
                if ret != 0:
                    print("Got %d when tried to get arch, skipping: %s" %
                          (ret, str(content)))
                    continue
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
                            ret, arch = command(['rpm', '-q', '--qf',
                                                 '%{ARCH}', '-p',
                                                 str(root) + "/" + str(file)],
                                                args)
                            if ret != 0:
                                print(("Got %d when tried to get arch, " +
                                       "skipping: %s") % (ret, str(content)))
                                continue
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



def apply_args(args, configs):
    """
    Puts command-line args as a values of "defaults" section of configuration
    file, so it could be used for providing defaults when specific argument
    is not provided.

    :param args:    Namespace instance containing command line arguments, as
                    returned by argparse.ArgumentParser.parse_args()
    :param configs: Dict of dicts of configuration values.
    :return:        Updated configs argument
    """
    if "defaults" not in configs:
        configs["defaults"] = {}
    configs["defaults"].update([(k, v) for k, v in args.__dict__.iteritems()
                                if v is not None])

    return configs


def apply_config_file(filename, configs={}):
    """
    Read configuration file and apply it to a configuration dict.

    Ignores sections and keys containing dot as it breaks config_get/config_set
    (and we do not use such section/key names anyway).

    :param filename: Path to configuration file.
    :param configs:  Configuration dict to merge configuration file contents
                     into.
    :return:         Tuple containing updated configs value (useful in case no
                     starting configuration has been provided) and reading
                     result (None in case of configparser errors and result of
                     cfgparser.read() otherwise).
    """
    cfgparser = configparser.RawConfigParser()

    res = cfgparser.read(filename)

    try:
        for section in cfgparser.sections():
            if "." in section:
                print("WARNING: section \"%s\" (config file \"%s\") contains" +
                      " dot in its name, ignored." % (section, filename))
                continue
            if section not in configs:
                configs[section] = {}
            for key, val in cfgparser.items(section):
                if "." in key:
                    print("WARNING: key \"%s\" in section \"%s\" (config " +
                          "file \"%s\") contains dot in its name, ignored." %
                          (key, section, filename))
                    continue
                configs[section][key] = val
    except configparser.Error as err:
        print(str(err))
        return (configs, None)

    return (configs, res)


def parse_config(filename, args, configs={}):
    """
    Parse configuration file.

    Returns configuration dict based on the supplied config filename, command
    line arguments, and default configuration dict.

    It merges default, system, user, profile, and module configs, and provide
    resulting configuration dictionary.

    :param filename: Path to input file.
    :param args:     Namespace instance containing command line arguments, as
                     returned by argparse.ArgumentParser.parse_args()
    :param configs:  Pre-existing configuration dict.
    :return:         Resulting configuration dict.
    """
    implicit_configs = [
        os.path.join(config_get(configs, "res_dir", default=RES_DIR),
                     DEFAULT_CFG),
        SYSTEM_CFG,
        os.path.expanduser(USER_CFG),
        ]

    for cfg in implicit_configs:
        apply_config_file(cfg, configs)

    # Apply args here in order to derive profile to use
    apply_args(args, configs)

    profile_dir = config_get(configs, "profile_dir")
    profile = config_get(configs, "profile")
    if profile is not None and profile_dir is not None:
        apply_config_file(get_config_path(profile, profile_dir, extension=""),
                          configs)

    if filename is not None:
        ret = apply_config_file(filename, configs)[1]
        if ret is None or len(ret) == 0:
            print("Config file: " + filename + " not found")
            return None

    apply_args(args, configs)

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
    root_parser.add_argument("-p", "--profile",
                             help="Configuration profile to use")
    root_parser.add_argument("-R", "--res-dir",
                             help="Resources dir (%s by default)" % RES_DIR)
    root_parser.add_argument("-T", "--template-dir",
                             help="Templates dir (%s by default)" %
                             TEMPLATE_DIR)
    root_parser.add_argument("-P", "--profile-dir",
                             help="Profiles dir (%s by default)" % PROFILE_DIR)

    cmdparsers = root_parser.add_subparsers(title='Commands',
                                            help='main ddiskit commands')

    # parser for the "prepare_sources" command
    parser_prepare_sources = cmdparsers.add_parser('prepare_sources',
                                                   help='Prepare sources')
    parser_prepare_sources.add_argument("-c", "--config",
                                        default='module.config',
                                        help="Config file")
    parser_prepare_sources.add_argument("-t", "--config-template",
                                        help="Config file template")
    parser_prepare_sources.set_defaults(func=cmd_prepare_sources)

    # parser for the "generate_spec" command
    parser_generate_spec = cmdparsers.add_parser('generate_spec',
                                                 help='Generate spec file')
    parser_generate_spec.add_argument("-c", "--config",
                                      default='module.config',
                                      help="Config file")
    parser_generate_spec.add_argument("-t", "--spec-template",
                                      help="RPM spec file template")
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
        configs = parse_config(args.config, args, default_config)
        if configs is None:
            sys.exit(1)
        if (args.verbosity >= 2):
            print("Config: %r" % configs)
        configs = check_config(configs)
        if configs is None:
            sys.exit(1)
        args.func(args, configs)
    else:
        args.func(args, parse_config(None, args, default_config))


if __name__ == "__main__":
    main()
