"""
Generate protocol buffer representations of models
"""
import imp
import os
import sys
import pickle

from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import models

from pbandj.modelish import mapper
from pbandj.modelish.pb import proto, service
from pbandj.decorator import service_registry
from pbandj import util

PBANDJ_SERVICE_MODULES = getattr(settings, 'PBANDJ_SERVICE_MODULES', {})
PBANDJ_SERVICE_MODULE = 'pbandj_handlers'

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--out', dest='out', default='.',
            help='Set the output location'),
        make_option('--target', dest='target', default=None,
            help='Set the name of the generated .proto file'),
        make_option('--pb2', dest='pb2', default=None,
            help='Maintain field nubering from existing pb2 module'),                                             
    )

    help = "Generated Protocol Buffer service definitions and bindings"
    args = "[appname]"

    def handle(self, app=None, **options):
       
         # Make sure we have an app
        if not app:
            print "Please specify an app."
            return
        
        # See if the app exists
        app = app.split(".")[-1]
        service_mod = app + '.' + PBANDJ_SERVICE_MODULES.get(app, app + "." + PBANDJ_SERVICE_MODULE)
        try:
            service_mod = __import__(service_mod, fromlist=[app])
        except Exception, e:
            print e
            return
        
#        pb = proto.Proto(app + '_' + 'services')
#        pb.imports.append(app + '.proto')
        mapped_module = mapper.MappedModule(app + '_' + 'services')
        mapped_module.add_import(app + '.proto')
        for xtra_import in service_registry.proto_imports:
            mapped_module.add_import(xtra_import)
        for service_name, handlers in service_registry.services.items():
            pb_service = service.Service(service_name)
            service_handlers = {}
            for handler in handlers:
                meta = handler._pbandj
                service_in = meta.input
                if isinstance(service_in, type) and models.Model in service_in.__bases__: 
                    service_in = service_in.generate_protocol_buffer().pb_msg.name
                service_out = meta.output
                if isinstance(service_out, type) and models.Model in service_out.__bases__: 
                    service_out = service_out.generate_protocol_buffer().pb_msg.name
                pb_service.add_rpc(meta.method_name,
                                   service_in,
                                   service_out)
                # Add a handler entry for this service method 
                service_handlers[meta.method_name] = handler
            mapped_module.add_service(pb_service, service_handlers)
#            pb.add_service(pb_service)
#        print pb
        proto = mapped_module.generate_proto()
        print proto
        util.generate_pb2_module(mapped_module)
#        util.write_proto_file(pb)
        
        pickeled_srvc_file = open(app + "/" + "pickeled_pbandj.service", 'w')
        pickle.dump(mapped_module, pickeled_srvc_file)
        pickeled_srvc_file.close()

#if __name__ == "__main__":
#    from obsdb import pb
#    pbandj.genMod(pb.model, "protobuf/src/main/lcogt/pond")
#    pbandj.genMod(pb.services(), "protobuf/src/main/lcogt/pond")
#    pbandj.genMod(pb.services())
#    
#    pbandj.genMod(pb.model, "client/python/src/lcogt/pond")
#    pbandj.genMod(pb.services(), "client/python/src/lcogt/pond")   
