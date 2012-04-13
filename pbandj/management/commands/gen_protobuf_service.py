"""
Generate protocol buffer representations of models
"""
import imp
import os
import sys

from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import models

from pbandj import pbandj
from pbandj.model import ProtocolBuffer


PBANDJ_SERVICE_MODULES = getattr(settings, 'PBANDJ_SERVICE_MODULES', {})
PBANDJ_SERVICE_MODULE = 'pbandj.handlers'

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
        service_mod = app + '.' + PBANDJ_SERVICE_MODULES.get(app, PBANDJ_SERVICE_MODULE)
        try:
            service_mod = __import__(service_mod, fromlist=[app])
        except Exception, e:
            print e
            return
        
        pb = ProtocolBuffer(app + '_' + 'services')
        pb.imports.append(app + '.proto')
        for service_name, methods in pbandj.service_registry.items():
            for service_method in methods:
                pb.addRpc(service_name, service_method['method'], service_method['input'].generate_protocol_buffer(), service_method['output'].generate_protocol_buffer(), service_method['handler'])
        
        mod_name = pbandj.genMod(pb)
        
        


#if __name__ == "__main__":
#    from obsdb import pb
#    pbandj.genMod(pb.model, "protobuf/src/main/lcogt/pond")
#    pbandj.genMod(pb.services(), "protobuf/src/main/lcogt/pond")
#    pbandj.genMod(pb.services())
#    
#    pbandj.genMod(pb.model, "client/python/src/lcogt/pond")
#    pbandj.genMod(pb.services(), "client/python/src/lcogt/pond")   
