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
'''type_map.py - Type mapping definitions for Django fields that
don't map onto protocol buffer field types directly.

Authors: Zach Walker (zwalker@lcogt.net)
Dec 2009
'''

from __future__ import division
from datetime import datetime, time


import type_map_base as base
from django.db import models
from model import ProtocolBuffer


def Time():
    try:
        Time.instance
    except:
        time = ProtocolBuffer.Message('Time')
        time.addField(ProtocolBuffer.Field(ProtocolBuffer.Field.REQUIRED,
                                           'hour',
                                           base.PB_TYPE_INT32))
        time.addField(ProtocolBuffer.Field(ProtocolBuffer.Field.REQUIRED,
                                           'minute',
                                           base.PB_TYPE_INT32))
        time.addField(ProtocolBuffer.Field(ProtocolBuffer.Field.REQUIRED,
                                           'second',
                                           base.PB_TYPE_INT32))
        #time.addField(ProtocolBuffer.Field(ProtocolBuffer.Field.REQUIRED,
        #                                  'micro',
        #                                   base.PB_TYPE_INT32))
        Time.instance = time
    return Time.instance



def Date():
    try:
        Date.instance
    except:
        date = ProtocolBuffer.Message('Date')
        date.addField(ProtocolBuffer.Field(ProtocolBuffer.Field.REQUIRED,
                                          'day',
                                          base.PB_TYPE_INT32))
        date.addField(ProtocolBuffer.Field(ProtocolBuffer.Field.REQUIRED,
                                          'month',
                                          base.PB_TYPE_INT32))
        date.addField(ProtocolBuffer.Field(ProtocolBuffer.Field.REQUIRED,
                                          'year',
                                          base.PB_TYPE_INT32))
        date.addField(ProtocolBuffer.Field(ProtocolBuffer.Field.OPTIONAL,
                                          'time',
                                          Time()))
        Date.instance = date
    return Date.instance

#def _buildFile():
#    try:
#        _buildFile.file
#    except:
#        file = ProtocolBuffer.Message('File')
#        file.addField(ProtocolBuffer.Field(ProtocolBuffer.Field.REQUIRED,
#                                           'name',
#                                           base.PB_TYPE_STRING))
#        file.addField(ProtocolBuffer.Field(ProtocolBuffer.Field.REQUIRED,
#                                           'path',
#                                           base.PB_TYPE_STRING))
#        file.addField(ProtocolBuffer.Field(ProtocolBuffer.Field.OPTIONAL,
#                                           'data',
#                                           base.PB_TYPE_BYTES))
#        file.addField(ProtocolBuffer.Field(ProtocolBuffer.Field.OPTIONAL,
#                                           'size',
#                                           base.PB_TYPE_INT32))
#        file.addField(ProtocolBuffer.Field(ProtocolBuffer.Field.OPTIONAL,
#                                           'url',
#                                           base.PB_TYPE_STRING))
#        _buildFile.file = file
#    return _buildFile.file

def _buildDJ2PB():
    map = base.DJ2PB
    map[models.TimeField] = Time()
    map[models.DateField] = Date()
    map[models.DateTimeField] = Date()
    #map[models.FileField] = _buildFile()
    return map

def _buildDjangoProto():
    pb = ProtocolBuffer('django_types', 'org.lcogt.protobuf')
    pb.addMessage(Date())
    pb.addMessage(Time())
    #pb.addMessage(_buildFile())
    return pb

DJ2PB = _buildDJ2PB() 
PB2DJ = [(val,key) for (key,val) in DJ2PB.items()]
DJANGO_PROTO = _buildDjangoProto()

