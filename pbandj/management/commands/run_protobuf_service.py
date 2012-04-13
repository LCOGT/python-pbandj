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
        make_option('--pb2', dest='pb2', default=None,
            help='Protocol Buffer service module'),
    )

    help = "Generated Protocol Buffer service definitions and bindings"
    args = "[appname] [port]"

    def handle(self, app=None, port=None, daemon=True, **options):
       
         # Make sure we have an app
        if not app:
            print "Please specify an app."
            return
        
         # Make sure we have a port
        if not port:
            print "Please specify a port number."
            return
        
        # See if the app exists
        app = app.split(".")[-1]
        service_mod = app + '.' + PBANDJ_SERVICE_MODULES.get(app, PBANDJ_SERVICE_MODULE)
        try:
            service_mod = __import__(service_mod, fromlist=[app])
        except Exception, e:
            print e
            return
        
        # Generate service binding info 
        pb = ProtocolBuffer(app + '_' + 'services')
        for service_name, methods in pbandj.service_registry.items():
            for service_method in methods:
                pb.addRpc(service_name, service_method['method'], service_method['input'].generate_protocol_buffer(), service_method['output'].generate_protocol_buffer(), service_method['handler'])
        
        # Import service rpc implementation
        pb2_path = options.get('pb2')
        pb2_mod = None
        if pb2_path:
            mod_name,file_ext = os.path.splitext(os.path.split(pb2_path)[-1])
            if file_ext == '.py':
                pb2_mod = imp.load_source(mod_name, pb2_path)
            elif file_ext == '.pyc':
                pb2_mod = imp.load_compiled(mod_name, pb2_path)
            else:
                print "Don't understand pb2 value %s" % pb2_path
                sys.exit(1)
        
        # Bind handlers to rpc implementation
        sthread = ProtocolBuffer.ServiceThread(pb2_mod, int(port), daemon, pb.services.values())
        sthread.start()
        while(sthread.is_alive()):
            sthread.join(1)     
#        mod_name = pbandj.genMod(pb)
        
        


#if __name__ == "__main__":
#    from obsdb import pb
#    pbandj.genMod(pb.model, "protobuf/src/main/lcogt/pond")
#    pbandj.genMod(pb.services(), "protobuf/src/main/lcogt/pond")
#    pbandj.genMod(pb.services())
#    
#    pbandj.genMod(pb.model, "client/python/src/lcogt/pond")
#    pbandj.genMod(pb.services(), "client/python/src/lcogt/pond")   
