from django.db import models

from modelish import mapper
from modelish.pb import field


# When called with no args and no (), the decorator is called with the
# type or function being decorated as first arg.
# See http://stackoverflow.com/questions/653368/how-to-create-a-python-decorator-that-can-be-used-either-with-or-without-paramet
def protocol_buffer_message(*args, **kwargs):
    ''' Decorator for Django model classes adding static method
    for generating a protocol buffer message definition
    
    Args:
    msg_name - (str) An alternate name to be used for protocol buffer message
    include - (List) A list of field names from the model to
                      be included in the mapping
    exclude - (List) A list of field names to exclude from the
                      model.  Only used if included arg is []
    follow_related - (bool)Follow into relation fields if true or 
                       using pk if false
    no_follow_fields - (List) Field names which should not be followed.
                          Only used if follow_related=True
    no_follow_models - (List) Django models not to follow as relations
    '''
    def wrap(model):
        # Define a custom behavior based on decorator parameters
        #TODO: Rename to something like generate pbandj model
        def generate_protocol_buffer(**pbargs):
            ''' Generate a protocol buffer message descriptor
            
            Returns:
            A pbandj.model.ProtocolBuffer.Message object
            '''
            # Use model name for message name unless msg_name supplied
            msg_name = model.__name__
            if kwargs.has_key('msg_name'):
                msg_name = kwargs['msg_name']
            
            # Create a field number map for old module id supplied
            field_number_map = pbargs.get('field_number_map', {}) 
            if field_number_map:
                print field_number_map
                kwargs['pb_field_num_map'] = field_number_map
            # TODO remove need to pass msg_name as non kwarg
            if kwargs.has_key('msg_name'):
                return mapper.MappedModel(model, **kwargs)
            else:
                return mapper.MappedModel(model, **kwargs)
        
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
        meta = ServiceMeta(service_name, service_method_name, input_type, output_type)
        service_registry.register(f, meta)
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