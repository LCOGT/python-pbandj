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
'''pbandj.py - Functions for generating .proto files and
pyhton modules.

Authors: Zach Walker (zwalker@lcogt.net)
Dec 2009
'''


from os import system

from type_map import DJANGO_PROTO
from model import ProtocolBuffer

def _genProto(proto, path="."):
    f = open(path + "/" + proto.proto_filename(), 'w')
    f.write(proto.__str__())
    f.close()

def genProto(proto, path="."):
    if proto != DJANGO_PROTO and not(DJANGO_PROTO in proto.imports):
        proto.imports.append(DJANGO_PROTO)
    protos = (DJANGO_PROTO, proto)
    for proto in protos:
        _genProto(proto, path)


def genMod(proto, path="."):
    """ Generate a python module for this Protocol Buffer.
        The default name is genereated_pb2.py unless specified.
        Accepted Arguments:
        path -- (String) The path, relative or fully qualified,
                to the directory where the generated module will
                be created
    """
    genProto(proto, path)
    modules = proto.imports + [proto]
    for mod in modules:
        if type(mod) is ProtocolBuffer:
            mod = mod.proto_filename()
        system("protoc --python_out=" + path +
               " --proto_path=" + path + " " +
               path + "/" + mod)
               
    return proto.module_name + "_pb2"