Name:           ddiskit
Version:        3.3
Release:        1%{?dist}
Summary:        Tool for Red Hat Enterprise Linux Driver Update Disk creation

License:        GPLv3
URL:            https://github.com/orosp/ddiskit
Source0:        https://github.com/orosp/ddiskit/archive/%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python-devel
BuildRequires:  python-setuptools
Requires:       kernel-devel redhat-rpm-config kmod createrepo genisoimage

%description -n %{name}
Ddiskit is a little framework for simplifying creation of proper
Driver Update Disks (DUD).

%prep
%autosetup -n %{name}-%{version}

%build
%{__python} setup.py build

%install
%{__python} setup.py install --skip-build --root $RPM_BUILD_ROOT

%check
%{__python} setup.py test

%files -n %{name}
%defattr(-,root,root,-)
%doc README
%license COPYING
%{python_sitelib}/*
%{_bindir}/ddiskit
%{_sysconfdir}/bash_completion.d/ddiskit.bash
%dir %{_datadir}/ddiskit/profiles
%dir %{_datadir}/ddiskit/templates
%{_datadir}/ddiskit/templates/spec
%{_datadir}/ddiskit/templates/config
%{_datadir}/ddiskit/profiles/*
%config(noreplace) %{_datadir}/ddiskit/ddiskit.config

%changelog
* Mon Apr 24 2017 Petr Oros <poros@redhat.com> - 3.3-1
- New upstream release

* Tue Mar 14 2017 Petr Oros <poros@redhat.com> - 3.2-1
- New upstream release

* Tue Feb 28 2017 Petr Oros <poros@redhat.com> - 3.1-1
- New upstream release

* Mon Feb 13 2017 Petr Oros <poros@redhat.com> - 3.0-2
- Bump version after few important fixes

* Mon Sep 5 2016 Petr Oros <poros@redhat.com> - 3.0-1
- Initial package.

