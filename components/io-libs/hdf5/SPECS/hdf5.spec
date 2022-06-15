#----------------------------------------------------------------------------bh-
# This RPM .spec file is part of the OpenHPC project.
#
# It may have been modified from the default version supplied by the underlying
# release package (if available) in order to apply patches, perform customized
# build/install configurations, and supply additional files to support
# desired integration conventions.
#
#----------------------------------------------------------------------------eh-

# Serial HDF5 library build that is dependent on compiler toolchain
%define ohpc_compiler_dependent 1
%include %{_sourcedir}/OHPC_macros

# Base package name
%define pname hdf5

Summary:   A general purpose library and file format for storing scientific data
Name:      %{pname}-%{compiler_family}%{PROJ_DELIM}
Version:   1.10.9
Release:   1%{?dist}
License:   HDF5 (BSD-3-Clause) and LBNL
Group:     %{PROJ_NAME}/io-libs
URL:       http://www.hdfgroup.org/HDF5
Source0:   https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-1.10/%{pname}-%{version}/src/%{pname}-%{version}.tar.bz2

BuildRequires: zlib-devel
Requires:      zlib

#!BuildIgnore: post-build-checks rpmlint-Factory

# Default library install path
%define install_path %{OHPC_LIBS}/%{compiler_family}/%{pname}/%version

%description
HDF5 is a general purpose library and file format for storing scientific data.
HDF5 can store two primary objects: datasets and groups. A dataset is
essentially a multidimensional array of data elements, and a group is a
structure for organizing objects in an HDF5 file. Using these two basic
objects, one can create and store almost any kind of scientific data
structure, such as images, arrays of vectors, and structured and unstructured
grids. You can also mix and match them in HDF5 files according to your needs.


%prep
%setup -q -n %{pname}-%{version}


%build
# override with newer config.guess for aarch64
%ifarch aarch64 || ppc64le
cp /usr/lib/rpm/config.guess bin
%endif

# OpenHPC compiler/mpi designation
%ohpc_setup_compiler

./configure --prefix=%{install_path} \
            --libdir=%{install_path}/lib \
            --enable-fortran         \
            --enable-static=no       \
            --enable-shared          \
            --enable-cxx             \
            --enable-fortran2003    || { cat config.log && exit 1; }

%if "%{compiler_family}" == "llvm" || "%{compiler_family}" == "arm1"
sed -i -e 's#wl=""#wl="-Wl,"#g' libtool
sed -i -e 's#pic_flag=""#pic_flag=" -fPIC -DPIC"#g' libtool
%endif

make %{?_smp_mflags}


%install
# OpenHPC compiler designation
%ohpc_setup_compiler

export NO_BRP_CHECK_RPATH=true

make %{?_smp_mflags} DESTDIR=$RPM_BUILD_ROOT install

# Remove static libraries
find "%buildroot" -type f -name "*.la" -delete

# OpenHPC module file
mkdir -p %{buildroot}%{OHPC_MODULEDEPS}/%{compiler_family}/%{pname}
cat << EOF > %{buildroot}/%{OHPC_MODULEDEPS}/%{compiler_family}/%{pname}/%{version}.lua
help([[
This module loads the %{PNAME} library built with the %{compiler_family} compiler toolchain.

Version %{version}
]])

whatis("Name: %{pname} built with %{compiler_family} toolchain")
whatis("Version: %{version}")
whatis("Category: runtime library")
whatis("Description: %{summary}")
whatis("%{url}")

local version = "%{version}"

prepend_path( "PATH",            "%{install_path}/bin")
prepend_path( "INCLUDE",         "%{install_path}/include")
prepend_path( "LD_LIBRARY_PATH", "%{install_path}/lib")
setenv(       "%{pname}_DIR",    "%{install_path}")
setenv(       "%{pname}_BIN",    "%{install_path}/bin")
setenv(       "%{pname}_LIB",    "%{install_path}/lib")
setenv(       "%{pname}_INC",    "%{install_path}/include")

family("hdf5")
EOF

cat << EOF > %{buildroot}/%{OHPC_MODULEDEPS}/%{compiler_family}/%{pname}/.version.%{version}.lua
-- version file for %{pname}-%{version}
--
local ModulesVersion = "%{version}"
EOF

mkdir -p ${RPM_BUILD_ROOT}/%{_docdir}


%files
%{install_path}
%{OHPC_MODULEDEPS}/%{compiler_family}/%{pname}
%license COPYING
%doc README.md
