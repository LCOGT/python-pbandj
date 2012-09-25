import imp

from dj.field import OneToOne, ForeignKey, ManyToMany
from dj.model import Model
from pb import message, field, proto, enum
from types import DJ2PB
from pbandj.conversion import Converter
    

def model_to_field_map(pbandj_dj_model, pb_field_num_start=0, pb_field_num_map=None):
    """ Create a mapping by field name to 
        (django_pbandj_model, protobuf_pbandj_model) field tuples.
    
    Args:
    pbandj_dj_model - (model.dj.model) - Model used to create field map
    pb_field_num_map - (dict) A mapping of protocol buffer fields to field numbers
    """
    field_maps =  model_to_field_map.processed_models.get(pbandj_dj_model, None)
    if field_maps != None:
        return field_maps
    else:
        field_maps = [{}, {}]
        model_to_field_map.processed_models[pbandj_dj_model] = field_maps
    
    # Initialize field number map
    if pb_field_num_map is None:
        pb_field_num_map = {}
#        for pb_field in pb_msg.all_fields():
#            pb_field_num_map[pb_field] = pb_field.field_num

    # Create new message and populate with fields from django model            
    dj_to_pb_field_map = field_maps[0]
    pb_field_num = pb_field_num_start
    for pbandj_dj_field in pbandj_dj_model.fields:
        if isinstance(pbandj_dj_field, ForeignKey):
            if isinstance(pbandj_dj_field.dj_type, Model):
                fk_field_map, fk_rel_map = model_to_field_map(pbandj_dj_field.dj_type)
                fk_pb_msg = field_map_to_message(pbandj_dj_field.dj_type.name, fk_field_map, fk_rel_map)
                pbandj_pb_field = field.Field(field.OPTIONAL, pbandj_dj_field.name, fk_pb_msg, pb_field_num + 1)
            else:
                pbandj_pb_field = field.Field(field.OPTIONAL, pbandj_dj_field.name,  DJ2PB.get(pbandj_dj_field.dj_type), pb_field_num + 1)
        elif isinstance(pbandj_dj_field, ManyToMany):
            if isinstance(pbandj_dj_field.dj_type, Model):
                m2m_field_map, m2m_rel_map = model_to_field_map(pbandj_dj_field.dj_type)
                m2m_pb_msg = field_map_to_message(pbandj_dj_field.dj_type.name, m2m_field_map, m2m_rel_map)
                pbandj_pb_field = field.Field(field.REPEATED, pbandj_dj_field.name, m2m_pb_msg, pb_field_num + 1)
            else:
                pbandj_pb_field = field.Field(field.REPEATED, pbandj_dj_field.name, DJ2PB.get(pbandj_dj_field.dj_type), pb_field_num + 1)
        else:
            if(pbandj_dj_field.choices):
                enum_doc = "Generated from 'choices' for django model field: %s.%s" % (pbandj_dj_model.name, pbandj_dj_field.name)
                field_enum = enum.Enum(pbandj_dj_field.name.capitalize() , [a for a,b in pbandj_dj_field.choices], enum_doc)
                pbandj_pb_field = field.Field(field.OPTIONAL, pbandj_dj_field.name, field_enum, pb_field_num + 1)                  
            else:
                pbandj_pb_field = field.Field(field.OPTIONAL, pbandj_dj_field.name, DJ2PB.get(pbandj_dj_field.dj_type), pb_field_num + 1)
        
        # Check the field number map for a matching field
        if pbandj_pb_field.field_key in pb_field_num_map.keys():
            pbandj_pb_field.field_num = pb_field_num_map.get(pbandj_pb_field.field_key)
        else:
            pb_field_num += 1
        dj_to_pb_field_map[pbandj_pb_field.name] = (pbandj_dj_field, pbandj_pb_field)
    
    # Add fields for mapped relations
    dj_to_pb_relation_map = field_maps[1]
    for pbandj_dj_relation in pbandj_dj_model.related_fields:
        if isinstance(pbandj_dj_relation, OneToOne):
            if isinstance(pbandj_dj_relation.dj_type, Model):
                fk_field_map, fk_rel_map = model_to_field_map(pbandj_dj_relation.child_model)
                fk_pb_msg = field_map_to_message(pbandj_dj_relation.child_model.name, fk_field_map, fk_rel_map)
                pbandj_pb_field = field.Field(field.OPTIONAL, pbandj_dj_relation.related_model_field_name, fk_pb_msg, pb_field_num + 1)
            else:
                pbandj_pb_field = field.Field(field.OPTIONAL, pbandj_dj_relation.related_model_field_name,  DJ2PB.get(pbandj_dj_relation.dj_type), pb_field_num + 1)
        elif isinstance(pbandj_dj_relation, ForeignKey):
            if isinstance(pbandj_dj_relation.dj_type, Model):
                fk_field_map, fk_rel_map = model_to_field_map(pbandj_dj_relation.child_model)
                fk_pb_msg = field_map_to_message(pbandj_dj_relation.child_model.name, fk_field_map, fk_rel_map)
                pbandj_pb_field = field.Field(field.REPEATED, pbandj_dj_relation.related_model_field_name, fk_pb_msg, pb_field_num + 1)
            else:
                pbandj_pb_field = field.Field(field.REPEATED, pbandj_dj_relation.related_model_field_name,  DJ2PB.get(pbandj_dj_relation.dj_type), pb_field_num + 1)
        elif isinstance(pbandj_dj_relation, ManyToMany):
            if isinstance(pbandj_dj_relation.dj_type, Model):
                m2m_field_map, m2m_rel_map = model_to_field_map(pbandj_dj_relation.child_model)
                m2m_pb_msg = field_map_to_message(pbandj_dj_relation.child_model.name, m2m_field_map, m2m_rel_map)
                pbandj_pb_field = field.Field(field.REPEATED, pbandj_dj_relation.related_model_field_name, m2m_pb_msg, pb_field_num + 1)
            else:
                pbandj_pb_field = field.Field(field.REPEATED, pbandj_dj_relation.related_model_field_name, DJ2PB.get(pbandj_dj_relation.dj_type), pb_field_num + 1)
        
        # Check the field number map for a matching field
        if pbandj_pb_field.field_key in pb_field_num_map.keys():
            pbandj_pb_field.field_num = pb_field_num_map.get(pbandj_pb_field.field_key)
        else:
            pb_field_num += 1
        dj_to_pb_relation_map[pbandj_pb_field.name] = (pbandj_dj_relation, pbandj_pb_field)

    return field_maps
