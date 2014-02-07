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
from pbandj import util


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
#        make_option('--out', dest='out', default='.',
#            help='Set the output location'),
#        make_option('--target', dest='target', default=None,
#            help='Set the name of the generated .proto file'),
        make_option('--pb2', dest='pb2', default=None,
            help='Maintain field nubering from existing pb2 module'),                                             
    )

    help = "Generated Protocol Buffer definitions according to model"
    args = "[appname] [--all]"

    def handle(self, app=None, **options):
        ### Start of code copied from south apps convert_to_south.py
        # Make sure we have an app
        if not app:
            print "Please specify an app."
            return
        
        # See if the app exists
        app = app.split(".")[-1]
        try:
            app_module = models.get_app(app)
        except ImproperlyConfigured:
            print "There is no enabled application matching '%s'." % app
            return
        
        # Try to get its list of models
        model_list = models.get_models(app_module)
        if not model_list:
            print "This application has no models."
            
        ### End of code copied from south apps convert_to_south.py
        
        pb2_path = options.get('pb2')
        pb2_mod = None
        field_number_map = {}
        if pb2_path:
            mod_name,file_ext = os.path.splitext(os.path.split(pb2_path)[-1])
            if file_ext == '.py':
                pb2_mod = imp.load_source(mod_name, pb2_path)
            elif file_ext == '.pyc':
                pb2_mod = imp.load_compiled(mod_name, pb2_path)
            else:
                print "Don't understand pb2 value %s" % pb2_path
                sys.exit(1)
            field_number_map = util.generate_field_number_map(pb2_mod)
#        pb = ProtocolBuffer(app)
        mapped_module = mapper.MappedModule(app)
        mapped_models = [model.generate_protocol_buffer(old_pb2_mod=pb2_mod, field_number_map=field_number_map) for model in model_list if hasattr(model, '__PBANDJ')]
        for mapped_model in mapped_models:
#            pb.addMessage(msg)
            mapped_module.add_mapped_model(mapped_model)
        
        proto = mapped_module.generate_proto()
        print proto
        util.generate_pb2_module(mapped_module)
#        mod_name = pbandj.genMod(pb)
        app_path, module_file = os.path.split(app_module.__file__) 
        util.save_module(mapped_module, path=app_path)
#        pickeled_model_file = open(app + "/" + "pickeled_pbandj.model", 'w')
#        pickle.dump(mapped_module, pickeled_model_file)
#        pickeled_model_file.close()

#if __name__ == "__main__":
#    from obsdb import pb
#    pbandj.genMod(pb.model, "protobuf/src/main/lcogt/pond")
#    pbandj.genMod(pb.services(), "protobuf/src/main/lcogt/pond")
#    pbandj.genMod(pb.services())
#    
#    pbandj.genMod(pb.model, "client/python/src/lcogt/pond")
#    pbandj.genMod(pb.services(), "client/python/src/lcogt/pond")   
