%global srcname ddiskit
%global sum     Tool for Red Hat Enterprise Linux Driver Update Disk creation

Name:           %{srcname}
Version:        3.2
Release:        1%{?dist}
Summary:        %{sum}

License:        GPLv3
URL:            %{srcname}
Source0:        %{srcname}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python-devel
BuildRequires:  python-setuptools
Requires:       kernel-devel redhat-rpm-config kmod createrepo genisoimage

%description -n %{srcname}
Ddiskit is a little framework for simplifying creation of proper
Driver Update Disks (DUD).

%prep
%autosetup -n %{srcname}-%{version}

%build
%{__python} setup.py build

%install
%{__python} setup.py install --skip-build --root $RPM_BUILD_ROOT

%check
%{__python} setup.py test

%files -n %{srcname}
%defattr(-,root,root,-)
%doc README
%license COPYING
%{python_sitelib}/*
%{_bindir}/ddiskit
%{_sysconfdir}/bash_completion.d/ddiskit.bash
%{_datadir}/ddiskit/templates/spec
%{_datadir}/ddiskit/templates/config
%{_datadir}/ddiskit/profiles/*
%{_datadir}/ddiskit/ddiskit.config

%changelog
* Tue Mar 14 2017 Petr Oros <poros@redhat.com> - 3.2-1
- New upstream release

* Tue Feb 28 2017 Petr Oros <poros@redhat.com> - 3.1-1
- New upstream release

* Mon Feb 13 2017 Petr Oros <poros@redhat.com> - 3.0-2
- Bump version after few important fixes

* Mon Sep 5 2016 Petr Oros <poros@redhat.com> - 3.0-1
- Initial package.

