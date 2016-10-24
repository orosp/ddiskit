%global srcname ddiskit
%global Tool for create Driver Update Disc

Name:           python3-%{srcname}
Version:        3.0
Release:        1%{?dist}
Summary:        %{sum}

License:        GPLv3
URL:            %{srcname}
Source0:        %{srcname}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools
Requires:       kernel-devel redhat-rpm-config kmod createrepo
Summary:        %{sum}

%description -n python3-%{srcname}
Ddiskit is a little framework for easy creating proper Driver Update Disc.

%prep
%autosetup -n %{srcname}-%{version}

%build
%py3_build

%install
%py3_install

%files -n python3-%{srcname}
%defattr(-,root,root,-)
%doc README
%license COPYING
%{python3_sitelib}/*
%{_bindir}/ddiskit
%{_sysconfdir}/bash_completion.d/ddiskit.bash
%{_datadir}/ddiskit/templates/spec
%{_datadir}/ddiskit/templates/config

%changelog
* Mon Sep 5 2016 Petr Oros <poros@redhat.com> - 3.0-1
- Initial package.

