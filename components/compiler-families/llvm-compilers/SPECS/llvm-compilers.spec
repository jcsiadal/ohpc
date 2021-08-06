#----------------------------------------------------------------------------bh-
# This RPM .spec file is part of the OpenHPC project.
#
# It may have been modified from the default version supplied by the underlying
# release package (if available) in order to apply patches, perform customized
# build/install configurations, and supply additional files to support
# desired integration conventions.
#
#----------------------------------------------------------------------------eh-

# Simple check for other active LLVM versions; they will break this build
%if 0%(which clang llvm-ar >/dev/null 2>&1; echo $?) == 0
%{error: "LLVM found in PATH; cannot build LLVM with with another LLVM available"}
%endif

%include %{_sourcedir}/OHPC_macros

%ifarch aarch64 
%global triple aarch64-pc-linux-gnu
%global build_target AArch64
%else
%global triple x86_64-pc-linux-gnu
%global build_target X86
%endif

# Limit the number of parallel build processes to avoid race conditions
%global _smp_ncpus_max 8

%global major_ver 12
%global pname llvm%{major_ver}-compilers

Summary:   LLVM (An Optimizing Compiler Infrastructure)
Name:      %{pname}%{PROJ_DELIM}
Version:   12.0.1
Release:   1%{?dist}
License:   Apache-2.0 with LLVM exception
Group:     %{PROJ_NAME}/compiler-families
URL:       http://www.llvm.org
Source0:   https://github.com/llvm/llvm-project/archive/refs/tags/llvmorg-%{version}.tar.gz

BuildRequires:  cmake%{PROJ_DELIM}
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  python3
BuildRequires:  zlib-devel
BuildRequires:  pkgconfig
BuildRequires:  binutils-devel
BuildRequires:  glibc >= 2.26
BuildRequires:  libffi-devel
BuildRequires:  (libelf-devel or elfutils-libelf-devel)
BuildConflicts: libunwind-devel

Requires:       binutils
Requires:       python3
Requires:       gcc-gfortran

Patch1:          llvm1201-polly_inc_fix.patch


%define install_path %{OHPC_COMPILERS}/llvm/%{version}

%description
LLVM is a compiler infrastructure designed for compile-time, link-time, runtime,
and idle-time optimization of programs from arbitrary programming languages.
LLVM is written in C++ and has been developed since 2000 at the University of
Illinois and Apple. It currently supports compilation of C and C++ programs, 
using front-ends derived from GCC 4.0.1. The compiler infrastructure
includes mirror sets of programming tools as well as libraries with equivalent
functionality.
This package includes: clang, flang, libcxx, ibcxxabi, compiler-rt, openmp,
                       libunwind, lld, clang-tools-extra, libclc, and polly 
  

%prep
%setup -q -n llvm-project-llvmorg-%{version} 
%patch1 -p1
mkdir -p build/stage1
mkdir -p build/stage2

# Replace any ambiguous python shebangs or rpmbuild will fail
find . -type f -exec sed -i '1s,#! */usr/bin/env python\($\| \),#!/usr/bin/python2,' "{}" \;


%build
module load cmake

MAIN=$(pwd)
BOOTSTRAP=$MAIN/build/stage1
FINAL=$MAIN/build/stage2

# STAGE 1
# Bootstrap llvm with the distro llvm
# Lots of options; the goal is to disable as much as possible
#    to reduce build time, but keep all of the required components
#    needed to rebuild LLVM12 with LLVM12
# ZLib support required for OpenSUSE15
cd $BOOTSTRAP
cmake -DCMAKE_INSTALL_PREFIX="$BOOTSTRAP" \
      -DCMAKE_C_COMPILER=gcc \
      -DCMAKE_CXX_COMPILER=g++ \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_CXX_LINK_FLAGS="-Wl,-rpath,$BOOTSTRAP/lib -L$BOOTSTRAP/lib" \
      -DLLVM_DEFAULT_TARGET_TRIPLE=%{triple} \
      -DLLVM_ENABLE_PROJECTS="clang;lld;compiler-rt;libunwind;libcxxabi;libcxx" \
      -DLLVM_BUILD_TOOLS=On \
      -DLLVM_TARGETS_TO_BUILD=%{build_target} \
      -DLLVM_INCLUDE_TESTS=Off \
      -DLLVM_INCLUDE_EXAMPLES=Off \
      -DLLVM_INCLUDE_UTILS=Off \
      -DLLVM_INCLUDE_DOCS=Off \
      -DLLVM_INCLUDE_BENCHMARKS=Off \
      -DLLVM_ENABLE_ZLIB=On \
      -DLLVM_ENABLE_Z3_SOLVER=Off \
      -DLLVM_ENABLE_BACKTRACES=Off \
      -DLLVM_LINK_LLVM_DYLIB=On \
      -DLLVM_ENABLE_LTO=Off \
      -DLLVM_STATIC_LINK_CXX_STDLIB=On \
      -DCLANG_INCLUDE_TESTS=Off \
      -DCLANG_ENABLE_STATIC_ANALYZER=Off \
      -DCLANG_ENABLE_ARCMT=Off \
      -DCOMPILER_RT_INCLUDE_TESTS=Off \
      -DCOMPILER_RT_BUILD_BUILTINS=On \
      -DCOMPILER_RT_BUILD_SANITIZERS=Off \
      -DCOMPILER_RT_BUILD_XRAY=Off \
      -DCOMPILER_RT_BUILD_LIBFUZZER=Off \
      -DCOMPILER_RT_BUILD_PROFILE=Off \
      -DLIBCXX_INCLUDE_BENCHMARKS=Off \
      -DLIBCXX_INCLUDE_TESTS=Off \
      -DLIBCXX_ENABLE_EXPERIMENTAL_LIBRARY=Off \
      -DFLANG_BUILD_NEW_DRIVER=Off \
      -DFLANG_INCLUDE_DOCS=Off \
      -DFLANG_INCLUDE_TESTS=Off \
      -DFLANG_BUILD_TOOLS=On \
      -Wno-dev $MAIN/llvm 

