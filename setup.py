#!/usr/bin/python3
import sys
from setuptools import setup

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
    entry_points={
        'console_scripts': [
            'ddiskit=ddiskit.ddiskit:main',
        ],
    },

)
