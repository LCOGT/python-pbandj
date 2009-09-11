#!python

#    Copyright (C) 2009  Zachary Walker
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


'''pbandj/pbandj.py - Mapping of Django model classes to Protocol Buffer 
messages and services.
                         
This package contains classes providing a mappings between Django models
and Protocol Buffer messages and RPC services

Authors: Zachary Walker (zwalker@lcogt.net)

July 2009
'''

# Standard library imports
from datetime import date, datetime
from os import system

# Third party imports
from django.conf import settings
if not settings.configured:
    settings.configure() #Must be called to avoid runtime error
from django.db import  models
from protobuf.server import SocketRpcServer

# Module imports


#TODO: Add constants for pb types
PB_TYPE_STRING = "string"
PB_TYPE_DOUBLE = "double"
PB_TYPE_INT32  = "int32"
PB_TYPE_FLOAT  = "float"
PB_TYPE_FLOAT   = "bool"

#TODO: Change keys in dict to be types in stead of strings
DJANGO2PB_TYPE_MAP = {models.CharField.__name__: PB_TYPE_STRING,
                     models.DecimalField.__name__: PB_TYPE_DOUBLE,
                     models.IntegerField.__name__: PB_TYPE_INT32,
                     models.FloatField.__name__: PB_TYPE_FLOAT,
                     models.DateTimeField.__name__: PB_TYPE_STRING,
                     models.DateField.__name__: PB_TYPE_STRING,
                     models.BooleanField.__name__: PB_TYPE_FLOAT,
                     models.NullBooleanField.__name__: PB_TYPE_FLOAT,
                     models.AutoField.__name__: PB_TYPE_INT32,
                     models.ForeignKey.__name__: PB_TYPE_INT32}


#TODO: Change django type portion of key to type rather than string
conv_helpers = {}
#Django seems to require float values input as a string
conv_helpers[(PB_TYPE_DOUBLE,
               models.DecimalField.__name__)] = lambda val : str(val)
#Convert Decimal back to a python float which is the same as a double
#in protocol buffers apparently
conv_helpers[(models.DecimalField.__name__),
             "double"] = lambda val : val.__float__()
#Help convert a Django DateTimeField into a consistent string format
#for transport
conv_helpers[(models.DateTimeField.__name__,
              PB_TYPE_STRING)] = lambda val : val.strftime("%Y-%m-%d %H:%M:%S")
#Help convert a Django DateField into a consistent string format for transport
conv_helpers[(models.DateField.__name__,
              PB_TYPE_STRING)] = lambda val : val.strftime("%Y-%m-%d")
#Help convert a string into a Django DateTimeField
conv_helpers[(PB_TYPE_STRING,
              models.DateTimeField.__name__)] = \
                  lambda val : datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
#Help convert a string into a  Django DateField
conv_helpers[(PB_TYPE_STRING,
              models.DateField.__name__)] = \
                  lambda val : datetime.strptime(val, "%Y-%m-%d")