cmake --build . %{_smp_mflags}
# End Stage 1

# STAGE 2
# Rebuild all components with new clang.
# Swtich to using libc++, compiler-rt, and libunwind only.

cd $FINAL
#cmake -DCMAKE_BUILD_TYPE=Release \
#      -DCMAKE_INSTALL_PREFIX="%{install_path}" \
#      -DCMAKE_C_COMPILER=$BOOTSTRAP/bin/clang \
#      -DCMAKE_CXX_COMPILER=$BOOTSTRAP/bin/clang++ \
#      -DCMAKE_Fortran_COMPILER=/usr/bin/gfortran \
#      -DCMAKE_C_FLAGS="-I/$BOOTSTRAP/include/c++/v1 -fuse-ld=lld -fPIC -stdlib=libc++ -Qunused-arguments" \
#      -DCMAKE_CXX_FLAGS="-I$BOOTSTRAP/include/c++/v1 -fuse-ld=lld -fPIC -stdlib=libc++ -Qunused-arguments" \
#      -DCMAKE_Fortran_FLAGS="-fuse-ld=lld -fPIC -Wunused-parameter" \
#      -DCMAKE_ASM_COMPILER=$BOOTSTRAP/bin/clang \
#      -DCMAKE_AR=$BOOTSTRAP/bin/llvm-ar \
#      -DCMAKE_RANLIB=$BOOTSTRAP/bin/llvm-ranlib \
#      -DCMAKE_LINKER=$BOOTSTRAP/bin/ld.lld \
#      -DCMAKE_EXE_LINKER_FLAGS="-rtlib=compiler-rt -unwindlib=libunwind -L$STAGE2/lib -Wl,--thinlto-jobs=4 -Wl,--as-needed" \
#      -DCMAKE_SHARED_LINKER_FLAGS="-rtlib=compiler-rt -unwindlib=libunwind -L$STAGE2/lib -Wl,--thinlto-jobs=4 -Wl,--as-needed" \
#      -DLLVM_TABLEGEN=$BOOTSTRAP/bin/llvm-tblgen \
#      -DLLVM_OPTIMIZED_TABLEGEN=On \
#      -DLLVM_CONFIG_PATH=$BOOTSTRAP/bin/llvm-config \
#      -DLLVM_ENABLE_LIBCXX=On \
#      -DLLVM_DEFAULT_TARGET_TRIPLE=%{triple} \
#      -DLLVM_BINUTILS_INCDIR=/usr/include \
#      -DLLVM_ENABLE_LLD=On \
#      -DLLVM_ENABLE_PROJECTS="clang;lld;openmp;libclc;clang-tools-extra;polly;compiler-rt;libunwind;libcxxabi;libcxx" \
#      -DLLVM_ENABLE_LTO=Thin \
#      -DLLVM_TARGETS_TO_BUILD=%{build_target} \
#      -DLLVM_LINK_LLVM_DYLIB=On \
#      -DLLVM_BUILD_LLVM_DYLIB=On \
#      -DLLVM_BUILD_STATIC=Off \
#      -DLLVM_DYLIB_COMPONENTS=all\
#      -DLLVM_INCLUDE_DOCS=Off \
#      -DLLVM_INCLUDE_BENCHMARKS=Off \
#      -DLLVM_ENABLE_Z3_SOLVER=Off \
#      -DLLVM_INSTALL_UTILS=On \
#      -DLLVM_ENABLE_ZLIB=On \
#      -DLLVM_ENABLE_MODULES=On \
#      -DLLVM_ENABLE_RTTI=On \
#      -DLLVM_ENABLE_FFI=On \
#      -DLLVM_ENABLE_EH=Off \
#      -DLLVM_USE_INTEL_JITEVENTS=On \
#      -DLLVM_USE_PERF=On \
#      -DLLVM_BUILD_TESTS=Off \
#      -DLLVM_ENABLE_PIC=On \
#      -DLLVM_INSTALL_TOOLCHAIN_ONLY=On \
#      -DLLVM_INSTALL_CCTOOLS_SYMLINKS=On \
#      -DCLANG_DEFAULT_LINKER=lld \
#      -DCLANG_PLUGIN_SUPPORT=On \
#      -DCLANG_DEFAULT_RTLIB=compiler-rt \
#      -DCLANG_DEFAULT_UNWINDLIB=libunwind \
#      -DCLANG_DEFAULT_CXX_STDLIB=libc++ \
#      -DLIBUNWIND_USE_COMPILER_RT=On \
#      -DLIBUNWIND_ENABLE_STATIC=Off \
#      -DCOMPILER_RT_USE_LIBCXX=On \
#      -DCOMPILER_RT_BUILD_BUILTINS=On \
#      -DLIBCXXABI_USE_LLVM_UNWINDER=On \
#      -DLIBCXXABI_USE_COMPILER_RT=On \
#      -DLIBCXXABI_ENABLE_STATIC=Off \
#      -DLIBCXX_CXX_ABI=libcxxabi \
#      -DLIBCXX_USE_COMPILER_RT=On \
#      -DLIBCXX_ENABLE_SHARED=On \
#      -DLIBCXX_ENABLE_STATIC=Off \
#      -DLIBCXX_CXX_ABI_INCLUDE_PATHS="$MAIN/libcxxabi/include" \
#      -DLIBOMP_ENABLE_SHARED=On \
#      -DLIBOMP_ENABLE_STATIC=Off \
#      -DLIBOMP_LIBFLAGS="-lm" \
#      -DLIBOMP_FORTRAN_MODULES=Off \
#      -DLIBOMP_COPY_EXPORTS=Off \
#      -DLIBOMP_USE_HWLOC=Off \
#      -DLIBOMP_OMPT_SUPPORT=On \
#      -Wno-dev $MAIN/llvm

