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
'''django_test.test_app.models.py - Django model used for unittesting
pbandj

Authors: Zach Walker (zwalker@lcogt.net)
Dec 2009
'''

from django.db import models
from pbandj.decorator import protocol_buffer_message, add_field
from pbandj.modelish.pb import field

# Used for testing descorators from unit tests
#class UnmappedModel(models.Model):
#    int_test = models.IntegerField()
#    char_test = models.CharField()

#@protocol_buffer_message(field_num_map={('file_test', 'TYPE_STRING') : 1980})
@add_field('optional', 'zanotherfield', 'int32')
@add_field('optional', 'zfield', 'string')
@protocol_buffer_message
class OneOfEverything(models.Model):
    bool_test = models.BooleanField()
    char_test = models.CharField(max_length=10)
    comma_test = models.CommaSeparatedIntegerField(max_length=10)
    date_test = models.DateField()
    date_time_test = models.DateTimeField()
    decimal_test = models.DecimalField(decimal_places=2, max_digits=4)
    email_test = models.EmailField()
    file_test = models.FileField(upload_to='.')
    file_path_test = models.FilePathField()
    float_test = models.FloatField()
    image_test = models.ImageField(upload_to='.')
    int_test = models.IntegerField()
    ip_test = models.IPAddressField()
    null_bool_test = models.NullBooleanField()
    pos_int_test = models.PositiveIntegerField()
    pos_sm_int_test = models.PositiveSmallIntegerField()
    slug_test = models.SlugField()
    sm_int_test = models.SmallIntegerField()
    text_test = models.TextField()
    time_test = models.TimeField()
    url_test = models.URLField()
#    xml_test = models.XMLField()


@protocol_buffer_message
class Simple(models.Model):
    val = models.IntegerField()


@protocol_buffer_message
class EnumTest(models.Model):
    test_enum_choices = (('Val1', 'Long Name Val 1'),
                         ('Val2', 'Long Name Val 2'))
    enum_test = models.CharField(max_length = 20, choices=test_enum_choices)


@protocol_buffer_message
class ForeignKeyTest(models.Model):
    fkey_test = models.ForeignKey(Simple)


@protocol_buffer_message
class ManyToManyTest(models.Model):
    test_val = models.IntegerField()
    m2m_test = models.ManyToManyField(Simple)


@protocol_buffer_message
class ManyToManyThroughTest(models.Model):
    test_val = models.IntegerField()
    m2m_test = models.ManyToManyField(Simple, through='M2MAssocTest')

@protocol_buffer_message    
class M2MAssocTest(models.Model):
    assoc_test = models.IntegerField()
    simple_fk = models.ForeignKey(Simple)
    m2m_fk = models.ForeignKey(ManyToManyThroughTest)

# Test self referential foreign key reecursion
@protocol_buffer_message
class ForeignKeyRecursionTest(models.Model):
    fkey_test = models.ForeignKey('ForeignKeyRecursionTest')
    
# Test recursion in Through models
@protocol_buffer_message
class ManyToManyThroughRecursionTest(models.Model):
    test_val = models.IntegerField()
    m2m_test = models.ManyToManyField(Simple, through='M2MAssocRecursionTest')


@protocol_buffer_message    
class M2MAssocRecursionTest(models.Model):
    assoc_test = models.IntegerField()
    simple_fk = models.ForeignKey(Simple)
    m2m_fk = models.ForeignKey(ManyToManyThroughRecursionTest)
    
# Convoluted recursion test
@protocol_buffer_message
class ConvolutedRecursionTest(models.Model):
    test_val = models.IntegerField()
    m2m_test = models.ManyToManyField(Simple, through='ConvolutedM2MAssocRecursionTest')

# Test self referential foreign key reecursion
@protocol_buffer_message
class ConvolutedForeignKeyTest(models.Model):
    fkey_test = models.ForeignKey(ConvolutedRecursionTest)
    fkey_test2 = models.ForeignKey('ConvolutedForeignKeyTest')

@protocol_buffer_message    
class ConvolutedM2MAssocRecursionTest(models.Model):
    assoc_test = models.IntegerField()
    simple_fk = models.ForeignKey(Simple)
    m2m_fk = models.ForeignKey(ConvolutedRecursionTest)
    m2m_assoc_fk = models.ForeignKey(ConvolutedForeignKeyTest)