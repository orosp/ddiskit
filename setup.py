#!/usr/bin/python

from setuptools import setup

setup(
    name="ddiskit",
    version="3.3",
    author="Petr Oros",
    author_email="poros@redhat.com",
    description=("Red Hat tool for create Driver Update Disk"),
    license="GPLv3",
    url="http://git.engineering.redhat.com/git/users/poros/ddiskit.git/",
    packages=['ddiskit'],
    package_dir={'ddiskit': 'src/'},
    data_files=[('/etc/bash_completion.d', ['ddiskit.bash']),
                ('/usr/share/ddiskit/templates',
                    ['templates/spec', 'templates/config']),
                ('/usr/share/ddiskit/profiles', ['profiles/default']),
                ('/usr/share/ddiskit/profiles',
                    ['profiles/rh-testing', 'profiles/rh-release']),
                ('/usr/share/ddiskit', ['ddiskit.config']),
                ('/usr/share/man/man1', ['ddiskit.1']),
                ],
    entry_points={
        'console_scripts': [
            'ddiskit=ddiskit.ddiskit:main',
        ],
    },
)
