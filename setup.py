#!/usr/bin/python

from setuptools import setup

setup(
    name="ddiskit",
    version="3.6",
    author="Petr Oros",
    author_email="poros@redhat.com",
    description=("Red Hat tool for Driver Update Disk creation"),
    license="GPLv3",
    url="https://github.com/orosp/ddiskit.git",
    data_files=[('/usr/share/bash-completion/completions', ['ddiskit']),
                ('/usr/share/ddiskit/templates',
                    ['templates/spec', 'templates/config']),
                ('/usr/share/ddiskit/profiles', ['profiles/default']),
                ('/usr/share/ddiskit/profiles',
                    ['profiles/rh-testing', 'profiles/rh-release']),
                ('/usr/share/ddiskit/keyrings/rh-release',
                    ['keyrings/rh-release/fd431d51.key']),
                ('/usr/share/ddiskit', ['ddiskit.config']),
                ('/usr/share/man/man1', ['ddiskit.1']),
                ('/etc', ['etc/ddiskit.config']),
                ],
    scripts=['bin/ddiskit'],
)
