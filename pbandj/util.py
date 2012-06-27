import pickle

from os import system
from modelish.pb.proto import Proto

def write_proto_file(proto, path="."):
    f = open(path + "/" + proto.proto_filename(), 'w')
    f.write(proto.__str__())
    f.close()

#def genProto(proto, path="."):
#    if proto != DJANGO_PROTO and not(DJANGO_PROTO in proto.imports):
#        proto.imports.append(DJANGO_PROTO)
#    protos = (DJANGO_PROTO, proto)
#    for proto in protos:
#        _genProto(proto, path)



def save_module(mapped_module, filename="pickeled_pbandj.model"):
    """Save a pickled representation of a mapped_module
    """
    pickeled_model_file = open(mapped_module.module_name + "/" + filename, 'w')
    pickle.dump(mapped_module, pickeled_model_file)
    pickeled_model_file.close()


def restore_module(app, filename="pickeled_pbandj.model"):
    """Restore and return a mapped module from it's pickled
    representation
    
    app - (str) Name of the app to load service module from
    filename - (str) filename in the app directory of the pickled
                     service module
    """
    pickeled_model_file = open(app + "/" + filename, 'r')
    mapped_module = pickle.load(pickeled_model_file)
    pickeled_model_file.close()
    return mapped_module


def save_service_module(mapped_module):
    """Save a pickled representation of a service mapped_module
    """
    save_module(mapped_module, filename="pickled_pbandj.service")
    
    
def restore_service_module(app):
    """Restore and return a service mapped module from it's pickled
    representation
    
    app - (str) Name of the app to load service module from
    filename - (str) filename in the app directory of the pickled
                     service module
    """
    return resore_module(app, filename="pickled_pbandj.service")


def generate_pb2_module(mapped_module, path="."):
    """ Generate a python pb2 module for this Protocol Buffer.
    
    Args:
    mapped_module - (MappedModule) - module to generate pb2 file for
    path - (str) The path, relative or fully qualified,
           to the directory where the generated module will
           be created
    """
    proto = mapped_module.generate_proto()
    write_proto_file(proto)
#    protos = proto.imports + [proto]
#    for proto in protos:
#        # If it is a pbandj Proto object generate a .proto file for it
#        if isinstance(proto, Proto):
#            write_proto_file(proto)

    # Find proto imports that originate from included .proto files and
    # Generate pb2 moduels for them
    for ext_proto in proto.imports:
        if not isinstance(ext_proto, Proto):
            system("protoc --python_out=" + path + 
                   " --proto_path=" + path + " " +
                   path + "/" + ext_proto)
    
    system("protoc --python_out=" + path +
           " --proto_path=" + path + " " +
           path + "/" + mapped_module.proto_filename)
               
    return mapped_module.pb2_module_name