model_to_field_map.processed_models = {}


def field_map_to_message(name, field_map, relation_map):
    pbandj_pb_msg = message.Message(name)
    # Extract mapped pbandj pb fields
    pbandj_pb_fields = [mapped_field[1] for mapped_field in field_map.values()]
    pbandj_pb_relations = [mapped_field[1] for mapped_field in relation_map.values()]
    # Find any enums related to those fields and add them to the message
    pbandj_pb_enums = [field.pb_type for field in pbandj_pb_fields if isinstance(field.pb_type, enum.Enum)]
    pbandj_pb_msg.enums += pbandj_pb_enums
    # Add mapped field group to pbandj pb message model
    field_group_doc = 'Fields mapped from Django model %s' % name
    pbandj_pb_msg.add_field_group('mapped_fields', *pbandj_pb_fields, group_doc=field_group_doc)
    # Add relation field group to pbandj pb message model
    relation_group_doc = 'Fields mapped from relations to Django model %s' % name
    pbandj_pb_msg.add_field_group('mapped_relations', *pbandj_pb_relations, group_doc=relation_group_doc)
    # Add unmapped field group pbandj pb message model
    pbandj_pb_msg.add_field_group('unmapped_fields', group_doc="Fields not mapped to Django model")
    return pbandj_pb_msg
        

