"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from datetime import datetime

from django.db import models
from django.test import TestCase

from pbandj.modelish import types
from pbandj.modelish import mapper
from pbandj.modelish import pb
from pbandj.modelish import dj
from pbandj.modelish.types import PB_TYPE_DOUBLE
from pbandj import decorator
from pbandj import util
from pbandj.conversion import Converter

import pbandj_test.models as test_models

@decorator.protocol_buffer_message
class MessageTestModel(models.Model):
    int_test = models.IntegerField()
    char_test = models.CharField(max_length=10)
        
@decorator.protocol_buffer_message(msg_name="RenamedMessage")        
class MessageRenameTestModel(models.Model):
    int_test = models.IntegerField()
    char_test = models.CharField(max_length=10)

test_field_num_map = {
                      pb.field.Field(pb.field.OPTIONAL, 'char_test', types.DJ2PB.get(models.CharField), 1).field_key : 1,
                      pb.field.Field(pb.field.OPTIONAL, 'does_not_exist', types.DJ2PB.get(models.CharField), 2).field_key : 2,
                      pb.field.Field(pb.field.OPTIONAL, 'field_with_high_num', types.DJ2PB.get(models.IntegerField), 77).field_key : 77,
                      }
    
@decorator.protocol_buffer_message(pb_field_num_map=test_field_num_map)        
class FieldNumberMapTestModel(models.Model):
    int_test = models.IntegerField()
    char_test = models.CharField(max_length=10)
    field_with_high_num = models.IntegerField()
        
        
class MessageDecoratorTest(TestCase):
    
    def test_has_PBANDJ(self):
        """Make sure mode has been tagged as a PBANDJ model
        """
        self.assertTrue(hasattr(MessageTestModel, '__PBANDJ'))
        
    def test_has_generate_protocol_buffer(self):
        """Test that the generate_protocol_buffer method has been added
        by the decorator
        """
        self.assertTrue(hasattr(MessageTestModel, 'generate_protocol_buffer'))
        
    def test_generate_protocol_buffer_django_model(self):
        """Test that the original django model the decorator was applied to
        is referenced from the created model
        """
        mapped_model = MessageTestModel.generate_protocol_buffer()
        self.assertIsInstance(mapped_model, mapper.MappedModel)
        self.assertEqual(MessageTestModel, mapped_model.dj_model)
        
    def test_generate_protocol_buffer_django_fields(self):
        """Test that a mapping exists in the generated protocol buffer
        model for each field in the decorated django model
        """
        mapped_model = MessageTestModel.generate_protocol_buffer()
        self.assertIn('int_test', mapped_model.pb_to_dj_field_map.keys())
        self.assertIsInstance(mapped_model.pb_to_dj_field_map['int_test'], tuple)
        self.assertIsInstance(mapped_model.pb_to_dj_field_map['int_test'][0], dj.field.Field)
        self.assertIsInstance(mapped_model.pb_to_dj_field_map['int_test'][1], pb.field.Field)
        
        self.assertIn('char_test', mapped_model.pb_to_dj_field_map.keys())
        self.assertIsInstance(mapped_model.pb_to_dj_field_map['char_test'], tuple)
        self.assertIsInstance(mapped_model.pb_to_dj_field_map['char_test'][0], dj.field.Field)
        self.assertIsInstance(mapped_model.pb_to_dj_field_map['char_test'][1], pb.field.Field)

    def test_generate_protocol_buffer_renamed_message(self):
        """Test that the message renaming feature of the decorator works
        """
        mapped_model = MessageRenameTestModel.generate_protocol_buffer()
        self.assertEquals('RenamedMessage', mapped_model.pbandj_pb_msg.name)
        
    def test_generate_protocol_buffer_with_field_number_map(self):
        """Test that given a field number map, field in the map exist and
        are number appropriatly in the generated protocol buffer model
        """
        mapped_model = FieldNumberMapTestModel.generate_protocol_buffer()
        self.assertIn('int_test', mapped_model.pb_to_dj_field_map.keys())
        self.assertIsInstance(mapped_model.pb_to_dj_field_map['int_test'], tuple)
        self.assertIsInstance(mapped_model.pb_to_dj_field_map['int_test'][0], dj.field.Field)
        self.assertIsInstance(mapped_model.pb_to_dj_field_map['int_test'][1], pb.field.Field)
