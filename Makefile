# 
#   Copyright (C) 2017   Free Software Foundation, Inc.
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 

# This uses https://github.com/kivy/python-for-android to produce apks for Android,
# and a zip file for python pip.

PACKAGE := org.gosm.py
NAME := Gosm
BOOTSTRAP := sdl2		# pygame
REQUIREMENTS := kivy 
VERSION := 0.1
ARCH := armeabi-v7a
P4ABIN = /usr/local/bin/p4a
P2VER := python2
P3VER := python3crystax
DEFS := --private `pwd` --arch=${ARCH} --package=${PACKAGE} --name "${NAME}" --version ${VERSION} --bootstrap=${BOOTSTRAP} 

all: pip
	echo "Nothing to do..."

# Make a python2 apk for Android
apk2:
	${P4ABIN} apk ${DEFS} --requirements=${P2VER},${REQUIREMENTS}

# Make a python3 apk for Android
apk3:
	${P4ABIN} apk --private `pwd` --arch=${ARCH} --package=${PACKAGE} --name "${NAME}" --version ${VERSION} --bootstrap=${BOOTSTRAP} --requirements=${P3VER},${REQUIREMENTS}

# Make a python package for pip
pip:
	zip -r gosm.zip osmpylib/*.py

pip3-install:
	pip3 install --upgrade -e osmpylib

pip3-uninstall:
	pip3 uninstall Gosm

pip2-uninstall:
	pip2 uninstall Gosm

# Run regression tests
check:
	osmpylib/test.py

xforms:
