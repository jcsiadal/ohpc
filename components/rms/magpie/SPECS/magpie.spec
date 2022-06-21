#----------------------------------------------------------------------------bh-
# This RPM .spec file is part of the OpenHPC project.
#
# It may have been modified from the default version supplied by the underlying
# release package (if available) in order to apply patches, perform customized
# build/install configurations, and supply additional files to support
# desired integration conventions.
#
#----------------------------------------------------------------------------eh-
#
#  Copyright (C) 2013-2015 Lawrence Livermore National Security, LLC.
#  Produced at Lawrence Livermore National Laboratory (cf, DISCLAIMER).
#  Written by Albert Chu <chu11@llnl.gov>
#  LLNL-CODE-644248
#
#  This file is part of Magpie, scripts for running Hadoop on
#  traditional HPC systems.  For details, see https://github.com/llnl/magpie.
#
#  Magpie is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  Magpie is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Magpie.  If not, see <http://www.gnu.org/licenses/>.
#

%include %{_sourcedir}/OHPC_macros
%global pname magpie

Summary: Scripts for running Big Data software in HPC environments
Name: %{pname}%{PROJ_DELIM}
Version: 3.0
Release: 1%{?dist}
License: GPLv2
URL: https://github.com/LLNL/magpie
Group: %{PROJ_NAME}/rms
Source0: https://github.com/LLNL/magpie/archive/%{version}.tar.gz

# Java 8 (javac) or greater required on all cluster nodes.
BuildRequires: python3-rpm-macros
Requires: java-devel >= 1.8
Requires: python3

#!BuildIgnore: post-build-checks

%global install_path %{OHPC_UTILS}/%{pname}

%description
Magpie contains a number of scripts for running Big Data software in
HPC environments. Thus far, Hadoop, Spark, Hbase, Storm, Pig, Phoenix,
Kafka, Zeppelin, Zookeeper, and Alluxio are supported. It currently supports
running over the parallel file system Lustre and running over any generic
network filesytem. There is scheduler/resource manager support for Slurm, Moab,
Torque, and LSF.


%prep
%setup -q -n %{pname}-%{version}


%build
# Fix-up file permissions and shebang data that cause warnings/errors in OBS
# Not using `install` command in next section due to very large file count
find doc -type f -exec chmod -R -x {} \;
find conf -type f -exec chmod -R -x {} \;
find examples -type f -exec chmod -R -x {} \;
find patches -type f -exec chmod -R -x {} \;
chmod -x magpie/job/magpie-job-ray-rayips.py
chmod -x magpie/job/magpie-job-tensorflow-horovod-synthetic-benchmark.py
chmod -x magpie/job/magpie-job-tensorflow-tfadd.py
chmod -x submission-scripts/script-templates/magpie-hive
chmod -x testsuite/testscripts/test-ray.py
chmod -x testsuite/testscripts/test-tensorflow.py
chmod +x testsuite/test-config.sh
for script in $(grep "^#!/usr/bin/env bash" conf); do
   sed -i "s#/usr/bin/env bash#/bin/bash#" $script
   chmod +x $script
done

find . -name \.gitignore -type f -delete
rm .travis.yml

%install
mkdir -p -m 755 ${RPM_BUILD_ROOT}%{install_path}
cp -a . ${RPM_BUILD_ROOT}%{install_path}

# OpenHPC module file
mkdir -p %{buildroot}/%{OHPC_MODULES}/%{pname}
cat << EOF > %{buildroot}/%{OHPC_MODULES}/%{pname}/%{version}.lua
help([[
This module loads Magpie scripts

Version %{version}
]])

whatis("Name: Magpie ")
whatis("Version: %{version}")
whatis("Category: Resource Managers")
whatis("Description: Scripts for running Big Data in HPC environments")
whatis("URL: https://github.com/LLNL/magpie")

# JAVA_HOME must be set; locate "javac" in PATH
if not os.gettenv("JAVA_HOME") then
   print("ERROR: JAVA_HOME not set.")
   os.exit 1
else
   if os.execute("which javac") ~= 0 then
   print("ERROR: javac command not found")
   os.exit 1
end

local version = "%{version}"
setenv("MAGPIE_PATH", "%{install_path}")
setenv          MAGPIE_SCRIPTS_HOME %{install_path}
setenv          %{PNAME}_DIR        %{install_path}
EOF

cat << EOF > %{buildroot}/%{OHPC_MODULES}/%{pname}/.version.%{version}.lua
-- version file for %{pname}-%{version}
local ModulesVersion = "%{version}"
EOF


%files
%{install_path}
%doc doc/* NEWS README.md TODO VERSION
%license COPYING DISCLAIMER
%{OHPC_MODULES}/%{pname}
