from django.db import models
from pbandj.model import ProtocolBuffer as Proto
from pbandj import type_map
from pbandj.conversion import Converter

""" Alias for ProtocolBuffer.Field """
Field = Proto.Field


class AddressBook(models.Model):
    """ Address Book contact class extending Django model
    """
    name            = models.CharField(max_length=25)
    phone           = models.CharField(max_length=25)
    email           = models.CharField(max_length=25)
    birthday        = models.DateField()
    favorite_flag   = models.BooleanField()


class ContactGroup(models.Model):
    """ Address Book contact class extending Django model
    """
    group_name            = models.CharField(max_length=25)
    member_name           = models.ForeignKey(AddressBook)
 
# The protocol buffer object    
pbuf = Proto()

def onAddContact(service_impl, controller, request, done):
    """ Handler method for the add_contact RPC described below """
    print "In add contact"
    from generated_pb2 import Response
    resp = Response()
    print "Converting to django"
    converter = Converter()
    try:
        contact = converter.toDjangoObj(pbuf, request)
    except Exception, e:
        print e
    contact.save()
    for group in request.group:
        cont_grp = ContactGroup()
        cont_grp.group_name = group
        cont_grp.member_name = contact
        
        cont_grp.save()
    resp.success = True
    print "About to exit"
    done.run(resp)

def onGetGroup(service_impl, controller, request, done):
    """ Handler method for the get_group RPC method described below """
    print "In onGetGroup"
    from generated_pb2 import ContactGroup as PbGroup
    members = ContactGroup.objects.filter(group_name=request.group_name)
    resp = PbGroup()
    resp.group_name = request.group_name
    print "Adding memebers to response msg"
    for contact in members:
        print "Converting"
        converter = Converter()
        converter.toProtoMsg(pbuf, contact.member_name, resp.member.add())
        print "Done converting"
    done.run(resp)
    
def genProto():
    """ Generate and return the protocol buffer description object """
    
    # Create a generic response message
    rsp_msg = Proto.Message("Response")
    rsp_msg.addField(Field(Field.OPTIONAL, "success",
                           type_map.base.PB_TYPE_BOOL))
    rsp_msg.addField(Field(Field.OPTIONAL, "error_code",
                           type_map.base.PB_TYPE_INT32))
    rsp_msg.addField(Field(Field.OPTIONAL, 'error_reason',
                           type_map.base.PB_TYPE_STRING))
    # Add the respons message to the proto
    pbuf.addMessage(rsp_msg)
    
    # Create a contact message from the AddressBook model
    cont_msg = type_map.genMsg('AddressBook',AddressBook,exclude=["id"])
    cont_msg.addField(Field(Field.REPEATED,'group',
                            type_map.base.PB_TYPE_STRING))
    pbuf.addMessage(cont_msg)
    
    # Create a service accepting contact messages
    pbuf.addRpc("AddressService",'add_contact',
                     cont_msg, rsp_msg, onAddContact)
    
    # Create a group message from the ContactGroup Model
    grp_msg = type_map.genMsg('ContactGroup',ContactGroup,exclude=["member_name"])
    grp_msg.addField(Field(Field.REPEATED,'member', cont_msg))
    pbuf.addMessage(grp_msg)
    
    # Create a service returning memebers of a contact group
    pbuf.addRpc("AddressService", 'get_group',
                    grp_msg, grp_msg, onGetGroup)
    return pbuf