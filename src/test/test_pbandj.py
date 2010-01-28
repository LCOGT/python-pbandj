#!/usr/bin/python
# Copyright (C) 2009  Las Cumbres Observatory <lcogt.net>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
'''test_pbandj.py - Unittests for pbandj

Authors: Zach Walker (zwalker@lcogt.net)
Dec 2009
'''
import unittest
import os
from datetime import datetime

# Set the enviroment variable Django looks at to find db settings
from django.conf import ENVIRONMENT_VARIABLE
os.environ[ENVIRONMENT_VARIABLE] = 'django_test.settings'

from django.db import models as django_models
from pbandj.model import ProtocolBuffer
from pbandj.type_map import DJ2PB, genMsg
from pbandj.conversion import Converter
from pbandj import pbandj
from django_test.test_app import models
from protobuf import RpcService


class MessageRenameTestCase(unittest.TestCase):
    '''Test mapping when message name does not match
    django type name
    '''
    global proto
     
    def setUp(self):
        self.module_name = "simple_test"
        self.pb = ProtocolBuffer(self.module_name)
        self.simple = genMsg('SimpleRename', models.Simple)
        self.pb.addMessage(self.simple)
        mod_name = pbandj.genMod(self.pb)
        global proto
        proto = __import__(mod_name)
        self.con = Converter()
        
    def test_mappingExists(self):
        self.assert_(not self.pb.messages.get('SimpleRename') is None,
                     'No mapping by message name to message object')
        self.assert_(not self.pb.messages.get(models.Simple) is None,
                     'No mapping by django type to message object')
        self.assertEqual(self.pb.messages['SimpleRename'],
                         self.pb.messages[models.Simple],
                         'mapping from string not equal to mapping from django type')
    
    def test_invertible(self):
        msg = proto.SimpleRename()
        msg.val = 22
        django = self.con.toDjangoObj(self.pb, msg)
        msg = self.con.toProtoMsg(self.pb, django, proto)
         

class OneOfEverythingTestCase(unittest.TestCase):
    
    def setUp(self):
        self.module_name = "ooe_test"
        self.pb = ProtocolBuffer(self.module_name)
        self.ooe = genMsg('OneOfEverything',
                                        models.OneOfEverything)
        self.pb.addMessage(self.ooe)
        
        self.django_class_fields = [field for field in 
                               models.OneOfEverything._meta.local_fields]
        self.pb_field_names = [f.name for f in self.ooe.mapped_fields]

    def test_genMsg_field_types(self):
        ''' Ensure that there is a type map definition for each Django field
            type
        '''
        for field in self.django_class_fields:
            self.assert_(DJ2PB.get(type(field)) != None,
                         "No protocol buffer type mapped to %s Django type" % 
                         type(field).__name__)
    
    def test_genMsg_fields_exist(self):
        ''' Ensure that all fields from the django type exist in the generated
            protocol buffer type and their type matches the type map
        '''
        pb_fields_by_name = dict([(f.name, f) for f in self.ooe.mapped_fields])
        for field in self.django_class_fields:
            self.assert_(self.pb_field_names.count(field.name) > 0,
                         "Django field %s does not exist in protocol buffer message" % field.name)
            pb_field = pb_fields_by_name[field.name]
            dj_type = type(field)
            if isinstance(pb_field.pb_type, ProtocolBuffer.Message):
                self.assert_(pb_field.pb_type == DJ2PB[dj_type],
                             "Protocol Buffer field type %s does not match type %s specified in type map for Django type %s" %
                             (pb_field.pb_type, DJ2PB[dj_type],
                              dj_type.__name__))
            else:
                self.assert_(type(pb_field.pb_type) == DJ2PB[dj_type],
                             "Protocol Buffer field type %s does not match type %s specified in type map for Django type %s" %
                             (type(pb_field.pb_type), DJ2PB[dj_type],
                              dj_type.__name__))
    
    def test_genMod(self):
        '''Test that the generated mod name is correct and the module is 
           importable
        '''
        mod_name = pbandj.genMod(self.pb)
        self.assertEqual(mod_name, self.module_name + "_pb2",
                         "Module name does not match name passed in to ProtocolBuffer() constructor")
        try:
            proto = __import__(mod_name)
        except ImportError, ie:
            self.assert_(False,
                     "Failed to import generated python module")


