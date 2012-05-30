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

from __future__ import division

import decimal
from datetime import datetime, time
import traceback

from django.db import models

from modelish import types
from modelish.pb.enum import Enum
from modelish.pb.message import Message
from modelish.pb import field



#def _date_dj2pb(val, kwargs):
#    '''Convert Django DateField to a protocol buffer Date message'''
#    date = proto.Date()
#    date.year = val.year
#    date.month = val.month
#    date.day = val.day
#    return date
#
#def _date_pb2dj(val, kwargs):
#    '''Convert a protocol buffer Date msg to a Django DateField'''
#    return datetime(val.year, val.month, val.day)
#    
#def _datetime_dj2pb(val, kwargs):
#    '''Convert Django DateTimeField to a protocol buffer Date message'''
#    date = proto.Date()
#    date.year = val.year
#    date.month = val.month
#    date.day = val.day
#    date.time.hour = val.hour
#    date.time.minute = val.minute
#    date.time.second = val.second
#    #date.time.micro = val.microsecond
#    return date
#
#def _datetime_pb2dj(val, kwargs):
#    '''Convert protocol buffer Date msg to Django DateTimeField'''
#    return datetime(val.year, val.month, val.day, val.time.hour,
#                    val.time.minute, val.time.second)#, val.time.micro)
#    
#def _time_dj2pb(val, kwargs):
#    '''Convert  Django TimeField to a protocol buffer Time msg'''
#    time = proto.Time()
#    time.hour = val.hour
#    time.minute = val.minute
#    time.second = val.second
#    #time.micro = val.microsecond
#    return time
#
#def _time_pb2dj(val, kwargs):
#    '''Convert protocol buffer Time msg to Django TimeField'''
#    file = models.FileField
#    return time(val.hour, val.minute, val.second)#, val.micro)

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
                      types.PB_TYPE_STRING)] = lambda val, kwargs : val.strftime("%Y-%m-%d %H:%M:%S.%f")# + "." + str(val.microsecond / 1000000)
        
        #Help convert a Django DateField into a consistent string format for transport
        conv_helpers[(models.DateField,
                      types.PB_TYPE_STRING)] = lambda val, kwargs : val.strftime("%Y-%m-%d")
                      
        #Help convert a Django TimeField into a consistent string format for transport
        conv_helpers[(models.TimeField,
                      types.PB_TYPE_STRING)] = lambda val, kwargs : val.strftime("%H:%M:%S.%f")# + "." + str(val.microsecond / 1000000)
        
        #Help convert a string into a Django DateTimeField
        conv_helpers[(types.PB_TYPE_STRING,
                      models.DateTimeField)] = \
                          lambda val, kwargs : datetime.strptime(val, "%Y-%m-%d %H:%M:%S.%f")
        
        #Help convert a string into a  Django DateField
        conv_helpers[(types.PB_TYPE_STRING,
                      models.DateField)] = \
                          lambda val, kwargs : datetime.strptime(val, "%Y-%m-%d")
                          
        #Help convert a string into a Django DateTimeField
        conv_helpers[(types.PB_TYPE_STRING,
                      models.TimeField)] = \
                          lambda val, kwargs : datetime.strptime(val, "%H:%M:%S.%f")
        
        #Help convert a string into a  Django CharField by truncating input that is too long.
        conv_helpers[(types.PB_TYPE_STRING,
                      models.CharField)] = \
                          lambda val, kwargs : val[0:kwargs['output_type'].max_length]

        conv_helpers[(models.FileField,
                      types.PB_TYPE_STRING)] = \
                          lambda val, kwargs : val.name
                          
        conv_helpers[(models.ImageField,
                      types.PB_TYPE_STRING)] = \
                          lambda val, kwargs : val.name
                          
        conv_helpers[(Enum, models.CharField)] = \
                          lambda val, kwargs: dict([(b,a) for a,b in kwargs['input_type'].dj2val.items()])[val]
        
        conv_helpers[(models.CharField, Enum)] = \
                          lambda val, kwargs: kwargs['output_type'].dj2val[val]
                          
        conv_helpers[(models.ForeignKey, types.PB_TYPE_INT32)] = \
                          lambda val, kwargs: val.pk
                          
        conv_helpers[(types.PB_TYPE_INT32, models.ForeignKey)] = \
                          lambda val, kwargs: kwargs['output_type'].related.parent_model.objects.get(pk=val).pk
                          
        conv_helpers[(models.ForeignKey, Message)] = \
                          lambda val, kwargs: self.toProtoMsg(kwargs['pb'], val, kwargs['module'])
                          #self.convert(kwargs['input_type'], kwargs['output_type'], val)
        
        conv_helpers[(Message, models.ForeignKey)] = \
                          lambda val, kwargs: self.toDjangoObj(kwargs['pb'], val)
                          #lambda val, kwargs: self.convert(kwargs['input_type'], kwargs['output_type'], val)
        
        conv_helpers[(models.ManyToManyField, types.PB_TYPE_INT32)] = \
                          lambda val, kwargs : val.pk
        
        conv_helpers[(types.PB_TYPE_INT32, models.ManyToManyField)] = \
                          lambda val, kwargs : _m2m_pb2dj(val, kwargs)
        
        conv_helpers[(models.ManyToManyField, Message)] = \
                          lambda val, kwargs : self.toProtoMsg(kwargs['pb'], val, kwargs['module'])
        
        conv_helpers[(Message, models.ManyToManyField)] = \
                          lambda val, kwargs : val
        
        #Help convert string to Django comma separated integer
        #conv_helpers[(types.PB_TYPE_STRING,
        #              models.CommaSeparatedIntegerField)] = \
        #                  lambda val, kwargs : eval(val)
        #conv_helpers[(models.CommaSeparatedIntegerField,
        #              types.PB_TYPE_STRING)] = \
        #                  lambda val, kwargs : str(val)
        
