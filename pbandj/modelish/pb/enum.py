

class Enum(object):
    
    def __init__(self, name, values=None, doc=None):
        '''Create an Enumeration object with given name and list of values
        to be enumerated
        
        Args:
        name - (str) name used for .proto enum type
        values - (list) list of string values to enumerated or tuples (str, int)
                 to set the enum value explicitly
        doc - (str) doc string to appear in .proto file 
        '''
        self.name = name
        self.doc = doc
        # Construct a 2 way map from string to val
        self.values = [(str(values[i].strip()), i) for i in range(len(values))]
        self.values += [(i, val) for val, i in self.values]
        self.values = dict(self.values)
        

    def __eq__(self, other):
        
        if not isinstance(other, self.__class__):
            return False
        
        return (self.name == other.name and
                self.values == other.values and 
                self.doc == other.doc
                )
        
    def __ne__(self, other):
        
        return not self.__eq__(other)
    
    
    def __getitem__(self, item):
        return self.values[item]
   
 
    # Hacked hash.  Enums aren't imutable as implemented.
    # Be careful using hash
    def __hash__(self):
        
        return hash(self.name) ^ hash(tuple(self.values.items()))
    
    def __str__(self):
        if self.doc is None:
            proto = ''
        else:
            proto = "// %s\n" % str(self.doc).strip()
        proto += 'enum %s {\n' % self.name
        for key, val in self.values.items():
            if(type(key) == str):
                proto += '\t%s = %d;\n' % (key, self.values[key])
        proto += '}\n\n'
        return proto