# TODO: Add a recursion depth limit
# TODO: Prevent circular recursion        
def genMsg(msg_name, django_model_class, include=[], exclude=[], recurse_fk=True, no_recurse=[]):
    """ Create a protocol buffer message from a django type.
        By default all args will be included in the new message.
        If recurse_fk is set messages will also be created for foreign key
        types.  A list of generated messages will be returned.
        Accepted Args:
        msg_name -- (String) The name of the message
        django_model_class -- (Type) A reference to the django
                              model type
        included -- (List) A list of field names from the model to
                  be included in the mapping
        exclude -- (List) A list of field names to exclude from the
                  model.  Only used if included arg is []
        recurse_fk -- Flag for recursing into foreign key fields if true or 
                   using pk if false
        no-recurse -- List of field names which should not be recursed.
                      Only used if recurse_fk=True
    """
    Field = ProtocolBuffer.Field
    Enum = ProtocolBuffer.Enumeration
    #messages = {}
    root_msg = ProtocolBuffer.Message(msg_name, django_model_class)
    #messages[msg_name] = root_msg
    
    # Local fields
    django_class_fields = [field for field in 
                           django_model_class._meta.local_fields +
                           django_model_class._meta.many_to_many]
    django_field_by_name = {}
    
    # Iterate through Django fields and init dict that allows
    # lookup of fields by name.
    for field in django_class_fields:
        django_field_by_name[field.name] = field
    #[django_field_by_name.__setitem__(field.name, field) for field in
    #    django_class_fields]
    
    # Remove excluded fields or add included fields
    field_set = set()
    if include != []: 
        # Assert that the fields all exist
        include_set = set(include)
        assert include_set == set(django_field_by_name.keys()) & include_set
        field_set = include_set
    else:
        useable_field_names = set(django_field_by_name.keys()) - set(exclude)
        field_set = useable_field_names
    
    # Add a pb field to the pb msg for each django field in the set
    new_fields = []
    for field_name in field_set:
        field = django_field_by_name[field_name]
        #pb_usage = Field.OPTIONAL
        #pb_type = None
        #pb_field_name = field.name
        if isinstance(field, models.ForeignKey):
            if recurse_fk and not field.name in no_recurse:
                # Create a new msg type from the parent table in the fk relation
                fk_dj_model = field.rel.to
                if isinstance(fk_dj_model, str):
                    # TODO: Handle ForeignKey supplied as a str
                    #print fk_dj_model
                    assert False
                    #fk_dj_model = models.__dict__[fk_dj_model]
                pb_type = genMsg(fk_dj_model.__name__, fk_dj_model, recurse_fk=recurse_fk)
                new_fields.append(Field(Field.OPTIONAL, field.name,
                                        pb_type, field))
                # TODO: Change msg name to avoid name collision at the ProtocolBuffer level
            #else:
                # Use the pk from the foreign key relation as the value
            pb_type = DJ2PB.get(type(field))()
            new_fields.append(Field(Field.OPTIONAL, field.name + '_id',
                                    pb_type, field))
        elif isinstance(field, models.ManyToManyField):
            # If there is a 'through' model, add a repeated field for the through
            # data even if recurse_fk == False. If there is no through model and
            # recrse_fk == False then add repeated reference to fk object pk's.
            #pb_usage = Field.REPEATED
            if not field.rel.through is None:
                # There is data associated with the relation
                # Generate a msg from assoc model excluding fk reference
                # back to the parent type to prevent circular references
                m2m_dj_model = field.rel.through_model
                recur_rel_fields = [] # Fields which would cause a recursive relation
                for assoc_field in m2m_dj_model._meta._fields():
                    if (isinstance(assoc_field, models.ForeignKey) and
                        assoc_field.rel.to == django_model_class):
                        recur_rel_fields.append(assoc_field.name)
                pb_type = genMsg(m2m_dj_model.__name__, m2m_dj_model, recurse_fk=recurse_fk, no_recurse=recur_rel_fields)
                new_fields.append(Field(Field.REPEATED, field.name,
                                        pb_type, field))
                # TODO: Change msg name to avoid name collision at the ProtocolBuffer level
            else:
                # No data associated with the relation
                # Just like a foreign key but repeated
                if recurse_fk and not field.name in no_recurse:
                    m2m_dj_model = field.rel.to
                    pb_type = genMsg(m2m_dj_model.__name__, m2m_dj_model, recurse_fk=recurse_fk)
                    new_fields.append(Field(Field.REPEATED, field.name,
                                            pb_type, field))
                #else:
                    #pb_field_name += '_id'
                pb_type = DJ2PB.get(type(field))()
                new_fields.append(Field(Field.REPEATED, field.name + '_id',
                                        pb_type, field))
            #print field.rel.to, field.rel.through             
        else: # Not a Foreign Key
            # Add an enumeration for each django field with choices set
            if(field.choices):
                field_enum = Enum(field_name, [a for a,b in field.choices],
                                  "Generated from 'choices' for django model field: %s.%s" % (django_model_class.__name__, field.name))
                root_msg.enums.append(field_enum)
                pb_type = field_enum
            else:
                if isinstance(DJ2PB.get(type(field)), ProtocolBuffer.Message):
                    #TODO: The pb type here should be the generated pb2 message class or and instance of a metaclass
                    pb_type = DJ2PB.get(type(field))
                else:
                    pb_type = DJ2PB.get(type(field))()
            new_fields.append(Field(Field.OPTIONAL, field.name,
                                    pb_type, field))
        #pb_field = Field(pb_usage, pb_field_name, pb_type, field)
        #root_msg.addField(pb_field)
    root_msg.addField(*new_fields)
    return root_msg

