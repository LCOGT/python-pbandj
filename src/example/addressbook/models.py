from django.db import models
from pbandj.pbandj import ProtocolBuffer as Proto

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
 
#The protocol buffer object    
pbuf = Proto()

def onAddContact(service_impl, controller, request, done):
    """ Handler method for the add_contact RPC described below """
    print "In add contact"
    from generated_pb2 import Response
    resp = Response()
    print "Converting to django"
    contact = pbuf.toDjango(request)
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
    print "Adding memebers"
    for contact in members:
        print "Converting"
        pbuf.toProtoMsg(contact.member_name, resp.member.add())
        print "Done converting"
    done.run(resp)
    
def genProto():
    """ Generate and return the protocol buffer description object """
    
    #Create a generic response message
    rsp_msg = Proto.Message("Response")
    rsp_msg.addField(Field(Field.OPTIONAL, "success", Field.BOOL))
    rsp_msg.addField(Field(Field.OPTIONAL, "error_code", Field.INT32))
    rsp_msg.addField(Field(Field.OPTIONAL, 'error_reason', Field.STRING))
    #Add the respons message to the proto
    pbuf.addMessage(rsp_msg)
    
    #Create a contact message from the AddressBook model
    cont_msg = pbuf.genMsg('AddressBook',AddressBook,exclude=["id"])
    cont_msg.addField(Field(Field.REPEATED,'group',Field.STRING))
    #Create a service accepting contact messages
    pbuf.genRpc("AddressService",'add_contact',
                     cont_msg, rsp_msg, onAddContact)
    
    #Create a group message from the ContactGroup Model
    grp_msg = pbuf.genMsg('ContactGroup',ContactGroup,exclude=["member_name"])
    grp_msg.addField(Field(Field.REPEATED,'member', cont_msg))
    #Create a service returning memebers of a contact group
    pbuf.genRpc("AddressService", 'get_group',
                    grp_msg, grp_msg, onGetGroup)
    return pbuf