class MappedModel(object):
    """ Class mapping Django model to internal django model proxy and protocol
    buffer message proxy
    """
    
    MAPPED_FIELD_START = 0
    UNMAPPED_FIELD_START = 32768
    
    def __init__(self, dj_model, pb_field_num_map=None, msg_name=None, **kwargs):
        '''Create a MappedModel
        If a field number map is provided, field numbering will start from
        the max mapped field numbers to prevent collissions with fields that
        may have previously existed in the message. 
        
        Args:
        dj_model - (django.db.Model type) A type extending django.db.Model
        pb_field_num_map - (dict) A mapping of pbandj pb fields to field numbers
        '''
        # The actual django type
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
        # Create pbandj dj model
        self.pbandj_dj_model = Model.from_django_model(dj_model, **kwargs)
        
        # Create field map
        fields, relations = model_to_field_map(self.pbandj_dj_model,
                                                     pb_field_num_start=self.__next_mapped_field,
                                                     pb_field_num_map=pb_field_num_map)
        self.pb_to_dj_field_map = fields
        self.pb_to_dj_relation_map = relations
        
        # Create pbandj pb messaage
        if msg_name == None:
            msg_name = self.pbandj_dj_model.name
        self.pbandj_pb_msg = field_map_to_message(msg_name, fields, relations)
    
    
    def mapped_fields(self):
        '''Get the field mapping for this model
        Returns dict { 'field_name' : (pb.field, dj.field),...}
        '''
        return self.pb_to_dj_field_map
        
    def add_unmapped_field(self, usage, name, pb_type, field_num=None):
        """ Add an unmapped field to the mapped model.
        
        Args:
        usage - (str) protocol buffer usage OPTIONAL, REQUIRED, REPEATED
        name - (str) name of the field
        pb_type - (type) from pbandj.modelish.types
        field_num(optional) - (int) field number to be used in the generated
                  protocol buffer message.  Supplying this arg overrides any
                  pre existing field_num.  Warning that using this may result
                  in duplicate field numbers.  Use with care.
        """
        # Pick the next available field number if it wasn't supplied
        if field_num == None:
            field_num = self.__next_unmapped_field 
        pb_field = field.Field(usage, name, pb_type, field_num)
        
        # See if there is a field in the field map so we keep the field_num
        if pb_field in self.pb_field_num_map and field_num == None:
            pb_field.field_num  = self.pb_field_num_map.get(pb_field)
        else:
            # Dont increment unless the generated field number was used
            self.__next_unmapped_field += 1
        self.pbandj_pb_msg.add_field('unmapped_fields', pb_field)
        
    
    @property
    def unmapped_fields(self):
        """ List of unmapped protocol buffer fields asoociated with this
        pbandj mapped model
        """
        #TODO: Replace unmapped_fields with constant throughout code
        return self.pbandj_pb_msg.field_group('unmapped_fields').get('fields', [])


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
        self.__pb2 = None
        

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
            p.add_msg(mapped_model.pbandj_pb_msg)
            # Find messages included as fields and add to proto model
            # TODO: Add multilevel field check for other messages
            for field in mapped_model.pbandj_pb_msg.all_fields():
                if isinstance(field.pb_type, message.Message):
                    p.add_msg(field.pb_type) 
        for service in self.services:
            p.add_service(service)
        for xtra_import in self.xtra_proto_imports:
            p.add_import(xtra_import)
        return p
    
    def converter(self):
        """Convenience method to get a Converter object for
        this mapped_module
        """
        return Converter(self)
    
    @property
    def proto_filename(self):
        return self.module_name + ".proto"
    
    
    @property
    def pb2_module_name(self):
        return self.module_name + "_pb2"
    
    def load_pb2(self):
        '''Load and return the pb2 module related to this mapped module
        '''
        if self.__pb2:
            return self.__pb2
        print "Importing pb2 module for", self.module_name
        pb2_mod = None
        mod_name = self.pb2_module_name
        try:
            pb2_mod = imp.load_source(mod_name, mod_name + ".py")
        except Exception, e:
            try:
                pb2_mod = imp.load_compiled(mod_name, mod_name + ".pyc")
            except Exception, e:
                pass
        if pb2_mod == None:
            print "Unable to load service module " + mod_name
        self.__pb2 = pb2_mod
        return pb2_mod 