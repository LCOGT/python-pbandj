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

from modelish.dj.field import ForeignKey, ManyToMany


class Converter(object):
    
    def __init__(self, mapped_module):
        self.mapped_module = mapped_module
        
        #TODO: Change django type portion of key to type rather than string
        conv_helpers = {}
        
        #Django seems to require float values input as a string
        conv_helpers[(types.PB_TYPE_DOUBLE,
                       models.DecimalField)] = lambda input_type, output_type, val : decimal.Decimal(val)
        
        #Convert Decimal back to a python float which is the same as a double
        #in protocol buffers apparently
        conv_helpers[(models.DecimalField,
                     types.PB_TYPE_DOUBLE)] = lambda input_type, output_type, val : float(decimal.Decimal(val))
        
        #Help convert a Django DateTimeField into a consistent string format
        #for transport
        conv_helpers[(models.DateTimeField,
                      types.PB_TYPE_STRING)] = lambda input_type, output_type, val : val.strftime("%Y-%m-%d %H:%M:%S.%f")# + "." + str(val.microsecond / 1000000)
        
        #Help convert a Django DateField into a consistent string format for transport
        conv_helpers[(models.DateField,
                      types.PB_TYPE_STRING)] = lambda input_type, output_type, val : val.strftime("%Y-%m-%d")
                      
        #Help convert a Django TimeField into a consistent string format for transport
        conv_helpers[(models.TimeField,
                      types.PB_TYPE_STRING)] = lambda input_type, output_type, val : val.strftime("%H:%M:%S.%f")# + "." + str(val.microsecond / 1000000)
        
        #Help convert a string into a Django DateTimeField
        conv_helpers[(types.PB_TYPE_STRING,
                      models.DateTimeField)] = \
                          lambda input_type, output_type, val : datetime.strptime(val, "%Y-%m-%d %H:%M:%S.%f")
        
        #Help convert a string into a  Django DateField
        conv_helpers[(types.PB_TYPE_STRING,
                      models.DateField)] = \
                          lambda input_type, output_type, val : datetime.strptime(val, "%Y-%m-%d").date()
                          
        #Help convert a string into a Django DateTimeField
        conv_helpers[(types.PB_TYPE_STRING,
                      models.TimeField)] = \
                          lambda input_type, output_type, val : datetime.strptime(val, "%H:%M:%S.%f").time()
        
        #Help convert a string into a  Django CharField by truncating input that is too long.
        conv_helpers[(types.PB_TYPE_STRING,
                      models.CharField)] = \
                          lambda input_type, output_type, val : val[0:(output_type.max_length if hasattr(output_type, 'max_length') else len(val))]

        conv_helpers[(models.FileField,
                      types.PB_TYPE_STRING)] = \
                          lambda input_type, output_type, val : val.name
                          
        conv_helpers[(models.ImageField,
                      types.PB_TYPE_STRING)] = \
                          lambda input_type, output_type, val : val.name
                          
        conv_helpers[(Enum, models.CharField)] = \
                          lambda input_type, output_type, val: input_type[val]
        
        conv_helpers[(models.CharField, Enum)] = \
                          lambda input_type, output_type, val: output_type[val]

        self.helpers = conv_helpers
        
        self.conversion_methods = {}
        
        
        for mapped_model in self.mapped_module.mapped_models:
            for pbandj_dj_field, pbandj_pb_field in mapped_model.pb_to_dj_field_map.values():
                # Add converter to ManyToMany fields mapped to messages
                if isinstance(pbandj_dj_field, ManyToMany) and isinstance(pbandj_pb_field.pb_type, Message):
                    self.helpers[(pbandj_dj_field, pbandj_pb_field)] = self.django_many_to_many_field_to_protocol_buffer_message
                    self.helpers[(pbandj_pb_field, pbandj_dj_field)] = self.protocol_buffer_message_to_django_many_to_many_field
                # Add converter to ManyToMany fields mapped to fields
                elif isinstance(pbandj_dj_field, ManyToMany) and isinstance(pbandj_pb_field, field.Field):
                    self.helpers[(pbandj_dj_field, pbandj_pb_field)] = self.django_many_to_many_field_to_protocol_buffer_int32
                    self.helpers[(pbandj_pb_field, pbandj_dj_field)] = self.protocol_buffer_int32_to_django_many_to_many_field
                # Add converter to ForeignKey fields mapped to messages
                elif isinstance(pbandj_dj_field, ForeignKey) and isinstance(pbandj_pb_field.pb_type, Message):
                    self.helpers[(pbandj_dj_field, pbandj_pb_field)] = self.django_foreign_key_field_to_protocol_buffer_message
                    self.helpers[(pbandj_pb_field, pbandj_dj_field)] = self.protocol_buffer_message_to_django_foreign_key_field
                # Add converter to ForeignKey fields mapped to fields    
                elif isinstance(pbandj_dj_field, ForeignKey) and isinstance(pbandj_pb_field, field.Field):
                    self.helpers[(pbandj_dj_field, pbandj_pb_field)] = self.django_foreign_key_field_to_protocol_buffer_int32
                    self.helpers[(pbandj_pb_field, pbandj_dj_field)] = self.protocol_buffer_int32_to_django_foreign_key_field
                else:
                    self.helpers[(pbandj_dj_field, pbandj_pb_field)] = self.generic_django_field_to_generic_protocol_buffer_field
                    self.helpers[(pbandj_pb_field, pbandj_dj_field)] = self.generic_protocol_buffer_field_to_generic_django_field
            
            # Add converter for each enumerated type
            enums = mapped_model.pbandj_pb_msg.enums
            for enum in enums:
                # Django -> Protocol Buffer
                self.helpers[(models.CharField, enum)] = lambda input_type, output_type, val : output_type[str(val)]
                # Protocol Buffer -> Django
                self.helpers[(enum, models.CharField)] =  lambda input_type, output_type, val : input_type[val]
                
    
    def generic_django_field_to_generic_protocol_buffer_field(self, infield, outfield, val):
        helper = self.helpers.get((infield.dj_type, outfield.pb_type), lambda val, input_type, output_type : val)
        result = helper(input_type=infield.dj_type, output_type=outfield.pb_type, val=val)
        return result
    
    def generic_protocol_buffer_field_to_generic_django_field(self, infield, outfield, val):
        helper = self.helpers.get((infield.pb_type, outfield.dj_type), lambda val, input_type, output_type : val)
        result = helper(input_type=infield.pb_type, output_type=outfield.dj_type, val=val)
        return result
    
    def django_many_to_many_field_to_protocol_buffer_message(self, infield, outfield, val):
        return self.djtopb(val)
    
    def protocol_buffer_message_to_django_many_to_many_field(self, infield, outfield, val):
        return self.pbtodj(val)
    
    def django_many_to_many_field_to_protocol_buffer_int32(self, infield, outfield, val):
        return val.pk
    
    def protocol_buffer_int32_to_django_many_to_many_field(self, infield, outfield, val):
        return outfield.related_model.objects.get(pk=val)
    
    def django_foreign_key_field_to_protocol_buffer_message(self, infield, outfield, val):
        return self.djtopb(val)
    
    def protocol_buffer_message_to_django_foreign_key_field(self, infield, outfield, val):
        return self.pbtodj(val)
    
    def django_foreign_key_field_to_protocol_buffer_int32(self, infield, outfield, val):
        return val.pk
    
    def protocol_buffer_int32_to_django_foreign_key_field(self, infield, outfield, val):
        return outfield.related_model.objects.get(pk=val)
    
    def django_char_field_to_protocol_buffer_enum(self, infield, outfield, val):
        return outfield[str(val)]


    def add_conv_helper(self, input_type, output_type, helper):
        '''Add a conversion helper to go from the supplied input type to
           output type by calling the helper function.  Helper should
           take have the format helper(val, kwargs).  Args passed to the
           helper by keyword will be input_type and output_type
        '''
        self.helpers[(input_type, output_type)] = helper
        
    def convert_field(self, infield, outfield, val, **kwargs):
        '''Convert the input object to the output type and return an object of
           output type.  If there is not an existing mapping and conversion 
           helper between the type(input_obj) and output_type the input_obj
           will be returned unchanged
        '''