class OneOfEverythingUsageTestCase(unittest.TestCase):
    
    proto = None
    
    def setUp(self):
        self.module_name = "ooe_test"
        self.pb = ProtocolBuffer(self.module_name)
        self.ooe = genMsg('OneOfEverything',
                                        models.OneOfEverything)
        self.pb.addMessage(self.ooe)
        
        self.django_class_fields = [field for field in 
                               models.OneOfEverything._meta.local_fields]
        self.pb_field_names = [f.name for f in self.ooe.mapped_fields]
        mod_name = pbandj.genMod(self.pb)
        global proto
        proto = __import__(mod_name)
        
        ooe = proto.OneOfEverything()
        ooe.bool_test = True
        ooe.char_test = "ABC123"
        ooe.comma_test = "A,B,C"
        ooe.date_test.year = 1980
        ooe.date_test.month = 6
        ooe.date_test.day = 10
        ooe.date_time_test.year = 1989
        ooe.date_time_test.month = 9
        ooe.date_time_test.day = 19
        ooe.date_time_test.time.hour = 1
        ooe.date_time_test.time.minute = 2
        ooe.date_time_test.time.second = 3
        ooe.decimal_test = 12.34
        ooe.float_test = 56.789
        ooe.email_test = 'zman@namz.com'
        ooe.file_test = "path/to/file"
        ooe.image_test = "/path/to/image"
        ooe.int_test = -1
        ooe.ip_test = '123.456.789.123'
        ooe.null_bool_test = False
        ooe.pos_int_test = 1
        ooe.pos_sm_int_test = 1
        ooe.slug_test = 'This is a slug'
        ooe.sm_int_test = -1
        ooe.text_test = 'This is some text'
        ooe.time_test.hour = 12
        ooe.time_test.minute = 13
        ooe.time_test.second = 14
        ooe.url_test = 'http://www.lcogt.net'
        ooe.xml_test = '<abc>123</abc>'
        self.ooe = ooe
        self.converter = Converter()
        
        
    def test_conversion_invertible(self):
        '''Make sure conversion is invertible'''
        dj_obj = self.converter.toDjangoObj(self.pb, self.ooe)
        pb_obj = self.converter.toProtoMsg(self.pb, dj_obj, proto)
        self.assertEqual(self.ooe, pb_obj)
        
    def test_save_invertible(self):
        '''Make sure conversion is invertible going through database'''
        dj_obj = self.converter.toDjangoObj(self.pb, self.ooe)
        dj_obj.save()
        pb_from_db = self.converter.toProtoMsg(self.pb,
                                          type(dj_obj).objects.get(pk=dj_obj.id),
                                          proto)
        self.ooe.id = dj_obj.id
        self.assertEqual(self.ooe, pb_from_db)
        