class ProtocolBuffer(object):
    """ A class containing data describing a Protocol
        Buffer .proto file and it's mapping to Django
        objects
    """ 
    
    
    
    class Field(object):
        """ A class containing data describing a
            protocol buffer message field and any
            mapping to a related Django field
        """
        
        OPTIONAL = "optional"
        REQUIRED = "required"
        REPEATED = "repeated"
        
        # Just trying to get rid of multiple definitions of the same string
        STRING = TYPE_STRING
        DOUBLE = TYPE_DOUBLE
        INT32  = TYPE_INT32
        FLOAT  = TYPE_FLOAT
        BOOL   = TYPE_BOOL
        
        def __init__(self, usage, name, pb_type, dj_type=None):
            """
                Accepted Arguments:
                usage -- (String) Used of this field in the .proto file
                         OPTIONAL = "optional"
                         REQUIRED = "required"
                         REPEATED = "repeated"
                name-- (String) Name of this field
                pb_type -- (String) The Protocol Buffer type for this
                           message field
                dj_type -- (String) The Django type that this field is
                           mapped to.  None if this field isn't mapped
                           to Django
            """
            self.name    = name
            self.usage   = usage
            self.dj_type = dj_type
            self.pb_type = pb_type
             
             
             
    class Message(object):
        """ A class containing data describing a protocol buffer
            message and mapping to a Django model type if
            supplied. If a Django model type has been associated
            with a Message then all fields of the message with
            Django types can be translated between protocol
            buffer and django objects
        """
        
        def __init__(self, msg_name, django_model_class=None):
            """
                Accepted Arguments:
                msg_name -- (String) Name of this protocol
                            buffer message
                django_model_class -- (Django.db.models.model)
                                      Django class that this message
                                      will be mapped to.
                                      If None it will not be mapped 
            """
            self.name               = msg_name
            self.fields             = []
            self.django_model_class = django_model_class
            self.mapped_fields      = []
            self.message_fields     = []
            
            
        def addField(self, field):
            """ Add a field to this Protocol Buffer message   
                Accepted Arguments:
                field -- (ProtocolBuffer.Field) A field to be added to
                         the message
            """
            #Check if this field is mapped to a django type
            if field.dj_type == None:
                #Has the field already been mapped to a message
                if type(field.pb_type) == ProtocolBuffer.Message:
                    self.message_fields.append(field)
                else:
                    self.fields.append(field)
            else:
                self.mapped_fields.append(field)
            
            
        def __str__(self):
            """ Produces a .proto file message declaration
            """
            fields = self.fields + self.mapped_fields + self.message_fields
            field_base = 1
            message =   "message " + self.name + " {\n"
            for i in range(len(fields)):
                field = fields[i]
                message = message + "    %s %s %s = %d;\n"
                message %= (field.usage,
                            field.pb_type.name
                            if type(field.pb_type) == ProtocolBuffer.Message
                            else field.pb_type,
                            field.name, i + field_base)
            message = message + "}\n"
            return message
        
        
        
    class Service(object):
        """ A class containing data describing a protocol buffer
            service
        """
        
        def __init__(self, name, port=8091):
            """
                Accepted Arguments:
                name -- (String) The name of the protocol buffer
                        service
                port -- (Integer) The port number on which this
                        service will be run
            """
            self.name    = name
            self.methods = []
            self.port    = port
        
        
        def addRPCMethod(self, method):
            """ Add an RPC method to this service
                Accepted Arguments:
                method -- (ProtocolBuffer.RPCMethod) An RPCMethod to
                          be added to the service
            """
            self.methods.append(method)
    
    
    
    class RPCMethod(object):
        """ A class encapsulation the description of a Protocol Buffer
            RPC declaration 
        """
        
        def __init__(self, name, in_msg_type, out_msg_type, callable):
            """
                Accepted Arguments:
                name -- (String) The name of the RPC method
                in_msg_type -- (ProtocolBuffer.Message) The type of
                               message passed as an arg to this RPC
                               method
                out_msg_type -- (ProtocolBuffer.Message) The type of
                                message to be returned from the RPC
                                method
                callable -- (function) A function to be called to
                            handle the RPC call, signature 
                            (service_impl, controller, request, done)
            """
            self.name         = name
            self.in_msg_type  = in_msg_type
            self.out_msg_type = out_msg_type
            self.handler      = callable
        
    
    def __init__(self, module_name='generated'):
        """
            AcceptedArguments:
            module_name -- (String) The name of the python module that
                           will be generated for this Protocol Buffer
        """
        self.module_name = module_name
        self.messages    = {}
        self.services    = {}
        
        
    def addMessage(self, message):
        """ Add a message to this Protocol Buffer definition
        
            Accepted Arguments:
            message        -- (ProtocolBuffer.Message) The message to
                              be added to the Protcol Buffer
        """
        self.messages[message.name] = message
    
    
    def __str__(self):
        """ Produce a .proto file string for this Protocol Buffer
            instance
        """
        out= ""
        for key in self.services.keys():
            service = self.services[key]
            out += "service " + service.name + " {\n"
            for method in service.methods:
                out += "    rpc " + method.name + " (" + \
                       method.in_msg_type.name + ") returns (" + \
                       method.out_msg_type.name + ");\n"
            out += "}\n" 
            
        for key in self.messages.keys():
            out += self.messages[key].__str__()
            
        return out
            
            
    def genMsg(self, msg_name, django_model_class, include=[], exclude=[]):
        """ Create a protocol buffer message from a django type.
            By default all args will be included in the new message
            Accepted Args:
            msg_name -- (String) The name of the message
            django_model_class -- (Type) A reference to the django
                                  model type
            included -- (List) A list of field names from the model to
                      be included in the mapping
            exclude -- (List) A list of filed name to exclude from the
                      model.  Only used if included arg is []
        """
        Field = ProtocolBuffer.Field
        pb_msg = ProtocolBuffer.Message(msg_name, django_model_class)
        
        #Local fields
        django_class_fields = [field for field in 
                               django_model_class._meta.local_fields]
        django_field_by_name = {}
        #Iterate through Django fields and init dict that allows
        #lookup of fields by name.
        [django_field_by_name.__setitem__(field.name, field) for field in
            django_class_fields]
        
        if include != []: 
            #Assert that the fields all exist
            include_set = set(include)
            assert include_set == set(django_field_by_name.keys()) & include_set
            
            for field_name in include:
                field = django_field_by_name[field_name]
                pb_field = Field(Field.OPTIONAL,
                                 field.name,
                                 DJANGO2PB_TYPE_MAP.get(type(field).__name__),
                                 type(field).__name__)
                pb_msg.addField(pb_field)
        else:
            useable_field_names = set(django_field_by_name.keys()) - set(exclude)
            for field_name in list(useable_field_names):
                field = django_field_by_name[field_name]
                pb_field = Field(Field.OPTIONAL,
                                 field.name,
                                 DJANGO2PB_TYPE_MAP.get(type(field).__name__),
                                 type(field).__name__)
                pb_msg.addField(pb_field)
        
        self.messages[pb_msg.name] = pb_msg

        return pb_msg
    
    
    def genRpc(self, service_name, rpc_method_name, in_msg_type,
                     out_msg_type, rpc_handler):
        """ Generate a Protocol Buffer RPC
            Accepted Arguments:
            service_name -- (String) Name of the service that the
                            method will be added to or created if
                            not already in existence
            rpc_method_name -- (String) Name of the rpc method being
                               created within the service
            in_msg_type -- (ProtocolBuffer.Message) 
                           A ProtocolBuffer.Message describing the in
                           msg arg to the rpc call
            out_msg_type -- (ProtocolBuffer.Message)
                            A ProtocolBuffer.Message describing the
                            response msg to the rpc call
            rpc_handler -- (Method) A reference to a callable method
                           with signature (service_impl, controller,
                           request, done) that will be handle the rpc
                           call
        """
        service = self.services.get(service_name)
        if service == None:
            service = ProtocolBuffer.Service(service_name)
            self.services[service_name] = service

        rpc = ProtocolBuffer.RPCMethod(rpc_method_name,
                                       in_msg_type,
                                       out_msg_type,
                                       rpc_handler)
        service.addRPCMethod(rpc)
    
    
    def toDjango(self, obj):
        """ Take a protocol buffer object whose class was generated by
            this objcet and marshall a Django object
            Accepted Args:
            obj -- (google.protobuf.Message) The object to be converted
        """
        message = self.messages[obj.__class__.__name__]
        mapped_fields = dict([(field.name, field) for field in
                              message.mapped_fields])
        composite_msg_fields = dict([(field.name, field) for field in
                                      message.message_fields])
        unmapped_fields = dict([(field.name, field) for field in
                                 message.fields])

        djObj = message.django_model_class()
        for (field, val) in obj.ListFields():
            if field.name in composite_msg_fields:
                #This is a composite field that requires special handling
                pass
            elif field.name in unmapped_fields:
                #ignore this field it isn't mapped
                pass
            else:
                if mapped_fields[field.name].usage == ProtocolBuffer.Field.REPEATED:
                    #repeated fields imply some kind of foreign key relationship
                    #requires special handling
                    pass
                else:
                    #This is an optional or required directly mappable field
                    mapped_field = mapped_fields[field.name]
                    #Get conversion helper, default to dummy pass-through function
                    helper = conv_helpers.get((mapped_field.pb_type, mapped_field.dj_type), lambda x : x)
                    djObj.__setattr__(field.name, helper(val))
        return djObj
    
    
    def toProtoMsg(self, obj, dest_obj=None):
        """ Take a django object for which a protocol buffer message
            has been generated and return a related protocol buffer
            message.  Since the python implementation of protocol
            buffers uses factory methods to create field instances
            of nested messages, use the dest_obj arg to
            do the type conversion for you.
            Ex. pbuf.toProtoMsg(obj=django_obj, dest_obj=my_msg.field.add())
            Accepted Args:
            obj -- (django Model) The object to be converted
            dest_obj -- (Message) An instance of the message class
                        that is related to the django object arg.
                        Instead of creating a new object this obj
                        will be loaded with data and returned
        """
        exec("from " + self.module_name + "_pb2 import " + 
             obj.__class__.__name__)
        if dest_obj is None:
            exec("protoMsg = " + obj.__class__.__name__ + "()")
        else:
            protoMsg = dest_obj
            
        message = self.messages[obj.__class__.__name__]
        for field in message.mapped_fields:
            val = obj.__getattribute__(field.name)
            if  val != None and val != "":
                #Get conversion helper, default to dummy pass-through function
                helper = conv_helpers.get((field.dj_type, field.pb_type, ),
                                           lambda x : x)
                protoMsg.__setattr__(field.name,
                                      helper(obj.__getattribute__(field.name)))
                                      
        return protoMsg
          
           
    def genMod(self, path="."):
        """ Generate a python module for this Protocol Buffer.
            The default name is genereated_pb2.py unless specified.
            Accepted Arguments:
            path -- (String) The path, relative or fully qualified,
                    to the directory where the generated module will
                    be created
        """
        f = open(path + "/" + self.module_name + ".proto", 'w')
        f.write(self.__str__())
        f.close()
        
        print "protoc --python_out=" + path + \
              " --proto_path=" + path + " " + \
              self.module_name + ".proto"
        system("protoc --python_out=" + path +
               " --proto_path=" + path + " " +
               path + "/" + self.module_name + ".proto")
               
        return self.module_name + "_pb2"
    
    
    def startServices(self):
        """ Start all services described in this Protocol Buffer
            description
        """
        command = "import " + self.module_name + "_pb2 as proto"
        exec(command) in globals()
        
        for service in self.services.values():
            print "Starting " + service.name
            service_class = proto.__dict__[service.name]
            handlers = {}
            
            for method in service.methods:
                print "Adding handler " + method.name
                handlers[method.name] = method.handler
                
            server = SocketRpcServer(service.port)
            newservice = type(service.name + "Impl",
                              (service_class,), handlers)
            server.registerService(newservice())
            server.run();
        
    
        
