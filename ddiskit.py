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
from pprint import pprint

class Ddiskit:
    def cmd_prepare_sources(self, args, configs):
        # touch config example
        # create dirs for rpm build
        print "cmd_prepare_sources"

    def cmd_generate_spec(self, args, configs):
        # parse config file and create spec file(s)
        print "cmd_generate_spec"

    def cmd_build_rpm(self, args, configs):
        # build all rpms
        print "cmd_build_rpm"

    def cmd_build_iso(self, args, configs):
        # build iso added param for multi iso
        print "cmd_build_iso"
