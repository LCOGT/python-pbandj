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
        
        def __init__(self, name, values=None, doc=None):
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
                self.doc = doc
        
        def __eq__(self, other):
            if not isinstance(other, self.__class__):
                return False
#            print "Enum compare", (self.name == other.name ,
#                     self.name2val == other.name2val , 
#                     self.dj2val == other.dj2val)
            return (self.name == other.name and
                     self.name2val == other.name2val and 
                     self.dj2val == other.dj2val)
            
        def __ne__(self, other):
            return not self.__eq__(other)
        
        # Hacked hash.  Enums aren't imutable as implemented.
        # Be careful using hash
        def __hash__(self):
            return hash(self.name) ^ hash(tuple(self.name2val.items())) ^ hash(tuple(self.dj2val.items()))
        
        def __str__(self):
            if self.doc is None:
                proto = ''
            else:
                proto = "// %s\n" % str(self.doc).strip()
            proto += 'enum %s {\n' % self.name
            for key in self.name2val:
                if(type(key) == str):
                    proto += '\t%s = %d;\n' % (key, self.name2val[key])
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
            
        def __eq__(self, other):
            if not isinstance(other, self.__class__):
                return False
            return (self.name == other.name ,
                    self.usage == other.usage and
                    self.dj_type == other.dj_type and
                    self.pb_type == other.pb_type)
        
        def __ne_(self, other):
            return not self.__eq__(other)
        
        # Hacked hash.  Fields aren't immutable as implemented.
        # Be careful using hash
        def __hash__(self):
            return hash(self.name) ^ hash(self.usage) ^ hash(self.dj_type) ^ hash(self.pb_type)
             
       
             
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
            self.__iadd__           = None
        
        def __eq__(self, other):
            if not isinstance(other, self.__class__):
                return False
            if self.name != other.name: return False
            if len(self.fields) != len(other.fields): return False
            if len(self.mapped_fields) != len(other.mapped_fields): return False
            if len(self.message_fields) != len(other.message_fields): return False
            if len(self.enums) != len(other.enums): return False
            for field in self.fields:
                if other.fields.count(field) != self.fields.count(field):
                    return False #break
            if self.django_model_class != other.django_model_class: return False
            for field in self.mapped_fields:
                if other.mapped_fields.count(field) != self.mapped_fields.count(field):
                    return False
            for field in self.message_fields:
                if other.message_fields.count(field) != self.message_fields.count(field):
                    return False
            for enum in self.enums:
                if other.enums.count(enum) != self.enums.count(enum):
                    return False
            
            return True
            
        def __ne__(self, other):
            return not self.__eq__(other)
        
        # Hacked hash.  Messages aren't immutable as implemented.
        # Be careful using hash
        def __hash__(self):
            return hash(self.name) ^ hash(tuple(self.mapped_fields))
        
        def __add__(self, other):
            if not isinstance(other, self.__class__):
                raise Exception("Can't add type %s to a %s" % 
                                (type(other), type(self)))
            s1 = set(self.message_fields + self.fields + self.enums)
            s2 = set(other.message_fields + other.fields + other.enums)
            diff = s1.symmetric_difference(s2)
            self_names = set([obj.name for obj in s1.intersection(diff)])
            other_names = set([obj.name for obj in s2.intersection(diff)])
            colissions = self_names.intersection(other_names)
            if colissions != set():
                raise Exception("Namespace collision between messages on %s" % colissions)
            new_msg = ProtocolBuffer.Message(self.name, self.django_model_class)  
            new_msg.mapped_fields = self.mapped_fields
            new_msg.fields = list(set(self.fields).union(set(other.fields)))
            new_msg.message_fields = list(set(self.message_fields).union(set(other.message_fields)))
            new_msg.enums = list(set(self.enums).union(set(other.enums)))
            return new_msg
            
            
        def addField(self, *fields):
            """ Add a field to this Protocol Buffer message   
                Accepted Arguments:
                field -- (ProtocolBuffer.Field) A field to be added to
                         the message
            """
            # Check if this field is mapped to a django type
            for field in fields:
                if field.dj_type is None:
                    # Has the field already been mapped to a message
                    if type(field.pb_type) == ProtocolBuffer.Message:
                        self.message_fields.append(field)
                    else:
                        self.fields.append(field)
                else:
                    self.mapped_fields.append(field)

        @staticmethod
        def _write_proto_field(field, field_num):
            field_str = ''
            if type(field.pb_type) == ProtocolBuffer.Message:
                field_type = field.pb_type.name
            elif type(field.pb_type) == ProtocolBuffer.Enumeration:
                field_type = field.pb_type.name
            else:
                field_type = field.pb_type.ptype
            field_str = field_str + "\t%s %s %s = %d;\n"
            field_str %= (field.usage,
                        field_type,
                        field.name, field_num)
            return field_str
        
        def __str__(self):
            """ Produces a .proto file message declaration
            """
            #fields = self.fields + self.mapped_fields + self.message_fields
            #field_base = 1
            field_num = 1
            if self.django_model_class != None:
                message = "// Generated from Django model %s\n" % self.django_model_class.__name__
            else:
                message = ""
            message +=   "message " + self.name + " {\n"
            for enum in self.enums:
                enum_str = str(enum)
                for line in enum_str.splitlines():
                    message += "\t%s\n" % line
                #message += str(enum)
