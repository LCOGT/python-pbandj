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


def generate_pb2_module(mapped_module, path="."):
    """ Generate a python pb2 module for this Protocol Buffer.
    
    Args:
    mapped_module - (MappedModule) - module to generate pb2 file for
    path - (str) The path, relative or fully qualified,
           to the directory where the generated module will
           be created
    """
    proto = mapped_module.generate_proto()
    protos = proto.imports + [proto]
    for proto in protos:
        if isinstance(proto, Proto):
            write_proto_file(proto)
    
    system("protoc --python_out=" + path +
           " --proto_path=" + path + " " +
           path + "/" + mapped_module.proto_filename)
               
    return mapped_module.pb2_module_name