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
'''conversion.py - Handlers for mapping Django models and fields to
protocol buffer messages and fields

Authors: Zach Walker (zwalker@lcogt.net)
Dec 2009
'''


import decimal
from datetime import datetime, time
import traceback

from model import ProtocolBuffer
from django.db import models
from type_map import Date, Time
import type_map_base as types
import django_types_pb2 as proto



def _date_dj2pb(val, kwargs):
    '''Convert Django DateField to a protocol buffer Date message'''
    date = proto.Date()
    date.year = val.year
    date.month = val.month
    date.day = val.day
    return date

def _date_pb2dj(val, kwargs):
    '''Convert a protocol buffer Date msg to a Django DateField'''
    return datetime(val.year, val.month, val.day)
    
def _datetime_dj2pb(val, kwargs):
    '''Convert Django DateTimeField to a protocol buffer Date message'''
    date = proto.Date()
    date.year = val.year
    date.month = val.month
    date.day = val.day
    date.time.hour = val.hour
    date.time.minute = val.minute
    date.time.second = val.second
    #date.time.micro = val.microsecond
    return date

def _datetime_pb2dj(val, kwargs):
    '''Convert protocol buffer Date msg to Django DateTimeField'''
    return datetime(val.year, val.month, val.day, val.time.hour,
                    val.time.minute, val.time.second)#, val.time.micro)
    
def _time_dj2pb(val, kwargs):
    '''Convert  Django TimeField to a protocol buffer Time msg'''
    time = proto.Time()
    time.hour = val.hour
    time.minute = val.minute
    time.second = val.second
    #time.micro = val.microsecond
    return time

def _time_pb2dj(val, kwargs):
    '''Convert protocol buffer Time msg to Django TimeField'''
    file = models.FileField
    return time(val.hour, val.minute, val.second)#, val.micro)

def _m2m_pb2dj(val, kwargs):
    output_type = kwargs['output_type']
    model_type = output_type.to
    if not output_type.through is None:
        model_type = output_type.through
    if isinstance(model_type, str):
        model_type = models.__dict__[model_type]
    return model_type.objects.get(pk=val)


#def _file_dj2pb(val, kwargs):
#    '''Convert Django FileField to protocol buffer File msg'''
#    file = proto.File()
#    file.name = val.name
#    file.path = val.path
#    file.url = val.url
#    file.size = val.size 
#
#def _file_pb2dj(val, kwargs):
#    '''Convert protocol buffer File msg to a Django FileField'''
#    file = {'name':val.name, 'content':val.data, 'save':True}
#    return file

