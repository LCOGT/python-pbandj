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
'''type_map_base.py - Type mapping definitions for Django fields to
protocol buffer fields

Authors: Zach Walker (zwalker@lcogt.net)
Dec 2009
'''

from django.db import  models


def _make_type(name, ptype):
    return type(name, (), {'name': name,
                           'ptype': ptype,
                           '__eq__': lambda x,y: isinstance(y, x.__class__) and x.ptype == y.ptype,
                           '__ne__': lambda x,y: not x.__eq__(y)})

PB_TYPE_STRING  = _make_type('PB_TYPE_STRING', 'string')
PB_TYPE_DOUBLE  = _make_type('PB_TYPE_DOUBLE','double')
PB_TYPE_INT32   = _make_type('PB_TYPE_INT32','int32')
PB_TYPE_INT64   = _make_type('PB_TYPE_INT64','int64')
PB_TYPE_UINT32  = _make_type('PB_TYPE_UINT32','uint32')
PB_TYPE_UINT64  = _make_type('PB_TYPE_UINT64','uint64')
PB_TYPE_SINT32  = _make_type('PB_TYPE_SINT32','sint32')
PB_TYPE_SINT64  = _make_type('PB_TYPE_SINT64','sint64')
PB_TYPE_FINT32  = _make_type('PB_TYPE_FINT32','fixed32')
PB_TYPE_FINT64  = _make_type('PB_TYPE_FINT64','fixed64')
PB_TYPE_SFINT32 = _make_type('PB_TYPE_SFINT32','sfixed32')
PB_TYPE_SFINT64 = _make_type('PB_TYPE_SFINT64','sfixed64')
PB_TYPE_FLOAT   = _make_type('PB_TYPE_FLOAT','float')
PB_TYPE_BOOL    = _make_type('PB_TYPE_BOOL','bool')
PB_TYPE_BYTES   = _make_type('PB_TYPE_BYTES','bytes')


#PB_TYPE_STRING  = type('PB_TYPE_STRING', (), {'ptype': 'string'})
#PB_TYPE_DOUBLE  = type('PB_TYPE_DOUBLE', (), {'ptype': 'double'})
#PB_TYPE_INT32   = type('PB_TYPE_INT32', (), {'ptype': 'int32'})
#PB_TYPE_INT64   = type('PB_TYPE_INT64', (), {'ptype': 'int64'})
#PB_TYPE_UINT32  = type('PB_TYPE_UINT32', (), {'ptype': 'uint32'})
#PB_TYPE_UINT64  = type('PB_TYPE_UINT64', (), {'ptype': 'uint64'})
#PB_TYPE_SINT32  = type('PB_TYPE_SINT32', (), {'ptype': 'sint32'})
#PB_TYPE_SINT64  = type('PB_TYPE_SINT64', (), {'ptype': 'sint64'})
#PB_TYPE_FINT32  = type('PB_TYPE_FINT32', (), {'ptype': 'fixed32'})
#PB_TYPE_FINT64  = type('PB_TYPE_FINT64', (), {'ptype': 'fixed64'})
#PB_TYPE_SFINT32 = type('PB_TYPE_SFINT32', (), {'ptype': 'sfixed32'})
#PB_TYPE_SFINT64 = type('PB_TYPE_SFINT64', (), {'ptype': 'sfixed64'})
#PB_TYPE_FLOAT   = type('PB_TYPE_FLOAT', (), {'ptype': 'float'})
#PB_TYPE_BOOL    = type('PB_TYPE_BOOL', (), {'ptype': 'bool'})
#PB_TYPE_BYTES   = type('PB_TYPE_BYTES', (), {'ptype': 'bytes'})


DJ2PB = {models.CharField: PB_TYPE_STRING,
         models.DecimalField: PB_TYPE_DOUBLE,
         models.IntegerField: PB_TYPE_INT32,
         models.FloatField: PB_TYPE_FLOAT,
         models.DateTimeField: PB_TYPE_STRING,
         models.DateField: PB_TYPE_STRING,
         models.BooleanField: PB_TYPE_BOOL,
         models.NullBooleanField: PB_TYPE_BOOL,
         models.CommaSeparatedIntegerField: PB_TYPE_STRING,
         models.EmailField : PB_TYPE_STRING,
         models.FileField: PB_TYPE_STRING,
         models.FilePathField:  PB_TYPE_STRING,
         models.ImageField: PB_TYPE_STRING,
         models.IPAddressField: PB_TYPE_STRING,
         models.PositiveIntegerField: PB_TYPE_UINT32,
         models.PositiveSmallIntegerField: PB_TYPE_UINT32,
         models.SlugField: PB_TYPE_STRING,
         models.SmallIntegerField: PB_TYPE_INT32,
         models.TextField: PB_TYPE_STRING,
         models.TimeField: PB_TYPE_STRING,
         models.URLField: PB_TYPE_STRING,
         models.XMLField: PB_TYPE_STRING,
         models.AutoField: PB_TYPE_INT32,
         models.ForeignKey: PB_TYPE_INT32,
         # TODO: Add a ManyToManyField mapping
         models.ManyToManyField: PB_TYPE_INT32 
         }

PB2DJ = dict([(DJ2PB[key], key) for key in DJ2PB])