#        conv_helpers[(models.DateTimeField, Message)] = _datetime_dj2pb
#        conv_helpers[(models.DateField, Message)] = _date_dj2pb
#        conv_helpers[(models.TimeField, Message)] = _time_dj2pb
#
#        conv_helpers[(Message, models.DateField)] = _date_pb2dj
#        conv_helpers[(Message, models.DateTimeField)] = _datetime_pb2dj
#        conv_helpers[(Message, models.TimeField)] = _time_pb2dj

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
        helper = self.helpers.get((input_type, output_type), lambda x, kwargs : x)
        kwargs['input_type'] = input_type
        kwargs['output_type'] = output_type
        return helper(val, kwargs)

    def toDjangoObj(self, mapped_module, obj, dest_obj=None):
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
            
            mapped_model = None
            for mapped_model_test in mapped_module.mapped_models:
                if mapped_model_test.pbandj_pb_msg.name == pb_msg_name:
                    mapped_model = mapped_model_test
                    break

            if mapped_model == None:
                raise Exception("No pbandj mapping found for protocol buffer message type %s" % pb_msg_name)
            
            if(not dest_obj is None):
                if isinstance(dest_obj, mapped_model.dj_model):
                    # TODO: Add unittest for this case
                    dj_obj = dest_obj
                else:
                    # TODO: Add unittest for this case 
                    raise Exception("dest_obj type %s doesn't match model type %s" % 
                                    (type(dest_obj), mapped_model.dj_model))
            else:
                dj_obj = mapped_model.dj_model()
            
            # Iterate through msg fields and convert to django types
            for (pb_field, val) in obj.ListFields():
                pbandj_dj_field, pbandj_pb_field = mapped_model.pb_to_dj_field_map[pb_field.name]
                if pbandj_pb_field.usage == field.REPEATED:
                    # repeated fields imply some kind of foreign key relationship
                    # requires special handling
                    # Django doesn't make it easy to add relation fields to an
                    # object without first saving it.
                    pass
                else:
                    # This is an optional or required directly mappable field
#                    mapped_field = mapped_fields[pb_field.name]
                    dj_val = self.convert(pbandj_pb_field,
                                          pbandj_dj_field,
                                          val, pb=mapped_module)
                    # For a foreign key, we set 'field_id' to the pk of the related value 
                    setattr(dj_obj, pbandj_dj_field.name, dj_val)
            return dj_obj
    
    
    def toProtoMsg(self, mapped_module, obj, dest_obj=None):
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
            dest_obj -- (Message) An instance of the message class
                        that is related to the django object arg.
                        Instead of creating a new object this obj
                        will be loaded with data and returned
        """
        # Import the message type and instantiate if necessary
        dj_type = type(obj)
        # Try to get the type using the django class name
        mapped_model = None
        for mapped_model_test in mapped_module.mapped_models:
            if mapped_model_test.dj_model == dj_type:
                mapped_model = mapped_model_test
                break
            
        if mapped_model == None:
            raise Exception("No mapping available for django type %s." % dj_type)
        
        msg_type = getattr(mapped_module.load_pb2(), mapped_model.pbandj_pb_msg.name)
#        pbandj_model = mapped_model.pbandj_model
        
        if dest_obj is None:
            protoMsg = msg_type()
        else:
            protoMsg = dest_obj
        
        # Get the pb message type and convert the django message 
#        for mapped_field in mapped_model.pbandj_pb_msg.fields['mapped_fields']['fields']:
        for dj_field, pb_field in mapped_model.pb_to_dj_field_map.values():
#            dj_field, pb_field = mapped_model.pb_to_dj_field_map[field.name]
                    
            if pb_field.usage == field.REPEATED:
                # Must be a ManyToMany type relation
                val_list = []
                    
                if isinstance(dj_field, field.ManyToMany):
                    val_list = dj_field.dj_type.all()
                    
                rep_field = getattr(protoMsg, pb_field.name)
                
                # Iterate thorugh and convert each value independantly
                for val in val_list:
                    try:
                        pb_val = self.convert(dj_field.dj_type,
                                          pb_field.pb_type,
                                          val, pb=mapped_model, module=mapped_module.load_pb2())
                    except Exception, e:
                        #print field.name, field.dj_type, field.pb_type
                        traceback.print_exc()
                        raise e
                    if isinstance(pb_field, Message):
                        rep_field.add().CopyFrom(pb_val)
                    else:
                        rep_field.append(pb_val)
            else:
                try:
                    val = getattr(obj, dj_field.name)
                except Exception, e:
                    #print message.name, type(obj), field.name, type(field.dj_type.name), field.dj_type.name, field.dj_type, field.pb_type
                    #traceback.print_exc()
                    raise e
                if  val != None and val != "":
                    # TODO: Check if field is repeated and if so get all objects
                    # that need to be converted
                    pb_val = self.convert(dj_field.dj_type,
                                          pb_field.pb_type,
                                          val, pb=mapped_model, module=mapped_module.load_pb2())
                    
                    # Use CopyFrom in case field is a composite type
                    if isinstance(pb_field, Message):
                        getattr(protoMsg, pb_field.name).CopyFrom(pb_val)
                    else:
                        # print field.name
                        try:
                            setattr(protoMsg, pb_field.name, pb_val)
                        except Exception, e:
                            print dj_field.name, type(dj_field), dj_field.dj_type, type(pb_field), pb_field.pb_type, type(val), val #val.pk, val.fk_test,  pb_val
                            traceback.print_exc()
                            raise e
        return protoMsg