class EnumTestCase(unittest.TestCase):
    proto = None
    def setUp(self):
        self.module_name = "enum_test"
        self.pb = ProtocolBuffer(self.module_name)
        self.emsg= genMsg('EnumTest',
                                        models.EnumTest)
        self.pb.addMessage(self.emsg)
        self.django_class_fields = [field for field in 
                               models.EnumTest._meta.local_fields]
        self.pb_field_names = [f.name for f in self.emsg.mapped_fields]
        mod_name = pbandj.genMod(self.pb)
        global proto
        proto = __import__(mod_name)
        emsg = proto.EnumTest()
        emsg.enum_test = proto.EnumTest.ENUM_TEST_VAL1
        self.emsg = emsg
        self.converter = Converter()
        
        enum_db = models.EnumTest(enum_test='Val1')
        enum_db.save()
        self.enum_db = enum_db
        
    def test_toDjangoObj(self):
        dj_obj = self.converter.toDjangoObj(self.pb, self.emsg)
        self.assertEqual(dj_obj.enum_test, self.pb.messages['EnumTest'].enums[0].dj2val[proto.EnumTest.ENUM_TEST_VAL1])
    
    def test_conversion_invertible(self):
        '''Make sure conversion is invertible'''
        dj_obj = self.converter.toDjangoObj(self.pb, self.emsg)
        pb_obj = self.converter.toProtoMsg(self.pb, dj_obj, proto)
        self.assertEqual(self.emsg, pb_obj)
    
    def test_save_invertible(self):
        '''Make sure conversion is invertible going through database'''
        dj_obj = self.converter.toDjangoObj(self.pb, self.emsg)
        dj_obj.save()
        pb_from_db = self.converter.toProtoMsg(self.pb,
                                          type(dj_obj).objects.get(pk=dj_obj.id),
                                          proto)
        self.emsg.id = dj_obj.id
        self.assertEqual(self.emsg, pb_from_db)
        
class ServiceTestCase(unittest.TestCase):
    
    proto = None
    services_started = False
    
    def setUp(self):
        self.pb = ProtocolBuffer("service_test")
        simple_msg = genMsg("Simple", models.Simple)
        self.pb.addMessage(simple_msg)
        self.service_port = 4567
        
        def SimpleHandler(service_impl, controller, request, done):
            request.val += 1
            done.run(request)
        
        def SimpleHandler2(service_impl, controller, request, done):
            '''Docstring from Handler2'''
            request.val += 5
            done.run(request)
            
        self.pb.addRpc('SimpleService', 'TestRpc', simple_msg,
                                   simple_msg, SimpleHandler,
                                   'A line of documentation')
        self.pb.addRpc('SimpleService', 'TestRpc2', simple_msg,
                                   simple_msg, SimpleHandler2)
        self.pb.addRpc('SimpleService2', 'TestRpc', simple_msg,
                                   simple_msg, SimpleHandler)
        mod_name = pbandj.genMod(self.pb)
        global proto
        proto = __import__(mod_name)
        if not ServiceTestCase.services_started:
            self.pb.services['SimpleService'].start(proto, self.service_port, True)
            self.pb.services['SimpleService2'].start(proto, self.service_port + 1, True)
            ServiceTestCase.services_started = True

        
    def test_RpcService(self):
        client = RpcService(proto.SimpleService_Stub, self.service_port,
                            "localhost")
        test_msg = proto.Simple()
        test_msg.val = 1
        response = client.TestRpc(test_msg, timeout=5000)
        self.assertEqual(response.val, test_msg.val + 1,
                         "Rpc test failed")
    
    def test_n_rpc_same_service(self):
        client = RpcService(proto.SimpleService_Stub, self.service_port,
                            "localhost")
        test_msg = proto.Simple()
        test_msg.val = 1
        response = client.TestRpc(test_msg, timeout=5000)
        self.assertEqual(response.val, test_msg.val + 1,
                         "Rpc test failed")
        response = client.TestRpc2(test_msg, timeout=5000)
        self.assertEqual(response.val, test_msg.val + 5,
                         "Rpc test failed")
        
    def test_n_services(self):
        client1 = RpcService(proto.SimpleService_Stub, self.service_port,
                            "localhost")
        client2 = RpcService(proto.SimpleService2_Stub, self.service_port + 1,
                            "localhost")
        test_msg = proto.Simple()
        test_msg.val = 1
        response = client1.TestRpc(test_msg, timeout=5000)
        self.assertEqual(response.val, test_msg.val + 1,
                         "Rpc test failed")
        response = client2.TestRpc(test_msg, timeout=5000)
        self.assertEqual(response.val, test_msg.val + 1,
                         "Rpc test failed")   
        
        
