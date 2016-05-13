%global srcname ddiskit
%global Tool for create Driver Update Disc

Name:           python-%{srcname}
Version:        3.0
Release:        1%{?dist}
Summary:        %{sum}

License:        GPLv2
URL:            %{srcname}
Source0:        %{srcname}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel

%description
An python module which provides a convenient example.

%package -n python3-%{srcname}
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

%check
%{__python3} setup.py test

%files -n python3-%{srcname}
%license COPYING
%doc README.rst
%{python3_sitelib}/*
%{_bindir}/ddiskit

%changelog
