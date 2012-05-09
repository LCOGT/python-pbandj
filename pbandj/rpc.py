#!python

#    Copyright (C) 2009  Zachary Walker
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Standard library imports
import threading

from time import time, sleep

# Third party imports
from protobuf.channel import SocketRpcChannel
from protobuf.server import SocketRpcServer

# Module imports
from modelish.pb.service import Service

# Constants
RPC_HOST = "localhost"
RPC_PORT = 8091

class ServiceThread(threading.Thread):

    def __init__(self, mapped_module, port, daemon=False):
        threading.Thread.__init__(self)
        self.module = mapped_module.load_pb2()
        self.mapped_module = mapped_module
#        for service in self.mapped_module.services:
#            print type(service)
#            if isinstance(service, Service):
#                print "is a service"
#                self.services.append(service)
        self.port = port
        self.setDaemon(daemon)

#            def _createHandler(self, func):
#                def handler(service_impl, controller, request, done):
#                    try:
#                        result = func(request)
#                    except Exception, e:
#                        controller.handleError(e, e.__str__())
#                    done.run(result)

    def run(self):
        """ Start service thread """
        # Create a server instance
        server = SocketRpcServer(self.port,host='')
        for service in self.mapped_module.services:
            print "handling service " + service.name
            service_class = self.module.__dict__[service.name]
#            handlers = {}
#
#            # Link each method to its handler
#            for method in service.rpc.values():
#                print "handling method " + method.name
#                #handlers[method.name] = self._createHandler(method.handler)
#                print "using handler " + method.handler
#                handlers[method.name] = method.handler

            # Extend Service class and add handlers
            newservice = type(service.name + "Impl",
                          (service_class,), self.mapped_module.service_handlers[service.name])
            server.registerService(newservice())

        # Start the server
        server.run();



class ProtoBufRpcRequest(object):
    """ Class abstracting the Protocol Buffer RPC calls for a supplied
        service stub.
    """
  
    def __init__(self, service_stub_class, port=RPC_PORT, host=RPC_HOST):
        """ Contruct a new ProtoBufRpcRequest and return it.

            Accepted Arguments:
            service_stub_class -- (Service_Stub) The client side RPC
                                  stub class produced by protoc from
                                  the .proto file
            port -- (Integer) The port on which the service is running
                    on the RPC server. Default is value of
                    pond_client.RPC_PORT
            host -- (String) The hostname or IP address of the server
                    running the RPC service. Default is value of
                    pond_client.RPC_HOST
        """
        self.service_stub_class = service_stub_class
        self.port               = port
        self.host               = host
        
        #go through service_stub methods and add a wrapper function to 
        #this object that will call the method with only the msg as the arg
        for method in service_stub_class.GetDescriptor().methods:
            #Add service methods to the this object
            self.__dict__[method.name] = \
                lambda msg, timeout, service=self, method=method.name : service.call(
                    service_stub_class.__dict__[method], msg, timeout)
            
            #This is just a convenience that adds service methods to the
            #instance objects namespace.  No longer do it this way since
            #the  closures above are cleaner
            #self.__dict__[method.name] = \
            #    service_stub_class.__dict__[method.name]

    
    def call(self, rpc, msg, timeout):
        """ Save the object that has been created and return the response.
            Will timeout after timeout ms if response has not been received
            
            Accepted Arguments:
            timeout -- (Integer) ms to wait for a response before returning
        """
                
        # Define local callback function to handle RPC response
        # and initialize result dict
        result = {"done":False, "success":False, "response":None,
                        "error_msg":"timeout", "error_code":None}
        #Can't use just a simple boolean for 'done' because of the way it is
        #referenced in the callback.  The scope isn't clear and python
        #will redefine 'done' rather than change the value unless explicitly
        #defined as 'global done'
        #done = False
        def callback(request, response):
            result["response"]  = response
            result["done"]      = True
            result["error_msg"] = ""
            result["success"]   = True
        
        #Setup the RPC channel
        channel     = SocketRpcChannel(host=self.host, port=self.port)
        controller  = channel.newController()
        service     = self.service_stub_class(channel)
        
        #Make the RPC call and pass in a generic object with a
        #function called "run" linked to callback
        try:
            #Attempting to do something similar to a JAVA anonymous class
            #Create an instalce of a new generic type initialized with a
            #dict that has a run method pointing to the callback function
            rpc(service, controller, msg, type("", (), {"run":callback})())
        except Exception, info:
            print controller.error
        except:
            print controller.error
        end = time() + (timeout / 1000)
        
        #Tight loop waiting for timeout or callback to set done to True 
        while time() < end and not result["done"]:
            pass
        return result
