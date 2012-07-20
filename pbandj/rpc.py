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
from protobuf.socketrpc.channel import SocketRpcChannel
from protobuf.socketrpc.server import SocketRpcServer

# Module imports
from modelish.pb.service import Service

# Constants
RPC_HOST = "localhost"
RPC_PORT = 8091

class ServiceThread(threading.Thread):


    def __init__(self, mapped_module, service_module, port, daemon=False):
        threading.Thread.__init__(self)
        self.mapped_module = mapped_module
        self.service_module = service_module
        self.service_pb2_module = service_module.load_pb2()
        self.port = port
        self.setDaemon(daemon)


    def protobuf_rpc_closure(self, handler):
        ''' Returns a function implementing the expected method signature for
        a protobuf rpc handler by wrapping the implemented handler function
        '''
        def protobuf_rpc_wrapper(controller, request, callback):
            try:
                result = handler(request,
                                 mapped_module=self.mapped_module,
                                 service_module=self.service_module)
                callback.run(result)
            except Exception, e:
                controller.handleError(1, e.message)
        return protobuf_rpc_wrapper


    def run(self):
        """ Start service thread """
        # Create a server instance
        import ipdb; ipdb.set_trace();
        server = SocketRpcServer(self.port,host='')
        for service in self.service_module.services:
            service_class = getattr(self.service_pb2_module, service.name)
            newservice = service_class()
            for method_name, handler in self.service_module.service_handlers[service.name].items():
                # Attatch a handler to the service class
                setattr(newservice, method_name, self.protobuf_rpc_closure(handler))
            server.registerService(newservice)

        # Start the server
        server.run();