#        self.assertNotEquals(mapped_model.pb_to_dj_field_map['int_test'][1].field_num, 1)
        
        self.assertIn('char_test', mapped_model.pb_to_dj_field_map.keys())
        self.assertIsInstance(mapped_model.pb_to_dj_field_map['char_test'], tuple)
        self.assertIsInstance(mapped_model.pb_to_dj_field_map['char_test'][0], dj.field.Field)
        self.assertIsInstance(mapped_model.pb_to_dj_field_map['char_test'][1], pb.field.Field)
#        self.assertEquals(mapped_model.pb_to_dj_field_map['char_test'][1].field_num, 1)
        
        self.assertIn('field_with_high_num', mapped_model.pb_to_dj_field_map.keys())
        self.assertIsInstance(mapped_model.pb_to_dj_field_map['field_with_high_num'], tuple)
        self.assertIsInstance(mapped_model.pb_to_dj_field_map['field_with_high_num'][0], dj.field.Field)
        self.assertIsInstance(mapped_model.pb_to_dj_field_map['field_with_high_num'][1], pb.field.Field)
        self.assertEquals(mapped_model.pb_to_dj_field_map['field_with_high_num'][1].field_num, 77)
        print mapped_model.pbandj_pb_msg
        
    #TODO: Add field numbering test from a pb2 module


@decorator.add_field('OPTIONAL', 'added_field',  PB_TYPE_DOUBLE)
@decorator.protocol_buffer_message  
class MessageWithAddedField(models.Model):
    int_test = models.IntegerField()
    char_test = models.CharField(max_length=10)
    
                
@decorator.add_field('OPTIONAL', 'added_field',  PB_TYPE_DOUBLE, 77)
@decorator.protocol_buffer_message  
class MessageWithAddedFieldAndFieldNumArg(models.Model):
    int_test = models.IntegerField()
    char_test = models.CharField(max_length=10) 
    
      
class AddFieldDecoratorTest(TestCase):
    
    def test_add_field_field_exists(self):
        mapped_model = MessageWithAddedField.generate_protocol_buffer()
        unmapped_field_names = [field.name for field in mapped_model.unmapped_fields]
        self.assertIn('added_field', unmapped_field_names)
        
    def test_add_field_with_field_num_arg(self):
        mapped_model = MessageWithAddedFieldAndFieldNumArg.generate_protocol_buffer()
        unmapped_fields_by_name = dict([(field.name, field) for field in mapped_model.unmapped_fields])
        self.assertIn('added_field', unmapped_fields_by_name.keys())
        self.assertEqual(77, unmapped_fields_by_name.get('added_field').field_num)


@decorator.protocol_buffer_message
class ServiceDecoratorTestModel(models.Model):
    int_test = models.IntegerField()
    char_test = models.CharField(max_length=10) 
    
service_decorator_mapped_model = ServiceDecoratorTestModel.generate_protocol_buffer()    
@decorator.service('ServiceDecoratorTestService', 'TestMethod', service_decorator_mapped_model.pbandj_pb_msg, service_decorator_mapped_model.pbandj_pb_msg)
def service_test_method(input):
    return input

class ServiceDecoratorTest(TestCase):
    
    def test_handler_has_meta(self):
        self.assertTrue(hasattr(service_test_method, '_pbandj'))
    
    def test_service_registry_has_service(self):
        self.assertIn("ServiceDecoratorTestService", decorator.service_registry.service_names())
        
    def test_registered_service_has_method(self):
        service_handlers = decorator.service_registry.methods_by_service_name("ServiceDecoratorTestService")
        self.assertNotEqual(service_handlers, [])
        self.assertIn(service_test_method, service_handlers)
#        self.assertIn('TestMethod', [s.method_name for s in service_handlers])

    def test_method_input_type(self):
        self.assertEqual(service_decorator_mapped_model.pbandj_pb_msg, service_test_method._pbandj.input)
        
    def test_method_output_type(self):
        self.assertEqual(service_decorator_mapped_model.pbandj_pb_msg, service_test_method._pbandj.output)
        
    
    