class Converter(object):
    
    def __init__(self):
        #TODO: Change django type portion of key to type rather than string
        conv_helpers = {}
        #Django seems to require float values input as a string
        conv_helpers[(types.PB_TYPE_DOUBLE,
                       models.DecimalField)] = lambda val, kwargs : str(val)
        #Convert Decimal back to a python float which is the same as a double
        #in protocol buffers apparently
        conv_helpers[(models.DecimalField,
                     types.PB_TYPE_DOUBLE)] = lambda val, kwargs : decimal.Decimal(val).__float__()
        #Help convert a Django DateTimeField into a consistent string format
        #for transport
        conv_helpers[(models.DateTimeField,
                      types.PB_TYPE_STRING)] = lambda val, kwargs : val.strftime("%Y-%m-%d %H:%M:%S")
        #Help convert a Django DateField into a consistent string format for transport
        conv_helpers[(models.DateField,
                      types.PB_TYPE_STRING)] = lambda val, kwargs : val.strftime("%Y-%m-%d")
        #Help convert a string into a Django DateTimeField
        conv_helpers[(types.PB_TYPE_STRING,
                      models.DateTimeField)] = \
                          lambda val, kwargs : datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
        #Help convert a string into a  Django DateField
        conv_helpers[(types.PB_TYPE_STRING,
                      models.DateField)] = \
                          lambda val, kwargs : datetime.strptime(val, "%Y-%m-%d")
        conv_helpers[(models.FileField,
                      types.PB_TYPE_STRING)] = \
                          lambda val, kwargs : val.name
                          
        conv_helpers[(models.ImageField,
                      types.PB_TYPE_STRING)] = \
                          lambda val, kwargs : val.name
                          
        conv_helpers[(ProtocolBuffer.Enumeration, models.CharField)] = \
                          lambda val, kwargs: dict([(b,a) for a,b in kwargs['input_type'].dj2val.items()])[val]
        
        conv_helpers[(models.CharField, ProtocolBuffer.Enumeration)] = \
                          lambda val, kwargs: kwargs['output_type'].dj2val[val]
                          
        conv_helpers[(models.ForeignKey, types.PB_TYPE_INT32)] = \
                          lambda val, kwargs: val.pk
                          
        conv_helpers[(types.PB_TYPE_INT32, models.ForeignKey)] = \
                          lambda val, kwargs: kwargs['output_type'].related.parent_model.objects.get(pk=val).pk
                          
        conv_helpers[(models.ForeignKey, ProtocolBuffer.Message)] = \
                          lambda val, kwargs: self.toProtoMsg(kwargs['pb'], val, kwargs['module'])
                          #self.convert(kwargs['input_type'], kwargs['output_type'], val)
        conv_helpers[(ProtocolBuffer.Message, models.ForeignKey)] = \
                          lambda val, kwargs: self.toDjangoObj(kwargs['pb'], val)
                          #lambda val, kwargs: self.convert(kwargs['input_type'], kwargs['output_type'], val)
        conv_helpers[(models.ManyToManyField, types.PB_TYPE_INT32)] = \
                          lambda val, kwargs : val.pk
        conv_helpers[(types.PB_TYPE_INT32, models.ManyToManyField)] = \
                          lambda val, kwargs : _m2m_pb2dj(val, kwargs)
        conv_helpers[(models.ManyToManyField, ProtocolBuffer.Message)] = \
                          lambda val, kwargs : self.toProtoMsg(kwargs['pb'], val, kwargs['module'])
        conv_helpers[(ProtocolBuffer.Message, models.ManyToManyField)] = \
                          lambda val, kwargs : val
        
        #Help convert string to Django comma separated integer
        #conv_helpers[(types.PB_TYPE_STRING,
        #              models.CommaSeparatedIntegerField)] = \
        #                  lambda val, kwargs : eval(val)
        #conv_helpers[(models.CommaSeparatedIntegerField,
        #              types.PB_TYPE_STRING)] = \
        #                  lambda val, kwargs : str(val)
        
        conv_helpers[(models.DateTimeField, ProtocolBuffer.Message)] = _datetime_dj2pb
        conv_helpers[(models.DateField, ProtocolBuffer.Message)] = _date_dj2pb
        conv_helpers[(models.TimeField, ProtocolBuffer.Message)] = _time_dj2pb
        #helpers[(models.FileField, _buildFile())] = _file_dj2pb
        conv_helpers[(ProtocolBuffer.Message, models.DateField)] = _date_pb2dj
        conv_helpers[(ProtocolBuffer.Message, models.DateTimeField)] = _datetime_pb2dj
        conv_helpers[(ProtocolBuffer.Message, models.TimeField)] = _time_pb2dj
        #helpers[(_buildFile(), models.FileField)] = _file_pb2dj
        self.helpers = conv_helpers

    def addConvHelper(self, input_type, output_type, helper):
        '''Add a conversion helper to go from the supplied input type to
           output type by calling the helper function.  Helper should
           take have the format helper(val, kwargs).  Args passed to the
           helper by keyword will be input_type and output_type
        '''
        self.helpers[(input_type, output_type)] = helper

    def convert(self, input_type, output_type, val, **kwargs):
        '''Convert the input object to the output type and return an object of
           output type.  If there is not an existing mapping and conversion 
           helper between the type(input_obj) and output_type the input_obj
           will be returned unchanged
        '''
        #print input_type, output_type, val
        helper = self.helpers.get((type(input_type), type(output_type)), lambda x, kwargs : x)
        kwargs['input_type'] = input_type
        kwargs['output_type'] = output_type
        return helper(val, kwargs)

    def toDjangoObj(self, pb, obj, dest_obj=None):
            """ Take a protocol buffer object whose class was generated by
                this objcet and marshall a Django object
                Accepted Args:
                pb -- ProtocolBuffer object defining the relation 
                obj -- (google.protobuf.Message) The object to be converted
                dest_obj -- A django object of the proper type to which all
                            mapped fields will be copied
            """
            # Find the message mapping
            pb_msg_name = obj.__class__.__name__
            message = pb.messages[pb_msg_name]
            
            # Break message fields down into name keyed dict objects
            # by type of field 
            mapped_fields = dict([(field.name, field) for field in
                                  message.mapped_fields])
            composite_msg_fields = dict([(field.name, field) for field in
                                          message.message_fields])
            unmapped_fields = dict([(field.name, field) for field in
                                     message.fields])
    
            # Create a new django target message for this given type
            if message.django_model_class == None:
                raise Exception("No django model associated with pb msg type %s" %
                                pb_msg_name)
            if(not dest_obj is None):
                if isinstance(dest_obj, message.django_model_class):
                    # TODO: Add unittest for this case
                    dj_obj = dest_obj
                else:
                    # TODO: Add unittest for this case 
                    raise Exception("dest_obj type %s doesn't match model type %s" % 
                                    (type(dest_obj), message.django_model_class))
            else:
                dj_obj = message.django_model_class()
            
            # Iterate through msg fields and convert to django types
            for (field, val) in obj.ListFields():
                if field.name in composite_msg_fields:
                    # This is a composite field that requires special handling
                    pass
                elif field.name in unmapped_fields:
                    # ignore this field it isn't mapped
                    pass
                else:
                    if mapped_fields[field.name].usage == ProtocolBuffer.Field.REPEATED:
                        # repeated fields imply some kind of foreign key relationship
                        # requires special handling
                        # Django doesn't make it easy to add relation fields to an
                        # object without first saving it.
                        pass
                    else:
                        # This is an optional or required directly mappable field
                        mapped_field = mapped_fields[field.name]
                        dj_val = self.convert(mapped_field.pb_type,
                                              mapped_field.dj_type,
                                              val, pb=pb)
                        # For a foreign key, we set 'field_id' to the pk of the related value 
                        setattr(dj_obj, mapped_field.name, dj_val)
            return dj_obj
    
    
    def toProtoMsg(self, pb, obj, module, dest_obj=None):
        """ Take a django object for which a protocol buffer message
            has been generated and return a related protocol buffer
            message.  Since the python implementation of protocol
            buffers uses factory methods to create field instances
            of nested messages, use the dest_obj arg to
            do the type conversion for you.
            Ex. pbuf.toProtoMsg(obj=django_obj, dest_obj=my_msg.field.add())
            Accepted Args:
            pb -- ProtocolBuffer object defining the relation 
            obj -- (django Model) The object to be converted
            module -- protocol buffer module generate from .proto file modeled by pb
            dest_obj -- (Message) An instance of the message class
                        that is related to the django object arg.
                        Instead of creating a new object this obj
                        will be loaded with data and returned
        """
        # Import the message type and instantiate if necessary
        dj_type = type(obj)
        # Try to get the type using the django class name
        message = pb.messages.get(dj_type)
        msg_type = getattr(module, message.name, None)
        if msg_type == None:
            raise Exception("No mapping available for django type %s." % dj_type)
        
            
        if dest_obj is None:
            protoMsg = msg_type()
        else:
            protoMsg = dest_obj
        
        # Get the pb message type and convert the django message    
        for field in message.mapped_fields:
            if field.usage == ProtocolBuffer.Field.REPEATED:
                # Must be a ManyToMany type relation
                val_list = []
                if not field.dj_type.rel.through is None:
                    # Get the association model
                    assoc_model = field.dj_type.rel.through_model
                    # Access it through the parent type member names 'modelclass_set'
                    val_list = getattr(obj, assoc_model.__name__.lower() + '_set').all()
                else:
                    # No through model use the related objects directly
                    val_list = getattr(obj, field.dj_type.name).all()
                rep_field = getattr(protoMsg, field.name)
                
                # Iterate thorugh and convert each value independantly
                for val in val_list:
                    try:
                        pb_val = self.convert(field.dj_type,
                                          field.pb_type,
                                          val, pb=pb, module=module)
                    except Exception, e:
                        #print field.name, field.dj_type, field.pb_type
                        #traceback.print_exc()
                        raise e
                    if isinstance(field.pb_type, ProtocolBuffer.Message):
                        rep_field.add().CopyFrom(pb_val)
                    else:
                        rep_field.append(pb_val)
            else:
                try:
                    val = getattr(obj, field.dj_type.name)
                except Exception, e:
                    #print message.name, type(obj), field.name, type(field.dj_type.name), field.dj_type.name, field.dj_type, field.pb_type
                    #traceback.print_exc()
                    raise e
                if  val != None and val != "":
                    # TODO: Check if field is repeated and if so get all objects
                    # that need to be converted
                    pb_val = self.convert(field.dj_type,
                                          field.pb_type,
                                          val, pb=pb, module=module)
                    # Use CopyFrom if it field is a composite type
                    if isinstance(field.pb_type, ProtocolBuffer.Message):
                        getattr(protoMsg, field.name).CopyFrom(pb_val)
                    else:
                        # print field.name
                        try:
                            setattr(protoMsg, field.name, pb_val)
                        except Exception, e:
                            #print field.name, field.dj_type, field.pb_type, val, val.pk, val.fk_test,  pb_val
                            #traceback.print_exc()
                            raise e
        return protoMsg