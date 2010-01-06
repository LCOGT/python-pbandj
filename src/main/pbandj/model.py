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
'''model.py - A class structure mapping the meta data needed to construct
a protocol buffer .proto file
                         
Authors: Zachary Walker (zwalker@lcogt.net)
July 2009
'''

# Standard library imports
import threading
from datetime import date, datetime
from socket import gethostname

# Third party imports
from protobuf.server import SocketRpcServer

# Module imports


class ProtocolBuffer(object):
    """ A class containing data describing a Protocol
        Buffer .proto file and it's mapping to Django
        objects
    """ 
    
    
    
    class Enumeration(object):
        
        def __init__(self, name, values=None):
            '''Create an Enumeration object with given name and list of values
            to be enumerated
            '''
            self.name = name.lower().capitalize()
            # Holds Protobuf enum val name to int mapping
            name2val = {}
            # Holds Django val to int mapping
            dj2val = {}
            #self.values = {}
            if values != None:
                # Map django choices to int values
                dj2val = [(str(values[i]), i) for i in range(len(values))]
                dj2val += [(val, key) for key,val in dj2val]
                # Create a enum to val mapping
                name2val = [[name.upper() + '_' + str(values[i]), i] for i in range(len(values))]
                # Format the enum constant names
                for pair in name2val:
                    name = pair[0]
                    if name[0].isdigit():
                        name = '_' + name
                    name = name.replace('.', '_')
                    name = name.replace('-', '_')
                    name = name.upper()
                    pair[0] = name
                self.name2val = dict(name2val)
                self.dj2val = dict(dj2val)
        
        def __str__(self):
            proto = 'enum %s {\n' % self.name
            for key in self.name2val:
                if(type(key) == str):
                    proto += '%s = %d;\n' % (key, self.name2val[key])
            proto += '}\n\n'
            return proto
             
            
    
    class Field(object):
        """ A class containing data describing a
            protocol buffer message field and any
            mapping to a related Django field
        """
        
        OPTIONAL = "optional"
        REQUIRED = "required"
        REPEATED = "repeated"
        
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
            self.enums              = []
            
        def addField(self, field):
            """ Add a field to this Protocol Buffer message   
                Accepted Arguments:
                field -- (ProtocolBuffer.Field) A field to be added to
                         the message
            """
            # Check if this field is mapped to a django type
            if field.dj_type is None:
                # Has the field already been mapped to a message
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
            for enum in self.enums:
                message += str(enum)
            for i in range(len(fields)):
                field = fields[i]
                if type(field.pb_type) == ProtocolBuffer.Message:
                    field_type = field.pb_type.name
                elif type(field.pb_type) == ProtocolBuffer.Enumeration:
                    field_type = field.pb_type.name
                else:
                    field_type = field.pb_type.ptype
                message = message + "    %s %s %s = %d;\n"
                message %= (field.usage,
                            field_type,
                            field.name, i + field_base)
            message = message + "}\n"
            return message
        
        
        
    class Service(object):
        """ A class containing data describing a protocol buffer
            service
        """
        
        class ServiceThread(threading.Thread):
            
            def __init__(self, module, service, port):
                threading.Thread.__init__(self)
                self.module = module
                self.service = service
                self.port = port
                