class TestDjangoFieldConversion(TestCase):
    """Tests to check that each django field type can be converted to a
    protocol buffer message field
    """
    
    mapped_module = None
    converter = None
    
    @classmethod
    def setUpClass(cls):
        cls.mapped_module = mapper.MappedModule('TestDjangoFieldConversion')
        cls.mapped_module.add_mapped_model(test_models.OneOfEverything.generate_protocol_buffer())
        cls.converter = Converter(cls.mapped_module)
        
    def setUp(self):
        self.django_ooe = test_models.OneOfEverything()
    
    def test_bool_conversion(self):
        self.django_ooe.bool_test = True
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(True, proto_ooe.bool_test)
        self.assertEqual(True, self.converter.pbtodj(proto_ooe).bool_test)
        
        self.django_ooe.bool_test = False
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(False, proto_ooe.bool_test)
        self.assertEqual(False, self.converter.pbtodj(proto_ooe).bool_test)
        
    def test_char_conversion(self):
        self.django_ooe.char_test = ''
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual('', proto_ooe.char_test)
        self.assertEqual('', self.converter.pbtodj(proto_ooe).char_test)
        
        self.django_ooe.char_test = 'abc123'
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual('abc123', proto_ooe.char_test)
        self.assertEqual('abc123', self.converter.pbtodj(proto_ooe).char_test)
    
    def test_comma_conversion(self):
        self.django_ooe.comma_test = '1,2,3'
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual('1,2,3', proto_ooe.comma_test)
        self.assertEqual('1,2,3', self.converter.pbtodj(proto_ooe).comma_test)
        
    def test_date_conversion(self):
        self.django_ooe.date_test = datetime(1980, 6, 10).date()
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual('1980-06-10', proto_ooe.date_test)
        self.assertEqual(datetime(1980, 6, 10).date(), self.converter.pbtodj(proto_ooe).date_test)
        
    def test_date_time_conversion(self):
        self.django_ooe.date_time_test = datetime(1980, 6, 10, 14, 30, 0, 999999)
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual('1980-06-10 14:30:00.999999', proto_ooe.date_time_test)
        self.assertEqual(datetime(1980, 6, 10, 14, 30, 0, 999999), self.converter.pbtodj(proto_ooe).date_time_test)
        
    def test_time_conversion(self):
        self.django_ooe.time_test = datetime(1980, 6, 10, 14, 30, 0, 999999).time()
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual('14:30:00.999999', proto_ooe.time_test)
        self.assertEqual(datetime(1980, 6, 10, 14, 30, 0, 999999).time(), self.converter.pbtodj(proto_ooe).time_test)
        
    def test_decimal_conversion(self):
        self.django_ooe.decimal_test = 0.0
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(0, proto_ooe.decimal_test)
        self.assertEqual(0, self.converter.pbtodj(proto_ooe).decimal_test)
        
        self.django_ooe.decimal_test = -1.2345
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(-1.2345, proto_ooe.decimal_test)
        self.assertEqual(-1.2345, self.converter.pbtodj(proto_ooe).decimal_test)
        
        self.django_ooe.decimal_test = 1.2345
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(1.2345, proto_ooe.decimal_test)
        self.assertEqual(1.2345, self.converter.pbtodj(proto_ooe).decimal_test)
        
    def test_float_conversion(self):
        self.django_ooe.float_test = 0.0
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(0, proto_ooe.float_test)
        self.assertEqual(0, self.converter.pbtodj(proto_ooe).float_test)
        
        self.django_ooe.float_test = -1.2345
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(-1.2345, proto_ooe.float_test)
        self.assertEqual(-1.2345, self.converter.pbtodj(proto_ooe).float_test)
        
        self.django_ooe.float_test = 1.2345
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(1.2345, proto_ooe.float_test)
        self.assertEqual(1.2345, self.converter.pbtodj(proto_ooe).float_test)
    
    def test_email_conversion(self):
        self.django_ooe.email_test = 'zwalker@lcogt.net'
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual('zwalker@lcogt.net', proto_ooe.email_test)
        self.assertEqual('zwalker@lcogt.net', self.converter.pbtodj(proto_ooe).email_test)
        
    def test_file_conversion(self):
        self.django_ooe.file_test = '/random/path/tofile.ext'
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual('/random/path/tofile.ext', proto_ooe.file_test)
        self.assertEqual('/random/path/tofile.ext', self.converter.pbtodj(proto_ooe).file_test)
        
    def test_image_conversion(self):
        self.django_ooe.image_test = '/random/path/to/image.jpg'
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual('/random/path/to/image.jpg', proto_ooe.image_test)
        self.assertEqual('/random/path/to/image.jpg', self.converter.pbtodj(proto_ooe).image_test)
        
    def test_int_conversion(self):
        self.django_ooe.int_test = 0
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(0, proto_ooe.int_test)
        self.assertEqual(0, self.converter.pbtodj(proto_ooe).int_test)
        
        self.django_ooe.int_test = -1
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(-1, proto_ooe.int_test)
        self.assertEqual(-1, self.converter.pbtodj(proto_ooe).int_test)
        
        self.django_ooe.int_test = 1
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(1, proto_ooe.int_test)
        self.assertEqual(1, self.converter.pbtodj(proto_ooe).int_test)
        
    def test_ip_conversion(self):
        self.django_ooe.ip_test = '1.2.3.4'
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual('1.2.3.4', proto_ooe.ip_test)
        self.assertEqual('1.2.3.4', self.converter.pbtodj(proto_ooe).ip_test)
        
    def test_null_bool_conversion(self):