#        print infield, outfield, val
        helper = self.helpers.get((infield, outfield))
        result = helper(infield, outfield, val)
#        print "returning", type(result), result 
        return result


    def pbtodj(self, obj, dest_obj=None):
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
            for mapped_model_test in self.mapped_module.mapped_models:
                if mapped_model_test.pbandj_pb_msg.name == pb_msg_name:
                    mapped_model = mapped_model_test
                    break

            if mapped_model == None:
                #print [model.pbandj_pb_msg.name for model in self.mapped_module.mapped_models]
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
            
            # Retrieve the set of mapped fields from the mapped model
            mapped_fields = mapped_model.mapped_fields()
            # Iterate through msg fields and convert to django types
#            for field.name, (pb_field, db_field) in 
            for (pb_field, val) in obj.ListFields():
                if not mapped_fields.has_key(pb_field.name):
                    continue
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
#                    dj_val = self.convert(pbandj_pb_field.pb_type,
#                                          pbandj_dj_field.dj_type,
#                                          val, pb=self.mapped_module)
                    dj_val = self.convert_field(pbandj_pb_field,
                                          pbandj_dj_field,
                                          val)                    
                    # For a foreign key, we set 'field_id' to the pk of the related value 
                    setattr(dj_obj, pbandj_dj_field.name, dj_val)
            return dj_obj
    
    
    def djtopb(self, obj, dest_obj=None):
        """ Take a django object for which a protocol buffer message
            has been generated and return a related protocol buffer
            message.  Since the python implementation of protocol
            buffers uses factory methods to create field instances
            of nested messages, use the dest_obj arg to
            do the type conversion for you.
            Ex. pbuf.djtopb(obj=django_obj, dest_obj=my_msg.field.add())
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
        for mapped_model_test in self.mapped_module.mapped_models:
            if mapped_model_test.dj_model == dj_type:
                mapped_model = mapped_model_test
                break
            
        if mapped_model == None:
            raise Exception("No mapping available for django type %s." % dj_type)
        
        msg_type = getattr(self.mapped_module.load_pb2(), mapped_model.pbandj_pb_msg.name)
#        pbandj_model = mapped_model.pbandj_model
        
        if dest_obj is None:
            protomsg = msg_type()
        else:
            protomsg = dest_obj
        
        # Get the pb message type and convert the django message 
#        for mapped_field in mapped_model.pbandj_pb_msg.fields['mapped_fields']['fields']:
        for dj_field, pb_field in mapped_model.pb_to_dj_field_map.values():
#            dj_field, pb_field = mapped_model.pb_to_dj_field_map[field.name]                  
            if pb_field.usage == field.REPEATED:
                # Must be a ManyToMany type relation
                val_list = []
                    
                if isinstance(dj_field, ManyToMany):
#                    val_list = dj_field.dj_type.all()
                    val_list = getattr(obj, dj_field.name).all()
                    
                rep_field = getattr(protomsg, pb_field.name)
                
                # Iterate thorugh and convert each value independantly
                for val in val_list:
                    try:
#                        print dj_field.dj_type, isinstance(pb_field.pb_type, Enum)
#                        print type(val), dj_field, pb_field
                        pb_val = self.convert_field(dj_field,
                                          pb_field,
                                          val)
#                        print type(pb_val)
                    except Exception, e:
                        #print field.name, field.dj_type, field.pb_type
                        traceback.print_exc()
                        raise e
                    if isinstance(pb_field.pb_type, Message):
#                        print "types"
#                        print type(pb_val)
#                        print type(rep_field)
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
#                    pb_val = self.convert(dj_field.dj_type,
#                                          pb_field.pb_type,
#                                          val, pb=mapped_model, module=self.mapped_module.load_pb2())
                    pb_val = self.convert_field(dj_field,
                                          pb_field,
                                          val)
                    # Use CopyFrom in case field is a composite type
                    if isinstance(pb_field.pb_type, Message):
                        #getattr(protomsg, pb_field.name).CopyFrom(pb_val)
                        attr = getattr(protomsg, pb_field.name)
                        attr.CopyFrom(pb_val)
                    else:
                        # print field.name
                        try:
                            setattr(protomsg, pb_field.name, pb_val)
                        except Exception, e:
                            #print dj_field.name, type(dj_field), dj_field.dj_type, type(pb_field), pb_field.pb_type, type(val), val #val.pk, val.fk_test,  pb_val
                            traceback.print_exc()
                            raise e
        return protomsg