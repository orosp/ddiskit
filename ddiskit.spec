%global srcname ddiskit
%global Tool for create Driver Update Disc

Name:           python-%{srcname}
Version:        3.1
Release:        1%{?dist}
Summary:        %{sum}

License:        GPLv2
URL:            %{srcname}
Source0:        %{srcname}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python-devel
BuildRequires:  python-setuptools
Requires:       kernel-devel redhat-rpm-config kmod createrepo genisoimage

%description -n python-%{srcname}
Ddiskit is a little framework for easy creating proper Driver Update Disc.

%prep
%autosetup -n %{srcname}-%{version}

%build
%{__python} setup.py build

%install
%{__python} setup.py install --skip-build --root $RPM_BUILD_ROOT

%check
%{__python} setup.py test

%files -n python-%{srcname}
%defattr(-,root,root,-)
%doc README
%license COPYING
%{python_sitelib}/*
%{_bindir}/ddiskit
%{_sysconfdir}/bash_completion.d/ddiskit.bash
%{_datadir}/ddiskit/templates/spec
%{_datadir}/ddiskit/templates/config

%changelog
* Tue Feb 28 2017 Petr Oros <poros@redhat.com> - 3.1-1
- New upstream relese

* Mon Feb 13 2017 Petr Oros <poros@redhat.com> - 3.0-2
- Bump version after few important fixes

* Mon Sep 5 2016 Petr Oros <poros@redhat.com> - 3.0-1
- Initial package.

