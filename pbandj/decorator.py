from modelish import mapper
from google.protobuf import descriptor_pb2

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
    '''
    def wrap(model):
        # Define a custom behavior based on decorator parameters
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
                field_num_map = dict([((f.name, _PB_INTERNAL_TYPE_MAP[f.type].name), f.number) for f in  msg_desc.fields])
                print field_num_map
                kwargs['field_num_map'] = field_num_map
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
    
    
def add_field(usage, name, pb_type, num=None):
    ''' Decorator for adding an umapped field to a protocol buffer message
    generated from a django model
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
            mapped_model.add_unmapped_field(usage, name, pb_type)
            return mapped_model
        
        model.generate_protocol_buffer = staticmethod(generate_protocol_buffer)
        return model
    
    return wrap


service_registry = {}

def service(service_name, service_method_name, input_type, output_type):
    ''' Decorator for declaring a pbandj service endpoint
    '''

    def wrap(f):
        service_method = {
            'method' : service_method_name,
            'input' : input_type,
            'output' : output_type,
            'handler' : f 
        }
        service_entry = service_registry.setdefault(service_name, [])
        service_entry.append(service_method)
        return f    
    return wrap