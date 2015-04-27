class Service(object):
    """ A class containing data describing a protocol buffer
        service
    """
    
    def __init__(self, name, doc=None):
        """Create a Service instance
         Args:
         name - (str) The name of the protocol buffer
               service
            
         Optional Args:
         doc - (str) Comment to appear in .proto
        """
        self.name    = name
        self.doc     = doc
        self.rpc = {}
    
    
    def add_rpc(self, rpc_name, rpc_in, rpc_out, rpc_doc=None):
        """ Generate a Protocol Buffer RPC
        Args:
        rpc_name - (str) Name of the rpc method being created
                   within the service
        rpc_in - (Message) A Message describing the input to the rpc call
        rpc_out -- (Message) A Message describing the ouput of the rpc call
            
        Optional Args:
        rpc_doc - (str) Comment to appear in .proto
        """
        self.rpc[rpc_name] = RPC(rpc_name, rpc_in, rpc_out, rpc_doc)
        
    
    def __str__(self):
        service = ''
        if self.doc:
            service += '// %s\n' % self.doc
        
        service += 'service %s {\n' % self.name
        
        for rpc_name, rpc in self.rpc.items():
            if rpc.rpc_doc:
                service += '\t// %s\n' % str(rpc.rpc_doc)
            service += '\t%s\n' % str(rpc)
        service += '}\n'
        return service


class RPC(object):
    """ A class encapsulation the description of a Protocol Buffer
    RPC declaration 
    """
    
    def __init__(self, rpc_name, rpc_in, rpc_out, rpc_doc=None):
        """Generate a service rpc 
        Args:
        rpc_name - (str) Name of the rpc method being created
                   within the service
        rpc_in - (Message) A Message describing the input to the rpc call
        rpc_out -- (Message) A Message describing the ouput of the rpc call
           
        Optional Args:
        rpc_doc - (str) Comment to appear in .proto
        """
        self.name         = rpc_name
        self.rpc_in  = rpc_in
        self.rpc_out = rpc_out
        self.rpc_doc = rpc_doc 
        
    
    def __str__(self):
        return 'rpc %s (%s) returns (%s);' % (self.name, self.rpc_in, self.rpc_out)