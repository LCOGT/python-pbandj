#!python

#    Copyright (C) 2009  Zachary Walker
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from time import time, sleep
#from protobuf.channel import SocketRpcChannel
#from pbandj.rpc import ProtoBufRpcRequest
from protobuf import RpcService
import generated_pb2 as proto
    
class AddressBook(object):
    """ A wrapper class for a protocol buffer AddressBook message """
    
    def __init__(self):
        self.service = RpcService(proto.AddressService_Stub, 8091, 'localhost')

    def add_contact(self, name, email, phone, birthday, favorite, groups=[]):
        """ Add a contact to the address book """
        msg = proto.AddressBook()
        msg.name = name
        msg.email = email
        msg.phone = phone
        msg.birthday.year = 1976
        msg.birthday.month = 10
        msg.birthday.day = 17
        msg.favorite_flag = favorite
        for group in groups:
            msg.group.append(group)
        return self.service.add_contact(msg, timeout=5000)
    
    def get_group(self, group_name):
        """ Get the contacts in a group """
        msg = proto.ContactGroup()
        msg.group_name = group_name
        return self.service.get_group(msg, timeout=5000)