#            def _createHandler(self, func):
#                def handler(service_impl, controller, request, done):
#                    try:
#                        result = func(request)
#                    except Exception, e:
#                        controller.handleError(e, e.__str__())
#                    done.run(result)
                
            def run(self):
                """ Start service thread """
                # Create a server instance
                server = SocketRpcServer(self.port,host='')
                service_class = self.module.__dict__[self.service.name]
                handlers = {}
                
                # Link each method to its handler
                for method in self.service.methods:
                    #handlers[method.name] = self._createHandler(method.handler)
                    handlers[method.name] = method.handler
                
                # Extend Service class and add handlers    
                newservice = type(self.service.name + "Impl",
                                  (service_class,), handlers)
                server.registerService(newservice())
                
                # Start the server
                server.run();
        
        
        def __init__(self, name):
            """
                Accepted Arguments:
                name -- (String) The name of the protocol buffer
                        service
                port -- (Integer) The port number on which this
                        service will be run
            """
            self.name    = name
            self.methods = []
        
        
        def addRPCMethod(self, rpc_method_name, in_msg_type,
                     out_msg_type, rpc_handler):
            """ Generate a Protocol Buffer RPC
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
            rpc = ProtocolBuffer.RPCMethod(rpc_method_name,
                                       in_msg_type,
                                       out_msg_type,
                                       rpc_handler)
            self.methods.append(rpc)
            
        def start(self, module, port, daemon=False):
            """ Start service in a new thread """
            thread = ProtocolBuffer.Service.ServiceThread(module, self, port)
            thread.setDaemon(daemon)
            thread.start()
            
    
    
    
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
        self.imports     = []
        self.messages    = {}
        self.services    = {}
        self.enum        = {}
        
    
    def python_mod_name(self):
        return self.module_name + "_pb2"
    
    def proto_filename(self):
        return self.module_name + ".proto"
          
    def addMessage(self, message):
        """ Add a message to this Protocol Buffer definition.  Also adds any
        messages that are used as fields of this message.  Message fields added
        after the message is added to the protocol buffer must be added to the
        protocol buffer directly using addMessage.  An Exception will be raised
        if a field of the root message is a message of the same name but different
        type of a message already included in the protocol buffer.  A name 
        collision on the root message will be ignored and the existing messasge
        will be overwritten.
            Accepted Arguments:
            message        -- (ProtocolBuffer.Message) The message to
                              be added to the Protcol Buffer
        """
        # Add mapping by message name
        self.messages[message.name] = message
        # Add mapping by django model class
        self.messages[message.django_model_class] = message
        # Add message mapping for fields of type message 
        for field in message.mapped_fields:
            if (isinstance(field.pb_type, ProtocolBuffer.Message) and
                not field.pb_type.django_model_class is None):
                if (self.messages.has_key(field.pb_type.name) and
                    self.messages[field.pb_type.name] != field.pb_type):
                    raise Exception("There is already a message named %s" %
                                    field.pb_type.name)
                if (self.messages.has_key(field.pb_type.django_model_class) and
                    self.messages[field.pb_type.django_model_class] != field.pb_type):
                    raise Exception("There is already a message mapped to django type %s" %
                                    field.pb_type.django_model_class.__name__)
                self.addMessage(field.pb_type)
    
    
    def addRpc(self, service_name, method_name, in_msg, out_msg, handler):
        ''' Create a new service with service_name that will be available
            on the specified port.  If the service already exists, the 
            existing service will be returned otherwise a new service
            will be returned.  Exception will be thrown a service by the
            same name is on a different port or if a service with a 
            different name is already using the requested port
        '''
        service = self.services.get(service_name)
        if service:
            service.addRPCMethod(method_name, in_msg, out_msg, handler)
        else:
            service = ProtocolBuffer.Service(service_name)
            service.addRPCMethod(method_name, in_msg, out_msg, handler)
            self.services[service_name] = service
    
    
    def __str__(self):
        """ Produce a .proto file string for this Protocol Buffer
            instance
        """
        out= ""
        for proto in self.imports:
            if type(proto) is ProtocolBuffer:
                out += 'import "%s";\n' % proto.proto_filename()
            else:
                out += 'import "%s";\n' % proto
        for key in self.services.keys():
            service = self.services[key]
            out += "service " + service.name + " {\n"
            for method in service.methods:
                out += "    rpc " + method.name + " (" + \
                       method.in_msg_type.name + ") returns (" + \
                       method.out_msg_type.name + ");\n"
            out += "}\n" 
            
        for key in self.messages.keys():
            if isinstance(key,str):
                out += self.messages[key].__str__()
            
        return out
        
    
        
