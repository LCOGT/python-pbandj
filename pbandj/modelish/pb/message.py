
class FieldKey(object):
    """An immutable object to use as a unique key for a field
    within a message
    """
    
    def __init__(self, name, pb_type):
        self._name = name
        self._pb_type = pb_type
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (self._name == other._name and
                self._pb_type == other._pb_type)
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __str__(self):
        return self._name + ":" + self._pb_type.ptype
    
    def __hash__(self):
        return hash(self._name) ^ hash(self._pb_type)


class Message(object):
    """ A class containing data describing a protocol buffer
        message.
    """
    
    MAPPED_FIELD_START = 0
    UNMAPPED_FIELD_START = 32768
    
    def __init__(self, msg_name, doc=None):
        """
            Args:
            msg_name - (str) Name of this protocol buffer message
                        buffer message
                        
            Optional Args:
            doc - (str) Comment to be placed at top of message in .proto
        """
        self.name               = msg_name
        self.doc                = doc
        self.enums              = []
        self.fields             = {
                                   None : {
                                           'doc' : None,
                                           'fields' : []
                                           }
                                   }
        
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.name != other.name: return False
        if self.fields != other.fields: return False
        if self.enums != other.enums: return False
        
        return True
        
    def __ne__(self, other):
        return not self.__eq__(other)
    
    # Hacked hash.  Messages aren't immutable as implemented.
    # Be careful using hash
    def __hash__(self):
        return hash(self.name) ^ hash(tuple(self.fields))
    
#    def __add__(self, other):
#        if not isinstance(other, self.__class__):
#            raise Exception("Can't add type %s to a %s" % 
#                            (type(other), type(self)))
#        s1 = set(self.message_fields + self.fields + self.enums)
#        s2 = set(other.message_fields + other.fields + other.enums)
#        diff = s1.symmetric_difference(s2)
#        self_names = set([obj.name for obj in s1.intersection(diff)])
#        other_names = set([obj.name for obj in s2.intersection(diff)])
#        colissions = self_names.intersection(other_names)
#        if colissions != set():
#            raise Exception("Namespace collision between messages on %s" % colissions)
#        new_msg = ProtocolBuffer.Message(self.name, self.django_model_class)  
#        new_msg.mapped_fields = self.mapped_fields
#        new_msg.fields = list(set(self.fields).union(set(other.fields)))
#        new_msg.message_fields = list(set(self.message_fields).union(set(other.message_fields)))
#        new_msg.enums = list(set(self.enums).union(set(other.enums)))
#        return new_msg
        
        
    def all_fields(self):
        """Get a flatened list of all fields
        """
        return reduce(lambda x,y : x + y, [group.fields for group in self.fields.values])
    
    
    def add_field_group(self, field_group, *field, **kwargs):
        """ Add a field to this Protocol Buffer message
        
            Args:
            field_group - (str) A name for the field group
            
            Optional Args:
            group_doc - (str) Comment preceding a group of fields
            field - (pbandj.model.Field) field to be added to
                     the message
        """
        dest_group = self.fields[field_group] =  {
                                                  'doc' : kwargs.get('group_doc', None),
                                                  'fields' : field
                                                 }
    
    
    def field_group(self, group_name):
        """ Get fields in a field group
        
        Args:
        group_name - (str) Name of the field group to get fields for
        
        Returns:
        dict {'doc' : 'field group comment', 'fields' : [pb.field.Field,...]}
        """
        return self.fields.get(group_name, None)
    
    def add_field(self, field_group=None, *field):
        """ Add a field to this Protocol Buffer message   
            Args:
            field_group -- (str) A name for the field group
            
            Optional Args:
            field -- (pbandj.model.Field) field to be added to
                     the message
        """
        dest_group = self.fields[field_group]
        dest_group['fields'] += field
        
    
    def __str__(self):
        """ Produces a .proto file message declaration
        """
        # Start field numbers at the max of the existing field numbers
#        mapped_field_num = 1 + max([x for x in self.field_number_map.values() if x < self.UNMAPPED_FIELD_START] + 
#                               [self.MAPPED_FIELD_START])
#        unmapped_field_num = 1 + max([x for x in self.field_number_map.values() if x >= self.UNMAPPED_FIELD_START]
#                                      + [self.UNMAPPED_FIELD_START])
        
        # Message doc   
        if self.doc != None:
            message = "// %s\n" % self.doc 
        else:
            message = ""
        
        # Start message    
        message +=   "message " + self.name + " {\n"
        
        # Enums up front
        for enum in self.enums:
            enum_str = str(enum)
            for line in enum_str.splitlines():
                message += "\t%s\n" % line
        
        # Fields
        for group_name, field_group in self.fields.items():
            doc = field_group.get('doc')
            if field_group.get('fields'):
                if doc and doc.strip() != '':
                    message += "\t// %s\n" % doc
                for field in field_group['fields']:
                    message += "\t%s\n" % field
                message += "\n"
        
        # Close Message
        message = message + "}\n"
        return message