class ForeignKeyTestCase(unittest.TestCase):
    proto = None
    
    def setUp(self):
        self.module_name = "fk_test"
        self.pb = ProtocolBuffer(self.module_name)
        self.fkt = genMsg('ForeignKeyTest',
                                        models.ForeignKeyTest)
        self.pb.addMessage(self.fkt)
        
        self.django_class_fields = [field for field in 
                               models.ForeignKeyTest._meta.local_fields]
        self.pb_fields_by_name = dict([(f.name, f) for f in self.fkt.mapped_fields])
        mod_name = pbandj.genMod(self.pb)
        global proto
        proto = __import__(mod_name)
        self.simple = models.Simple()
        self.simple.val = 1234
        self.simple.save()
        self.con = Converter()
    
    def test_genMsg(self):
        ''' Ensure that there is a type map definition for each Django field
            type
        '''
        for field in self.django_class_fields:
            self.assert_(DJ2PB.get(type(field)) != None,
                         "No protocol buffer type mapped to %s Django type" % 
                         type(field).__name__)
        
    def test_genMsg_fields_exist(self):
        ''' Ensure that all fields from the django type exist in the generated
            protocol buffer type and their type matches the type map
        '''
        for field in self.django_class_fields:
            self.assert_(self.pb_fields_by_name.has_key(field.name),
                         "Django field %s does not exist in protocol buffer message" % field.name)
            pb_field = self.pb_fields_by_name[field.name]
            dj_type = type(field)
            expected_type = [DJ2PB[dj_type]]
            if (dj_type == django_models.ForeignKey or dj_type == django_models.ManyToManyField):
                expected_type.append(ProtocolBuffer.Message)
            self.assert_(type(pb_field.pb_type) in expected_type,
                         "Protocol Buffer field type %s does not match type %s specified in type map for Django type %s" %
                         (type(pb_field.pb_type), DJ2PB[dj_type],
                          dj_type.__name__))
            
    def test_invertible(self):
        test = proto.ForeignKeyTest()
        test.fkey_test_id = self.simple.pk
        dj_test = self.con.toDjangoObj(self.pb, test)
        pb_test = self.con.toProtoMsg(self.pb, dj_test, proto)
        self.assertEqual(test.fkey_test_id, pb_test.fkey_test_id,
                         "Foreign key test objects not equal after conversion")
        
class ForeignKeyRecursionTestCase(unittest.TestCase):
    proto = None
    
    def setUp(self):
        self.module_name = "fk_recusion_test"
        self.pb = ProtocolBuffer(self.module_name)
        self.fkt = genMsg('ForeignKeyTest',
                           models.ForeignKeyTest,
                           recurse_fk = True)
        self.pb.addMessage(self.fkt)
        
        self.django_class_fields = [field for field in 
                               models.ForeignKeyTest._meta.local_fields]
        self.pb_fields_by_name = dict([(f.name, f) for f in self.fkt.mapped_fields])
        mod_name = pbandj.genMod(self.pb)
        global proto
        proto = __import__(mod_name)
        self.simple = models.Simple()
        self.simple.val = 1234
        self.simple.save()
        self.con = Converter()
    
    def test_genMsg(self):
        ''' Ensure that there is a type map definition for each Django field
            type
        '''
        for field in self.django_class_fields:
            self.assert_(DJ2PB.get(type(field)) != None,
                         "No protocol buffer type mapped to %s Django type" % 
                         type(field).__name__)
        
    def test_genMsg_fields_exist(self):
        ''' Ensure that all fields from the django type exist in the generated
            protocol buffer type and their type matches the type map
        '''
        for field in self.django_class_fields:
            self.assert_(self.pb_fields_by_name.has_key(field.name),
                         "Django field %s does not exist in protocol buffer message" % field.name)
            pb_field = self.pb_fields_by_name[field.name]
            dj_type = type(field)
            expected_type = [DJ2PB[dj_type]]
            if (dj_type == django_models.ForeignKey or dj_type == django_models.ManyToManyField):
                expected_type.append(ProtocolBuffer.Message)
            self.assert_(type(pb_field.pb_type) in expected_type,
                         "Protocol Buffer field type %s does not match type %s specified in type map for Django type %s" %
                         (type(pb_field.pb_type), DJ2PB[dj_type],
                          dj_type.__name__))
            
    def test_invertible(self):
        test = proto.ForeignKeyTest()
        test.fkey_test_id = self.simple.pk
        dj_test = self.con.toDjangoObj(self.pb, test)
        pb_test = self.con.toProtoMsg(self.pb, dj_test, proto)
        self.assertEqual(test.fkey_test_id, pb_test.fkey_test_id,
                         "Foreign key test objects not equal after conversion")
        
    def test_save_invertible(self):
        test = proto.ForeignKeyTest()
        self.con.toProtoMsg(self.pb, self.simple, proto, test.fkey_test)
        dj_test = self.con.toDjangoObj(self.pb, test)
        dj_test.save()
        pb_test = self.con.toProtoMsg(self.pb, models.ForeignKeyTest.objects.get(pk=dj_test.pk), proto)
        pb_test.ClearField('id')
        self.assertEqual(test.fkey_test, pb_test.fkey_test,
                         "Foreign key test objects not equal after save")
        
