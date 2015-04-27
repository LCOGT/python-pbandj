#!/usr/bin/python
# Copyright (C) 2009  Las Cumbres Observatory <lcogt.net>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
'''__init__.py 

This package contains classes providing a mappings between Django models
and Protocol Buffer messages and RPC services

Authors: Zach Walker (zwalker@lcogt.net)
Dec 2009
'''

# Point django settings to dummy settings if not have already been set
import os
if not os.environ.has_key('DJANGO_SETTINGS_MODULE'):
    print "WARNING: Using dummy django settings"
    os.environ['DJANGO_SETTINGS_MODULE'] = 'pbandj.dummy_settings'