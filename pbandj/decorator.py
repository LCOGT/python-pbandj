from django.db import models
from google.protobuf import descriptor_pb2

from modelish import mapper
from modelish.pb import field


_PB_INTERNAL_TYPE_MAP = descriptor_pb2._FIELDDESCRIPTORPROTO.enum_types_by_name['Type'].values_by_number


def __msg_name_to_descriptor_name(msg_name):
    ''' Convert a protocol buffer message name to the expected descriptor name
        Ex. test -> _TEST
    '''
    return "_" + msg_name.upper()


def __get_msg_descriptor(pb_mod, msg_name):
    ''' Get the message descriptor for a named message from the supplied module
    '''
    return getattr(pb_mod, __msg_name_to_descriptor_name(msg_name))


# When called with no args and no (), the decorator is called with the
# type or function being decorated as first arg.
# See http://stackoverflow.com/questions/653368/how-to-create-a-python-decorator-that-can-be-used-either-with-or-without-paramet
def protocol_buffer_message(*args, **kwargs):
    ''' Decorator for Django model classes adding static method
    for generating a protocol buffer message definition
    
    Args:
    msg_name - (str) An alternate name to be used for protocol buffer message
    '''
    def wrap(model):
        # Define a custom behavior based on decorator parameters
        #TODO: Rename to something like generate pbandj model
        def generate_protocol_buffer(**pbargs):
            ''' Generate a protocol buffer message descriptor
            
            Args:
            old_pb2_mod - (pb2) A previously generated pb2 module
            
            Returns:
            A pbandj.model.ProtocolBuffer.Message object
            '''
            # Use model name for message name unless msg_name supplied
            msg_name = model.__name__
            if kwargs.has_key('msg_name'):
                msg_name = kwargs['msg_name']
            
            # Create a field number map for old module id supplied
            old_pb2_mod = pbargs.get('old_pb2_mod', None) 
            if old_pb2_mod:
                msg_desc = __get_msg_descriptor(old_pb2_mod, msg_name)
                # Create a dict mapping tuples ('field_name', field_type) to field number
                field_num_map = dict([field.Field(field.OPTIONAL, f.name, _PB_INTERNAL_TYPE_MAP[f.type].name, -1) for f in  msg_desc.fields])
                print field_num_map
                kwargs['pb_field_num_map'] = field_num_map
            # TODO remove need to pass msg_name as non kwarg
            if kwargs.has_key('msg_name'):
                return mapper.MappedModel(model, **kwargs)
            else:
                return mapper.MappedModel(model, **kwargs)
                #return genMsg(django_model_class=model, msg_name=model.__name__, **kwargs)
#            return genMsg(msg_name, model_class, include, exclude, recurse_fk, no_recurse)
        
        model.generate_protocol_buffer = staticmethod(generate_protocol_buffer)
        model.__PBANDJ = True
        return model
    
    if args:
        model = args[0]
        return wrap(model)
    else:
        return wrap
    
    
def add_field(usage, name, pb_type, field_num=None):
    ''' Decorator for adding an umapped field to a protocol buffer message
    generated from a django model
    
    Args:
    usage - (str) protocol buffer usage OPTIONAL, REQUIRED, REPEATED
    name - (str) name of the field
    pb_type - (type) from pbandj.modelish.types
    field_num(optional) - (int) field number to be used in the generated
              protocol buffer message.  Supplying this arg overrides any
              pre existing field_num.  Warning that using this may result
              in duplicate field numbers.  Use with care.
    '''
    
    def wrap(model):
        if not hasattr(model, '__PBANDJ'):
            raise Exception("This doesn't taste like pbandj.  Have you added the %s decorator?" % protocol_buffer_message.__name__)
        
        builder = model.generate_protocol_buffer
        
        def generate_protocol_buffer(**pbargs):
            ''' Generate a protocol buffer message descriptor
            
            Args:
            
            Returns:
            A pbandj.model.ProtocolBuffer.Message object
            '''
            mapped_model = builder(**pbargs)
            mapped_model.add_unmapped_field(usage, name, pb_type, field_num)
            return mapped_model
        
        model.generate_protocol_buffer = staticmethod(generate_protocol_buffer)
        return model
    
    return wrap


def service(service_name, service_method_name, input_type, output_type):
    ''' Decorator for declaring a pbandj service endpoint
    '''

    def wrap(f):
#        service_method = {
#            'method' : service_method_name,
#            'input' : input_type,
#            'output' : output_type,
#            'handler' : f 
#        }
#        service_entry = service_registry.setdefault(service_name, [])
#        service_entry.append(service_method)
#        input_type = input_type.generate_protocol_buffer()
#        output_type = output_type.generate_protocol_buffer()
#        input_model = input_type
#        if isinstance(input_type, type) and models.Model in input_type.__bases__: 
#            input_model = input_type.generate_protocol_buffer()
#        output_model = output_type
#        if isinstance(output_type, type) and models.Model in output_type.__bases__: 
#            output_model = output_type.generate_protocol_buffer()
        meta = ServiceMeta(service_name, service_method_name, input_type, output_type)
        service_registry.register(f, meta)
#        d.__pbandj = meta
#        if not hasattr(f, '__pbandj'):
#            f.__pbandj = {}
#        f.__pbandj['service'] = service_method
        return f    
    return wrap


def service_import(xtra_proto):
    ''' Decorator for adding an external .proto import for a service
    '''

    def wrap(f):
        if not hasattr(f, '_pbandj'):
            raise Exception("This doesn't taste like pbandj.  Have you added the %s decorator?" % service.__name__)
        service_registry.add_proto_import(xtra_proto)
        return f    
    return wrap


class ServiceRegistry(object):
    
    def __init__(self):
        self.services = {}
        self.proto_imports = set()
        
    def register(self, handler, meta):
        """Register a handler method
        
        Args:
        handler - (method) Method to be called by service
        meta - (ServiceMeta) Description of service method
        """
        group = self.services.setdefault(meta.service_name, [])
        handler._pbandj = meta
        group.append(handler)
        
    def add_proto_import(self, xtra_import):
        """Add a .proto to be imported by the proto the services in this registry
        will be declared in.
        """
        self.proto_imports.add(xtra_import)
        
    def methods_by_service_name(self, service_name):
        """Returns list of ServiceMeta objects for the supplied
        service name
        """
        return self.services.get(service_name, [])
    
    def service_names(self):
        """Returns list of service names known to registry
        """
        return self.services.keys()
        

class ServiceMeta(object):
    
    def __init__(self, service_name, service_method_name, input_type, output_type, **kwargs):
        self.service_name = service_name
        self.method_name = service_method_name
        self.input = input_type
        self.output = output_type
        self.xtra = kwargs
        
    
        
service_registry = ServiceRegistry()