class ManyToManyTestCase(unittest.TestCase):
    
    def setUp(self):
        self.module_name = "m2m_test"
        self.pb = ProtocolBuffer(self.module_name)
        self.m2m = genMsg('ManyToManyTest',
                                        models.ManyToManyTest)
        self.pb.addMessage(self.m2m)
        
        self.django_class_fields = [field for field in 
                               models.ManyToManyTest._meta.local_fields +
                               models.ManyToManyTest._meta.many_to_many]
        self.pb_fields_by_name = dict([(f.name, f) for f in self.m2m.mapped_fields])
        mod_name = pbandj.genMod(self.pb)
        global proto
        proto = __import__(mod_name)
        self.simple1 = models.Simple()
        self.simple1.val = 1234
        self.simple1.save()
        self.simple2 = models.Simple()
        self.simple2.val = 5678
        self.simple2.save()
        self.con = Converter()
        
    def test_genMsg(self):
        ''' Ensure that there is a type map definition for each Django field
            type
        '''
        for field in self.django_class_fields:
            self.assert_(DJ2PB.get(type(field)) != None,
                         "No protocol buffer type mapped to %s Django type" % 
                         type(field).__name__)
    
    def test_genMsg_fields_exist(self):
        ''' Ensure that all fields from the django type exist in the generated
            protocol buffer type and their type matches the type map
        '''
        for field in self.django_class_fields:
            self.assert_(self.pb_fields_by_name.has_key(field.name),
                         "Django field %s does not exist in protocol buffer message" % field.name)
            pb_field = self.pb_fields_by_name[field.name]
            dj_type = type(field)
            expected_type = [DJ2PB[dj_type]]
            if (dj_type == django_models.ForeignKey or dj_type == django_models.ManyToManyField):
                expected_type.append(ProtocolBuffer.Message)
            self.assert_(type(pb_field.pb_type) in expected_type,
                         "Protocol Buffer field type %s does not match type %s specified in type map for Django type %s" %
                         (type(pb_field.pb_type), DJ2PB[dj_type],
                          dj_type.__name__))
    
    def test_toDjangoObj(self):
        pb_test = proto.ManyToManyTest()
        pb_test.test_val = 1
        pb_test.m2m_test_id.append(2)
        dj_test = self.con.toDjangoObj(self.pb, pb_test)
        self.assertEqual(pb_test.test_val, dj_test.test_val,
                         'Django object does not match source Protocol Buffer Message')
    
    def test_toProtoMsg(self):
        dj_test = models.ManyToManyTest()
        dj_test.test_val = 1
        dj_test.save()
        dj_test.m2m_test.add(self.simple1) 
        dj_test.m2m_test.add(self.simple2)       
