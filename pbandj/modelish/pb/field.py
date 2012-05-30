from pbandj.modelish import types 

from message import Message, FieldKey
from enum import Enum


OPTIONAL = "optional"
REQUIRED = "required"
REPEATED = "repeated"

        

class Field(object):
    """ A class containing data describing a
        protocol buffer message field and any
        mapping to a related Django field
    """
    
    
    
    def __init__(self, usage, name, pb_type, field_num):
        """
            Accepted Arguments:
            usage -- (String) Used of this field in the .proto file
                     OPTIONAL = "optional"
                     REQUIRED = "required"
                     REPEATED = "repeated"
            name-- (String) Name of this field
            pb_type -- (String) The Protocol Buffer type for this
                       message field
            field_num -- (int) Field number within a message
        """
        self.name    = name
        self.usage   = usage
        # If a string was passed as the type get the type get a wrapper type
        if isinstance(pb_type, str):
            self.pb_type = getattr(types, types.pbtype_name(pb_type))
        else:
            self.pb_type = pb_type
        self.field_num = int(field_num)
        self.field_key = FieldKey(name, pb_type)
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (self.name == other.name and
                self.usage == other.usage and
                self.pb_type == other.pb_type and
                self.field_num == other.field_num)
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __str__(self):
        if isinstance(self.pb_type, Message):
            return '%s %s %s = %d;' % (self.usage, self.pb_type.name, self.name, self.field_num)
        elif isinstance(self.pb_type, Enum):
            return '%s %s %s = %d;' % (self.usage, self.pb_type.name, self.name, self.field_num)
        else:
            return '%s %s %s = %d;' % (self.usage, self.pb_type.ptype, self.name, self.field_num)
    
    # Hacked hash.  Fields aren't immutable as implemented.
    # Be careful using hash
    def __hash__(self):
        return hash(self.name) ^ hash(self.pb_type)