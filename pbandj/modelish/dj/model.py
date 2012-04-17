from django.db import models as dj_models

from field import create_field



def find_recursion(dj_model, max_depth=3):
    """Decend relational references defined in the model fields and look for 
    recursive relationships.
    
    Args:
    max_depth - (int) Maximum number of levels to decend before aborting search
    """
    # Local fields
    fields = [field for field in 
                            dj_model._meta.local_fields +
                            dj_model._meta.many_to_many]
    
    if max_depth <= 0:
        return fields
    
    results = []
    for field in fields:
        field_recursion = None        
        if isinstance(field, dj_models.ForeignKey):
            field_recursion = find_recursion(field, max_depth - 1)
        elif isinstance(field. dj_models.ManyToManyField):
            if (not field.rel.through is None and
                len(field.rel.through._meta.fields) > 3):
                # There is data associated with the relation
                # Generate a Model instance from assoc model excluding fk reference
                # back to the parent type to prevent circular references
                field_recursion = find_recursion(field.rel_through, max_depth - 1)
            else:
                field_recursion = find_recursion(m2m_dj_field, max_depth -1)
        if field_recursion:
            results.append(field_recursion)
    return results

class Model(object):
    """Class mapping to a django model
    """

    @staticmethod
    def from_django_model(dj_model, **kwargs):
        """Create a model instance from a supplied django model
        """
        """ Create a protocol buffer message from a django type.
            By default all args will be included in the new message.
            If recurse_fk is set messages will also be created for foreign key
            types.  A list of generated messages will be returned.
            Accepted Args:
            msg_name -- (String) The name of the message
            dj_model -- (Type) A reference to the django
                                  model type
            include - (List) A list of field names from the model to
                      be included in the mapping
            exclude - (List) A list of field names to exclude from the
                      model.  Only used if included arg is []
            recurse_fk -- Flag for recursing into foreign key fields if true or 
                       using pk if false
            no-recurse - List of field names which should not be recursed.
                          Only used if recurse_fk=True
        """
        
        # Local fields
        django_class_fields = [field for field in 
                               dj_model._meta.local_fields +
                               dj_model._meta.many_to_many]
        django_field_by_name = {}
        
        # Iterate through Django fields and init dict that allows
        # lookup of fields by name.
        for field in django_class_fields:
            django_field_by_name[field.name] = field
        
        field_set = set()
        
        # Remove excluded fields or add included fields
        include = kwargs.get(include, [])
        exclude = kwargs.get(exclude, [])
        if include != []: 
            # Assert that the fields all exist
            include_set = set(include)
            assert include_set == set(django_field_by_name.keys()) & include_set
            field_set = include_set
        else:
            useable_field_names = set(django_field_by_name.keys()) - set(exclude)
            field_set = useable_field_names
        
        # Instantiate pbandj model
        model = Model()
        
        # Add a field for each remaining django field in the set
        for field_name in field_set:
            field = django_field_by_name[field_name]
            model.fields.append(create_field(field, **kwargs))
            
        return model
        
    
    def __init__(self):
        self.fields = [] 