#            for i in range(len(fields)):
#                field = fields[i]
#                if type(field.pb_type) == ProtocolBuffer.Message:
#                    field_type = field.pb_type.name
#                elif type(field.pb_type) == ProtocolBuffer.Enumeration:
#                    field_type = field.pb_type.name
#                else:
#                    field_type = field.pb_type.ptype
#                message = message + "    %s %s %s = %d;\n"
#                message %= (field.usage,
#                            field_type,
#                            field.name, i + field_base)
            if len(self.mapped_fields) > 0:# and not self.django_model_class is None: 
                message += "\t// Fields mapped to django model %s\n" % self.django_model_class.__name__ 
                for field in self.mapped_fields:
                    message += ProtocolBuffer.Message._write_proto_field(field, field_num)
                    field_num += 1
            if (len(self.message_fields) + len(self.fields)) > 0:
                message += "\t// Unmapped fields\n"
                for field in self.message_fields:
                    message += ProtocolBuffer.Message._write_proto_field(field, field_num)
                    field_num += 1
                for field in self.fields:
                    message += ProtocolBuffer.Message._write_proto_field(field, field_num)
                    field_num += 1
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
                     out_msg_type, rpc_handler, doc=None):
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
                                       rpc_handler,
                                       doc)
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
        
        def __init__(self, name, in_msg_type, out_msg_type, callable, doc=None):
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
            if doc is None or len(doc) == 0:
                self.doc = callable.__doc__
            else:
                self.doc          = doc
        
    
    
    def __init__(self, module_name='generated', package=''):
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
        self.package     = package
        
    
    def python_mod_name(self):
        return self.module_name + "_pb2"
    
    def proto_filename(self):
        return self.module_name + ".proto"
          
    def addMessage(self, message, user_type=False):
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
            user_type -- If true no mapping will be added for django to
                protobuf conversion.  Conversion can still be done by calling
                toProtoMsg with dest_obj set to the desired type.  This allows
                multiple messages mapped to the same Django type while only having
                a single default message used for auto conversion.
        """
        # Check if there is already a message with the same name
        orig_msg = self.messages.get(message.name, None)
        if self.messages.has_key(message.name):
            #print "Collision on %s" % message.name
            if self.messages[message.name] != message:
                if (self.messages[message.name].mapped_fields == message.mapped_fields):
                    #print "Merging messages"
                    message = self.messages[message.name] + message
                else:
                    raise Exception("There is already a message named %s whose mapped fields differs from the added message" %
                                    message.name)
        
        # Check for a mapping from the django type diffing from the added message        
        if (self.messages.has_key(message.django_model_class) and
            self.messages[message.django_model_class] != message and
            not user_type):
            if (self.messages[message.django_model_class] != message and
                self.messages[message.django_model_class].mapped_fields == message.mapped_fields):
                #print "Merging messages"
                message = self.messages[message.name] + message
            else:
                raise Exception("There is already a message mapped to django type %s whose mapped fields differ from the added message" %
                                message.django_model_class.__name__)
        if orig_msg != message:
            # Add mapping by message name
            self.messages[message.name] = message
            # Add mapping by django model class
            # TODO: Problem here if two messages are added with the same django_model_class
            #       With different fields within the message.  Each message added would override
            #       the previous one.
            if not message.django_model_class is None and user_type == False:
                    self.messages[message.django_model_class] = message
    
            # Add message mapping for fields of type message 
            for field in message.mapped_fields:
                if (isinstance(field.pb_type, ProtocolBuffer.Message) and
                    not field.pb_type.django_model_class is None):
                    #print "In %s.%s Adding type %s, %s" % (message.name, field.name, field.pb_type.name, user_type)
                    self.addMessage(field.pb_type, user_type=user_type)
            for field in message.message_fields:
                #print "In %s.%s Adding type %s, %s" % (message.name, field.name, field.pb_type.name, True)
                self.addMessage(field.pb_type, user_type=True)
            
    
    
    def addRpc(self, service_name, method_name, in_msg, out_msg, handler, doc=None):
        ''' Add a new method to the specified service or create the service
        if it doesn't already exist.  Service will take imput type in_msg
        and return type out_msg.  The optional doc argument will be inserted
        in the genreated .proto file along with the service declaration.
        '''
        service = self.services.get(service_name)
        if service:
            service.addRPCMethod(method_name, in_msg, out_msg, handler, doc)
        else:
            service = ProtocolBuffer.Service(service_name)
            service.addRPCMethod(method_name, in_msg, out_msg, handler, doc)
            self.services[service_name] = service
    
    
    def __str__(self):
        """ Produce a .proto file string for this Protocol Buffer
            instance
        """
        out= "//Protocol Buffer file generated by pbandj.\n\n"
        imported_msgs = []
        for proto in self.imports:
            imported_msgs += proto.messages.values()
            if type(proto) is ProtocolBuffer:
                out += 'import "%s";\n' % proto.proto_filename()
            else:
                out += 'import "%s";\n' % proto
        if len(self.imports) > 0:
            out += "\n"
        if self.package:
            out += "package " + self.package + ";\n"
        for key in self.services.keys():
            service = self.services[key]
            out += "service " + service.name + " {\n"
            for method in service.methods:
                if isinstance(method.doc, str) and len(method.doc) > 0:
                    for doc_line in method.doc.strip().splitlines():
                        out += "\t// %s\n" % doc_line.strip()
                out += "\trpc " + method.name + " (" + \
                       method.in_msg_type.name + ") returns (" + \
                       method.out_msg_type.name + ");\n\n"
            out += "}\n" 
        
        #print imported_msgs
        # Only include messages that are not defined in an import
        for key in self.messages.keys():
            if isinstance(key,str):
                if not self.messages[key] in imported_msgs:
                    out += "%s\n" % str(self.messages[key])
            
        return out
        
    
        
