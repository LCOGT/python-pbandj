from django.db import models as dj_models

def create_field(dj_field, **kwargs):
    """Factory method for creating Field instance based on Django type
    
    Args:
    dj_field - (django field) - a django model field instance
    """
    if isinstance(dj_field, dj_models.ForeignKey):
        return ForeignKey.from_dj_field(dj_field, **kwargs)
    elif isinstance(dj_field, dj_models.ManyToManyField):
        return ManyToMany.from_dj_field(dj_field, **kwargs)
    else:
        return Field.from_dj_field(dj_field, **kwargs)
        


class Field(object):
    
    def __init__(self, name, dj_type):
        self.name = name
        self.dj_type = dj_type
        self.choices = None
    
    @staticmethod    
    def from_dj_field(dj_field, **kwargs):
        field = Field(dj_field.name, type(dj_field))
                        # Add an enumeration for each django field with choices set
        if(dj_field.choices):
            self.choices = field.choices
        return field
        

class ForeignKey(Field):
    
    def __init__(self, name, dj_type):
        Field.__init__(self, name, dj_type)
    
    @staticmethod    
    def from_dj_field(dj_field, recurse_fk=True, no_recurse=[], **kwargs):      
        if isinstance(dj_field, models.ForeignKey):
            # By default leave type as a ForeignKey
            field = ForeignKey(dj_field.name, type(dj_field))
        else:
            raise PbandjFieldException("Supplied field is not a ForeignKey")
            
            # If foreign key recrusion is active.  Dive in
            if recurse_fk and not dj_field.name in no_recurse:
                # Create a new msg type from the parent table in the fk relation
                fk_dj_field = dj_field.rel.to
                if isinstance(fk_dj_field, str):
                    # TODO: Handle ForeignKey supplied as a str
                    raise NotImplemented('Unable to handle Django ForeignKey fields declared with a string passed for related model')
                    #fk_dj_model = models.__dict__[fk_dj_model]
                    
                fk_dj_model = Model.from_django_model(fk_dj_field)
                field.dj_type = fk_dj_model
        return field
    
    
class ManyToMany(Field):
    
    def __init__(self, name, dj_type):
        Field.__init__(self, name, dj_type)
        self.through = None
        
    @staticmethod
    def from_dj_field(dj_field, recurse_fk=True, no_recurse=[], **kwargs):
        if isinstance(dj_field, models.ManyToManyField):
            # By default leave type as a ManyToMany
            field = ManyToMany(dj_field.name, type(dj_field))
        else:
            raise PbandjFieldException("Supplied field is not a ManyToManyField")
        
        # If there is a 'through' model, capture it.
        # If there are only 3 fields than there is only an id and a fk to each
        # side of the relation so this is probably not a user defined assoc class
        if (not field.rel.through is None and
            len(field.rel.through._meta.fields) > 3):
            # There is data associated with the relation
            # Generate a Model instance from assoc model excluding fk reference
            # back to the parent type to prevent circular references
            self.through = Model.from_django_model(field.rel_through)
            
            # Find recursive fields
            m2m_dj_model = field.rel.through
            recur_rel_fields = [] # Fields which would cause a recursive relation
            for assoc_field in m2m_dj_model._meta._fields():
                if (isinstance(assoc_field, models.ForeignKey) and
                    assoc_field.rel.to == django_model_class):
                    recur_rel_fields.append(assoc_field.name)
                    
        # Just like a foreign key but repeated
        if recurse_fk and not dj_field.name in no_recurse:
            # Create a new msg type from the parent table in the fk relation
            m2m_dj_field = dj_field.rel.to
            if isinstance(m2m_dj_field, str):
                # TODO: Handle ManyToManyField supplied as a str
                raise NotImplemented('Unable to handle Django ManyToManyField declared with a string passed for related model')
                #fk_dj_model = models.__dict__[fk_dj_model]
            m2m_dj_model = Model.from_django_model(m2m_dj_field)
            field.dj_type = m2m_dj_model
            
        return field            