#      -DCMAKE_Fortran_COMPILER=$BOOTSTRAP/bin/flang \
#      -DFLANG_BUILD_NEW_DRIVER=On \
#      -DFLANG_INCLUDE_DOCS=Off \
#      -DFLANG_INCLUDE_TESTS=Off \
#      -DFLANG_BUILD_TOOLS=Off \

cmake -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX="%{install_path}" \
      -DCMAKE_C_COMPILER=$BOOTSTRAP/bin/clang \
      -DCMAKE_CXX_COMPILER=$BOOTSTRAP/bin/clang++ \
      -DCMAKE_Fortran_COMPILER=/usr/bin/gfortran \
      -DCMAKE_ASM_COMPILER=$BOOTSTRAP/bin/clang \
      -DCMAKE_AR=$BOOTSTRAP/bin/llvm-ar \
      -DCMAKE_RANLIB=$BOOTSTRAP/bin/llvm-ranlib \
      -DCMAKE_LINKER=$BOOTSTRAP/bin/ld.lld \
      -DCMAKE_C_FLAGS="-fuse-ld=lld -fPIC -stdlib=libc++ -Qunused-arguments" \
      -DCMAKE_CXX_FLAGS="-fuse-ld=lld -fPIC -stdlib=libc++ -Qunused-arguments" \
      -DCMAKE_EXE_LINKER_FLAGS="-rtlib=compiler-rt -unwindlib=libunwind -L$FINAL/lib" \
      -DCMAKE_SHARED_LINKER_FLAGS="-rtlib=compiler-rt -unwindlib=libunwind -L$FINAL/lib" \
      -DLLVM_TABLEGEN=$BOOTSTRAP/bin/llvm-tblgen \
      -DLLVM_OPTIMIZED_TABLEGEN=On \
      -DLLVM_CONFIG_PATH=$BOOTSTRAP/bin/llvm-config \
      -DLLVM_ENABLE_LIBCXX=On \
      -DLLVM_DEFAULT_TARGET_TRIPLE=%{triple} \
      -DLLVM_BINUTILS_INCDIR=/usr/include \
      -DLLVM_ENABLE_LLD=On \
      -DLLVM_ENABLE_PROJECTS="clang;lld;openmp;libclc;clang-tools-extra;polly;compiler-rt;libunwind;libcxxabi;libcxx" \
      -DLLVM_TARGETS_TO_BUILD=%{build_target} \
      -DLLVM_LINK_LLVM_DYLIB=On \
      -DLLVM_BUILD_LLVM_DYLIB=On \
      -DLLVM_BUILD_STATIC=Off \
      -DLLVM_DYLIB_COMPONENTS=all\
      -DLLVM_INCLUDE_DOCS=Off \
      -DLLVM_INCLUDE_BENCHMARKS=Off \
      -DLLVM_ENABLE_Z3_SOLVER=Off \
      -DLLVM_INSTALL_UTILS=On \
      -DLLVM_ENABLE_ZLIB=On \
      -DLLVM_ENABLE_MODULES=On \
      -DLLVM_ENABLE_RTTI=On \
      -DLLVM_ENABLE_FFI=On \
      -DLLVM_ENABLE_EH=Off \
      -DLLVM_USE_INTEL_JITEVENTS=On \
      -DLLVM_USE_PERF=On \
      -DLLVM_BUILD_TESTS=Off \
      -DLLVM_ENABLE_PIC=On \
      -DLLVM_INSTALL_TOOLCHAIN_ONLY=On \
      -DLLVM_INSTALL_CCTOOLS_SYMLINKS=On \
      -DCLANG_DEFAULT_LINKER=lld \
      -DCLANG_PLUGIN_SUPPORT=On \
      -DCLANG_DEFAULT_RTLIB=compiler-rt \
      -DCLANG_DEFAULT_UNWINDLIB=libunwind \
      -DCLANG_DEFAULT_CXX_STDLIB=libc++ \
      -DLIBUNWIND_USE_COMPILER_RT=On \
      -DLIBUNWIND_ENABLE_STATIC=Off \
      -DCOMPILER_RT_USE_LIBCXX=On \
      -DCOMPILER_RT_BUILD_BUILTINS=On \
      -DLIBCXXABI_USE_LLVM_UNWINDER=On \
      -DLIBCXXABI_USE_COMPILER_RT=On \
      -DLIBCXXABI_ENABLE_STATIC=Off \
      -DLIBCXX_CXX_ABI=libcxxabi \
      -DLIBCXX_USE_COMPILER_RT=On \
      -DLIBCXX_ENABLE_SHARED=On \
      -DLIBCXX_ENABLE_STATIC=Off \
      -DLIBCXX_CXX_ABI_INCLUDE_PATHS="$MAIN/libcxxabi/include" \
      -DLIBOMP_ENABLE_SHARED=On \
      -DLIBOMP_ENABLE_STATIC=Off \
      -DLIBOMP_LIBFLAGS="-lm" \
      -DLIBOMP_FORTRAN_MODULES=Off \
      -DLIBOMP_COPY_EXPORTS=Off \
      -DLIBOMP_USE_HWLOC=Off \
      -DLIBOMP_OMPT_SUPPORT=On \
      -Wno-dev $MAIN/llvm


