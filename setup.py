#!/usr/bin/python3
import sys
from setuptools import setup, Command

setup(
    name = "ddiskit",
    version = "3.0",
    author = "Petr Oros",
    author_email = "poros@redhat.com",
    description = ("Red Hat tool for create Driver Update Disk"),
    license = "GPLv2+",
    url = "http://git.engineering.redhat.com/git/users/poros/ddiskit.git/",
    packages = ['ddiskit'],
    package_dir={'ddiskit': 'src/'},
    data_files = [('/etc/bash_completion.d', ['ddiskit.bash'])],
)
