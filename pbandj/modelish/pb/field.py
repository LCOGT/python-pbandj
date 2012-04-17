
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
        self.pb_type = pb_type
        self.field_num = int(field_num)
        
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (self.name == other.name and
                self.usage == other.usage and
                self.pb_type == other.pb_type and
                self.field_num == other.field_num)
    
    def __ne_(self, other):
        return not self.__eq__(other)
    
    def __str__(self):
        return '%s %s %s = %d;\n' % (self.usage, self.pb_type, self.name, self.field_num)
    
    # Hacked hash.  Fields aren't immutable as implemented.
    # Be careful using hash
    def __hash__(self):
        return hash(self.name) ^ hash(self.usage) ^ hash(self.pb_type) ^ hase(self.field_num)