#        dj_test2 = models.ManyToManyTest()
#        dj_test2.test_val = 2
#        dj_test2.save()
#        dj_test2.m2m_test.add(self.simple) 
        pb_test = self.con.toProtoMsg(self.pb, dj_test, proto)
        self.assert_(len(pb_test.m2m_test_id) == 2,
                     "Added 2 objects to the relation but found %d" % len(pb_test.m2m_test_id))
        self.assertEqual(pb_test.m2m_test_id[0], self.simple1.pk,
                         "1st assoc object doesn't match the original")
        self.assertEqual(pb_test.m2m_test_id[1], self.simple2.pk,
                         "2nd assoc object doesn't match the original")
        
class ManyToManyThrough_Recurse_TestCase(unittest.TestCase):
    
    def setUp(self):
        self.module_name = "m2m_through_test_recurse"
        self.pb = ProtocolBuffer(self.module_name)
        self.m2m = genMsg('ManyToManyThroughTest',
                                        models.ManyToManyThroughTest, recurse_fk=True)
        self.pb.addMessage(self.m2m)
        
        self.django_class_fields = [field for field in 
                               models.ManyToManyThroughTest._meta.local_fields +
                               models.ManyToManyThroughTest._meta.many_to_many]
        
        self.django_assoc_class_fields = [field for field in 
                               models.M2MAssocTest._meta.local_fields +
                               models.M2MAssocTest._meta.many_to_many]
        
        self.pb_fields_by_name = dict([(f.name, f) for f in self.m2m.mapped_fields])
        self.pb_assoc_fields_by_name = dict([(f.name, f) for f in self.pb_fields_by_name['m2m_test'].pb_type.mapped_fields])
        mod_name = pbandj.genMod(self.pb)
        global proto
        proto = __import__(mod_name)
        self.simple = models.Simple()
        self.simple.val = 1234
        self.simple.save()
        self.con = Converter()
        
    def test_genMsg(self):
        ''' Ensure that there is a type map definition for each Django field
            type
        '''
        for field in self.django_class_fields:
            self.assert_(DJ2PB.get(type(field)) != None,
                         "No protocol buffer type mapped to %s Django type" % 
                         type(field).__name__)
    
    def test_genMsg_fields_exist(self):
        ''' Ensure that all fields from the django type exist in the generated
            protocol buffer type and their type matches the type map
        '''
        for field in self.django_class_fields:
            self.assert_(self.pb_fields_by_name.has_key(field.name),
                         "Django field %s does not exist in protocol buffer message" % field.name)
            pb_field = self.pb_fields_by_name[field.name]
            dj_type = type(field)
            expected_type = [DJ2PB[dj_type]]
            if (dj_type == django_models.ForeignKey or dj_type == django_models.ManyToManyField):
                expected_type.append(ProtocolBuffer.Message)
            self.assert_(type(pb_field.pb_type) in expected_type,
                         "Protocol Buffer field type %s does not match type %s specified in type map for Django type %s" %
                         (type(pb_field.pb_type), DJ2PB[dj_type],
                          dj_type.__name__))
    
    def test_genMsg_through_fields_exist(self):
        for field in self.django_assoc_class_fields:
            self.assert_(self.pb_assoc_fields_by_name.has_key(field.name),
                         "Django field %s does not exist in protocol buffer message for through relation" % field.name)
            pb_field = self.pb_assoc_fields_by_name[field.name]
            dj_type = type(field)
            expected_type = [DJ2PB[dj_type]]
            if dj_type == django_models.ForeignKey or dj_type == django_models.ManyToManyField:
                expected_type.append(ProtocolBuffer.Message)
            self.assert_(type(pb_field.pb_type) in expected_type,
                         "Protocol Buffer field type %s does not match type %s specified in type map for Django type %s" %
                         (type(pb_field.pb_type), DJ2PB[dj_type],
                          dj_type.__name__))
            if dj_type == django_models.ForeignKey and field.name == 'm2m_fk':
                self.assert_(pb_field.pb_type != self.m2m,
                         "Assoc class field creates a circular relationship")
            if dj_type == django_models.ForeignKey and field.name == 'simple_fk':
                self.assert_(isinstance(pb_field.pb_type, ProtocolBuffer.Message),
                         "recurse_fk was True but genMsg failed to recurse into fk type")
            
    def test_toProtoMsg(self):
        dj_test = models.ManyToManyThroughTest()
        dj_test.test_val = 1
        dj_test.save()
        assoc_test = models.M2MAssocTest()
        assoc_test.assoc_test = 1
        assoc_test.simple_fk = self.simple
        assoc_test.m2m_fk = dj_test
        assoc_test.save()
        assoc_test2 = models.M2MAssocTest()
        assoc_test2.assoc_test = 2
        assoc_test2.simple_fk = self.simple
        assoc_test2.m2m_fk = dj_test
        assoc_test2.save()
        pb_test = self.con.toProtoMsg(self.pb, dj_test, proto)
        self.assert_(len(pb_test.m2m_test) == 2,
                     "Added 2 objects to the relation but found %d" % len(pb_test.m2m_test))
        self.assertEqual(pb_test.m2m_test[0],
                         self.con.toProtoMsg(self.pb, assoc_test, proto),
                         "Conversion of 1st assoc object doesn't match stand alone conversion of the same object")
        self.assertEqual(pb_test.m2m_test[1],
                         self.con.toProtoMsg(self.pb, assoc_test2, proto),
                         "Conversion of 2nd assoc object doesn't match stand alone conversion of the same object")
    

