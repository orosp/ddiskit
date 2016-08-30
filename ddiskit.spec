%global srcname ddiskit
%global Tool for create Driver Update Disc

Name:           python3-%{srcname}
Version:        3.0
Release:        1%{?dist}
Summary:        %{sum}

License:        GPLv2
URL:            %{srcname}
Source0:        %{srcname}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools
Requires:       kernel-devel redhat-rpm-config kmod createrepo
%description
An python module which provides a convenient example.
Summary:        %{sum}
%{?python_provide:%python_provide python3-%{srcname}}

%description -n python3-%{srcname}
An python module which provides a convenient example.


%prep
%autosetup -n %{srcname}-%{version}

%build
%py3_build

%install
%py3_install

%files -n python3-%{srcname}
%license COPYING
%doc README
%{python3_sitelib}/*

%changelog
