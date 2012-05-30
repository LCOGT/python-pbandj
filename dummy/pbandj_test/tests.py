"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.db import models
from django.test import TestCase

from pbandj.modelish import types
from pbandj.modelish import mapper
from pbandj.modelish import pb
from pbandj.modelish import dj
from pbandj.modelish.types import PB_TYPE_DOUBLE
from pbandj import decorator


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
        
    #TODO: Add field numbering test when a modle already exists
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
              