#        self.django_ooe.null_bool_test = None
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(False, proto_ooe.null_bool_test)
        self.assertEqual(None, self.converter.pbtodj(proto_ooe).null_bool_test)
        
        self.django_ooe.null_bool_test = True
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(True, proto_ooe.null_bool_test)
        self.assertEqual(True, self.converter.pbtodj(proto_ooe).null_bool_test)
        
        self.django_ooe.null_bool_test = False
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(False, proto_ooe.null_bool_test)
        self.assertEqual(False, self.converter.pbtodj(proto_ooe).null_bool_test)
    
    def test_pos_int_conversion(self):
        self.django_ooe.pos_int_test = 0
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(0, proto_ooe.pos_int_test)
        self.assertEqual(0, self.converter.pbtodj(proto_ooe).pos_int_test)
        
#        self.assertRaises('ValueError', self.converter.djtopb(self.django_ooe))
        
        self.django_ooe.pos_int_test = 1
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(1, proto_ooe.pos_int_test)
        self.assertEqual(1, self.converter.pbtodj(proto_ooe).pos_int_test)
    
    def test_pos_sm_int_conversion(self):
        self.django_ooe.pos_sm_int_test = 0
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(0, proto_ooe.pos_sm_int_test)
        self.assertEqual(0, self.converter.pbtodj(proto_ooe).pos_sm_int_test)
        
#        self.django_ooe.pos_sm_int_test = -1
#        proto_ooe = self.converter.djtopb(self.django_ooe)
#        self.assertEqual(-1, proto_ooe.pos_sm_int_test)
#        self.assertEqual(-1, self.converter.pbtodj(proto_ooe).pos_sm_int_test)
        
        self.django_ooe.pos_sm_int_test = 1
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(1, proto_ooe.pos_sm_int_test)
        self.assertEqual(1, self.converter.pbtodj(proto_ooe).pos_sm_int_test)
    
    def test_slug_conversion(self):
        self.django_ooe.slug_test = ''
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual('', proto_ooe.slug_test)
        self.assertEqual('', self.converter.pbtodj(proto_ooe).slug_test)
        
        self.django_ooe.slug_test = 'Whats a slug?'
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual('Whats a slug?', proto_ooe.slug_test)
        self.assertEqual('Whats a slug?', self.converter.pbtodj(proto_ooe).slug_test)
    
    def test_sm_int_conversion(self):
        self.django_ooe.sm_int_test = 0
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(0, proto_ooe.sm_int_test)
        self.assertEqual(0, self.converter.pbtodj(proto_ooe).sm_int_test)
        
        self.django_ooe.sm_int_test = -1
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(-1, proto_ooe.sm_int_test)
        self.assertEqual(-1, self.converter.pbtodj(proto_ooe).sm_int_test)
        
        self.django_ooe.sm_int_test = 1
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual(1, proto_ooe.sm_int_test)
        self.assertEqual(1, self.converter.pbtodj(proto_ooe).sm_int_test)
    
    def test_text_conversion(self):
        self.django_ooe.text_test = ''
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual('', proto_ooe.text_test)
        self.assertEqual('', self.converter.pbtodj(proto_ooe).text_test)
        
        self.django_ooe.text_test = 'abc123'
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual('abc123', proto_ooe.text_test)
        self.assertEqual('abc123', self.converter.pbtodj(proto_ooe).text_test)
    
    def test_url_conversion(self):
        self.django_ooe.url_test = 'http://lcogt.net'
        proto_ooe = self.converter.djtopb(self.django_ooe)
        self.assertEqual('http://lcogt.net', proto_ooe.url_test)
        self.assertEqual('http://lcogt.net', self.converter.pbtodj(proto_ooe).url_test)
    
#    def test_xml_conversion(self):
#        self.django_ooe.xml_test = '<abc>123</abc>'
#        proto_ooe = self.converter.djtopb(self.django_ooe)
#        self.assertEqual('<abc>123</abc>', proto_ooe.xml_test)
#        self.assertEqual('<abc>123</abc>', self.converter.pbtodj(proto_ooe).xml_test)
        
    
        