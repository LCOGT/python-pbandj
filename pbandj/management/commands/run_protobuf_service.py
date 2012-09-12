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

from pbandj.rpc import ServiceThread
from pbandj import util


PBANDJ_SERVICE_MODULES = getattr(settings, 'PBANDJ_SERVICE_MODULES', {})
PBANDJ_SERVICE_MODULE = 'pbandj_handlers'

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
        try:
            app_module = models.get_app(app)
        except ImproperlyConfigured:
            print "There is no enabled application matching '%s'." % app
        app_path = os.path.split(app_module.__file__)[0]
        # Load the pickled service module
        mapped_module = util.restore_module(app, path=app_path)
        service_module = util.restore_service_module(app, path=app_path)
        
        
        # Bind handlers to rpc implementation
        sthread = ServiceThread(mapped_module, service_module, int(port), daemon)
        sthread.start()
        while(sthread.is_alive()):
            sthread.join(1)     
        
        

