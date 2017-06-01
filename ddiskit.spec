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
Requires:       kmod createrepo genisoimage
Suggests:       quilt
Recommends:     kernel-devel redhat-rpm-config
Recommends:     mock


%description -n %{name}
Ddiskit is a little framework for simplifying creation of proper
Driver Update Disks (DUD).

%prep
%autosetup -n %{name}-%{version}

%build
%{__python} setup.py build

%install
%{__python} setup.py install --skip-build --root $RPM_BUILD_ROOT
find %{buildroot} -size 0 -delete

%check
%{__python} setup.py test

%files -n %{name}
%defattr(-,root,root,-)
%doc README COPYING
%{python_sitelib}/*
%{_bindir}/ddiskit
%{_mandir}/man1/ddiskit.1*
%{_datadir}/bash-completion/completions/ddiskit
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