class ManyToManyThrough_NoRecurse_TestCase(unittest.TestCase):
    
    def setUp(self):
        self.module_name = "m2m_through_test_no_recurse"
        self.pb = ProtocolBuffer(self.module_name)
        self.m2m = genMsg('ManyToManyThroughTest',
                                        models.ManyToManyThroughTest, recurse_fk=False)
        self.pb.addMessage(self.m2m)
        
        self.django_class_fields = [field for field in 
                               models.ManyToManyThroughTest._meta.local_fields +
                               models.ManyToManyThroughTest._meta.many_to_many]
        
        self.django_assoc_class_fields = [field for field in 
                               models.M2MAssocTest._meta.local_fields +
                               models.M2MAssocTest._meta.many_to_many]
        
        self.pb_fields_by_name = dict([(f.name, f) for f in self.m2m.mapped_fields])
        self.pb_assoc_fields_by_name = dict([(f.name, f) for f in self.pb_fields_by_name['m2m_test'].pb_type.mapped_fields])
        mod_name = pbandj.genMod(self.pb)
        global proto
        proto = __import__(mod_name)
        self.simple = models.Simple()
        self.simple.val = 1234
        self.simple.save()
        self.con = Converter()
        
    def test_genMsg(self):
        ''' Ensure that there is a type map definition for each Django field
            type
        '''
        for field in self.django_class_fields:
            self.assert_(DJ2PB.get(type(field)) != None,
                         "No protocol buffer type mapped to %s Django type" % 
                         type(field).__name__)
        for field in self.django_assoc_class_fields:
            self.assert_(DJ2PB.get(type(field)) != None,
                         "No protocol buffer type mapped to %s Django type" % 
                         type(field).__name__)
    
    def test_genMsg_fields_exist(self):
        ''' Ensure that all fields from the django type exist in the generated
            protocol buffer type and their type matches the type map
        '''
        for field in self.django_class_fields:
            self.assert_(self.pb_fields_by_name.has_key(field.name),
                         "Django field %s does not exist in protocol buffer message" % field.name)
            pb_field = self.pb_fields_by_name[field.name]
            dj_type = type(field)
            expected_type = [DJ2PB[dj_type]]
            if (dj_type == django_models.ForeignKey or dj_type == django_models.ManyToManyField):
                expected_type.append(ProtocolBuffer.Message)
            self.assert_(type(pb_field.pb_type) in expected_type,
                         "Protocol Buffer field type %s does not match type %s specified in type map for Django type %s" %
                         (type(pb_field.pb_type), DJ2PB[dj_type],
                          dj_type.__name__))

    
    def test_genMsg_through_fields_exist(self):
        for field in self.django_assoc_class_fields:
            self.assert_(self.pb_assoc_fields_by_name.has_key(field.name),
                         "Django field %s does not exist in protocol buffer message for through relation" % field.name)
            pb_field = self.pb_assoc_fields_by_name[field.name]
            dj_type = type(field)
            expected_type = [DJ2PB[dj_type]]
            if dj_type == django_models.ForeignKey or dj_type == django_models.ManyToManyField:
                expected_type.append(ProtocolBuffer.Message)
            self.assert_(type(pb_field.pb_type) in expected_type,
                         "Protocol Buffer field type %s does not match type %s specified in type map for Django type %s" %
                         (type(pb_field.pb_type), DJ2PB[dj_type],
                          dj_type.__name__))
            if dj_type == django_models.ForeignKey and field.name == 'm2m_fk':
                self.assert_(pb_field.pb_type != self.m2m,
                         "Assoc class field creates a circular relationship")
            if dj_type == django_models.ForeignKey and field.name == 'simple_fk':
                self.assert_(not isinstance(pb_field.pb_type, ProtocolBuffer.Message),
                         "Recursive relationship found when recurse_fk was False")
            
    def test_toProtoMsg(self):
        dj_test = models.ManyToManyThroughTest()
        dj_test.test_val = 1
        dj_test.save()
        assoc_test = models.M2MAssocTest()
        assoc_test.assoc_test = 1
        assoc_test.simple_fk = self.simple
        assoc_test.m2m_fk = dj_test
        assoc_test.save()
        assoc_test2 = models.M2MAssocTest()
        assoc_test2.assoc_test = 2
        assoc_test2.simple_fk = self.simple
        assoc_test2.m2m_fk = dj_test
        assoc_test2.save()
        pb_test = self.con.toProtoMsg(self.pb, dj_test, proto)
        self.assert_(len(pb_test.m2m_test) == 2,
                     "Added 2 objects to the relation but found %d" % len(pb_test.m2m_test))
        self.assertEqual(pb_test.m2m_test[0],
                         self.con.toProtoMsg(self.pb, assoc_test, proto),
                         "Conversion of 1st assoc object doesn't match stand alone conversion of the same object")
        self.assertEqual(pb_test.m2m_test[1],
                         self.con.toProtoMsg(self.pb, assoc_test2, proto),
                         "Conversion of 2nd assoc object doesn't match stand alone conversion of the same object")
            
    
             
class GenModTestCase(unittest.TestCase):
    
    def setup(self):
        pass
    
if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(OneOfEverythingTestCase))
    suite.addTest(unittest.makeSuite(MessageRenameTestCase))
    suite.addTest(unittest.makeSuite(EnumTestCase))
    suite.addTest(unittest.makeSuite(OneOfEverythingUsageTestCase))
    suite.addTest(unittest.makeSuite(ServiceTestCase))
    suite.addTest(unittest.makeSuite(ForeignKeyTestCase))
    suite.addTest(unittest.makeSuite(ForeignKeyRecursionTestCase))
    suite.addTest(unittest.makeSuite(ManyToManyTestCase))
    suite.addTest(unittest.makeSuite(ManyToManyThrough_Recurse_TestCase))
    suite.addTest(unittest.makeSuite(ManyToManyThrough_NoRecurse_TestCase))
    unittest.TextTestRunner(verbosity=0).run(suite)
                
        
        
    