cmake --build . %{_smp_mflags}
# End stage 2


%install
module load cmake

cd build/stage2
cmake -DCMAKE_INSTALL_PREFIX="%{buildroot}%{install_path}" -P cmake_install.cmake

# OpenHPC module files
%{__mkdir_p} %{buildroot}/%{OHPC_MODULES}/llvm%{major_ver}
%{__cat} << EOF > %{buildroot}/%{OHPC_MODULES}/llvm%{major_ver}/%{version}
#%Module1.0#####################################################################

proc ModulesHelp { } {

puts stderr " "
puts stderr "This module loads the LLVM compiler infrastructure"
puts stderr " "

puts stderr "\nVersion %{version}\n"

}
module-whatis "Name: LLVM Compiler Infrastructure"
module-whatis "Version: %{version}"
module-whatis "Category: compiler, runtime support"
module-whatis "Description: The LLVM Compiler Infrastructure"
module-whatis "URL: http://www.llvm.org"

set     version           %{version}

setenv         LLVM%{major_ver}_PATH         %{install_path}
prepend-path   PATH               %{install_path}/bin
prepend-path   MANPATH            %{install_path}/share/man
prepend-path   INCLUDE            %{install_path}/include/c++/v1
prepend-path   LD_LIBRARY_PATH    %{install_path}/lib
prepend-path   MODULEPATH         %{OHPC_MODULEDEPS}/llvm%{major_ver}

setenv         F18_FC             gfortran

family "compiler"
EOF

%{__cat} << EOF > %{buildroot}/%{OHPC_MODULES}/llvm%{major_ver}/.version.%{version}
#%Module1.0#####################################################################
##
## version file for %{pname}-%{version}
##
set     ModulesVersion      "%{version}"
EOF


%files
%{OHPC_MODULES}/llvm%{major_ver}
%dir %{OHPC_COMPILERS}/llvm
%{install_path}
%doc llvm/CODE_OWNERS.TXT
%doc llvm/CREDITS.TXT
%doc llvm/README.txt
%doc llvm/RELEASE_TESTERS.TXT
%license llvm/LICENSE.TXT
