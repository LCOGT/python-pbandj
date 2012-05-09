import imp

from dj.field import ForeignKey, ManyToMany
from dj.model import Model
from pb import message, field, proto, enum
from types import DJ2PB



def model_to_message(dj_model, pb_field_num_start=0, pb_field_num_map=None):
    """ Create a pbandj protocol buffer model from a pbandj django model
    
    Args:
    pb_field_num_map - (dict) A mapping of protocol buffer fields to field numbers
    """
    # Initialize field number map
    if pb_field_num_map is None:
        pb_field_num_map = {}
#        for pb_field in pb_msg.all_fields():
#            pb_field_num_map[pb_field] = pb_field.field_num

    # Create new message and populate with fields from django model            
    proto_msg = message.Message(dj_model.name)
    pb_msg_fields = []
    pb_enums = []
    pb_field_num = pb_field_num_start
    for dj_field in dj_model.fields:
        if isinstance(dj_field, ForeignKey) and isinstance(dj_field.dj_type, Model):
            fk_pb_msg = model_to_message(dj_field.dj_type)
            pb_field = field.Field(field.OPTIONAL, dj_field.name, fk_pb_msg, pb_field_num + 1)
        elif isinstance(dj_field, ManyToMany) and isinstance(dj_field.dj_type, Model):
            m2m_pb_msg = model_to_message(dj_field.dj_type)
            pb_field = field.Field(field.REPEATED, dj_field.name, m2m_pb_msg, pb_field_num + 1)
        else:
            if(dj_field.choices):
                enum_doc = "Generated from 'choices' for django model field: %s.%s" % (dj_model.name, dj_field.name)
                field_enum = enum.Enum(dj_field.name + "_choices", [a for a,b in dj_field.choices], enum_doc)
                pb_enums.append(field_enum)
                pb_field = field.Field(field.OPTIONAL, dj_field.name, field_enum, pb_field_num + 1)                  
            else:
                pb_field = field.Field(field.OPTIONAL, dj_field.name, DJ2PB.get(dj_field.dj_type).ptype, pb_field_num + 1)
        
        # Check the field number map for a matching field
        if pb_field in pb_field_num_map:
            pb_field.field_num = pb_field_num_map.get(pb_field)
        else:
            pb_field_num += 1
        pb_msg_fields.append(pb_field)
    proto_msg.enums = pb_enums
    group_doc = 'Fields mapped from Django model %s' % dj_model.name
    proto_msg.add_field_group('mapped_fields', *pb_msg_fields, group_doc=group_doc)
    return proto_msg


class MappedModel(object):
    """ Class mapping Django model to internal django model proxy and protocol
    buffer message proxy
    """
    
    MAPPED_FIELD_START = 0
    UNMAPPED_FIELD_START = 32768
    
    def __init__(self, dj_model, pb_field_num_map=None):
        self.dj_model = dj_model
        self.pb_field_num_map = pb_field_num_map
        if self.pb_field_num_map is None:
            self.pb_field_num_map = {}
        # Set to highest field num less than unmapped field start
        self.__next_mapped_field = max([MappedModel.MAPPED_FIELD_START] + 
                                       [x for x in self.pb_field_num_map.values() if x < MappedModel.UNMAPPED_FIELD_START])
        # Set to highest field num greater than unmapped field start
        self.__next_unmapped_field = max([MappedModel.UNMAPPED_FIELD_START] + 
                                         [x for x in self.pb_field_num_map.values() if x >= MappedModel.UNMAPPED_FIELD_START])
        # Create internal django model proxy
        self.pbandj_model = Model.from_django_model(dj_model)
        # Create protocol buffer model proxy
        self.pb_msg = model_to_message(self.pbandj_model,
                                        pb_field_num_start=self.__next_mapped_field,
                                        pb_field_num_map=pb_field_num_map)
        # Create an unmapped field group
        self.pb_msg.add_field_group('unmapped_fields', group_doc="Fields not mapped to Django model")
        
        
    def add_unmapped_field(self, usage, name, pb_type):
        pb_field = field.Field(usage, name, pb_type, self.__next_unmapped_field)
        if pb_field in self.pb_field_num_map:
            pb_field.field_num  = self.pb_field_num_map.get(pb_field)
        else:
            self.__next_unmapped_field += 1
        self.pb_msg.add_field('unmapped_fields', pb_field)
        

#class MappedService(object):
#    
#    def __init__(self):
#        self.services = []
        
    


class MappedModule(object):
    """ Class combining MappedModel objects into a protocol buffer definition
    """
    
    def __init__(self, module_name):
        self.module_name = module_name.strip()
        self.mapped_models = []
        self.services = []
        # Map of service name to map of rpc handlers by rpc name
        self.service_handlers = {}
        self.xtra_proto_imports = []
        

    def add_mapped_model(self, mapped_model):
        self.mapped_models.append(mapped_model)
        
    def add_service(self, service, service_handlers):
        '''Add a pb.Service to the MappedModule
        Args:
        service - (pb.Serivce) a service related to the mapped module
        service_handlers - (dict) keys are pb.Service method names and values
                           are funcions to be called when service is running.
        '''
        self.services.append(service)
        self.service_handlers[service.name] = service_handlers
        
    def add_import(self, imported_proto):
        self.xtra_proto_imports.append(imported_proto)
    
    def generate_proto(self):
        # Create the proto model
        p = proto.Proto(self.module_name)
        for mapped_model in self.mapped_models:
            # Add top level messages to proto model
            p.add_msg(mapped_model.pb_msg)
            # Find messages included as fields and add to proto model
        for service in self.services:
            p.add_service(service)
        for xtra_import in self.xtra_proto_imports:
            p.add_import(xtra_import)
        return p
    
    @property
    def proto_filename(self):
        return self.module_name + ".proto"
    
    
    @property
    def pb2_module_name(self):
        return self.module_name + "_pb2"
    
    def load_pb2(self):
        '''Load and return the pb2 module related to this mapped module
        '''
        pb2_mod = None
        mod_name = self.pb2_module_name
        try:
            pb2_mod = imp.load_source(mod_name, mod_name + ".py")
        except Exception, e:
            pass
        try:
            pb2_mod = imp.load_compiled(mod_name, mod_name + ".pyc")
        except Exception, e:
            pass
        if pb2_mod == None:
            print "Unable to load service module " + mod_name
        return pb2_mod 