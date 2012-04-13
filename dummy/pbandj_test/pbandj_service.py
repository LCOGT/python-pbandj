
from pbandj.pbandj import service
import models


@service('SimpleService', 'getSimple', models.Simple, models.Simple)
def SimpleHandler(service_impl, controller, request, done):
            request.val += 1
            done.run(request)
            
            
@service('SimpleService', 'getSimpler', models.Simple, models.Simple)
def SimpleHandler2(service_impl, controller, request, done):
            request.val += 1
            done.run(request)            
            
            
@service('SimplerService', 'simplyGet', models.Simple, models.Simple)
def SimpleHandler2(service_impl, controller, request, done):
            request.val += 1
            done.run(request)             