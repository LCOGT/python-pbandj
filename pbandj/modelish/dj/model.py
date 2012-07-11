from django.db import models as dj_models

import field


def find_circular_relationships(dj_model, max_depth=3, visited_models=None):
    """Decend relational references defined in the model fields and look for 
    circular relationships.  Any relationship over max_depth deep will be 
    treated as circular.
    
    Args:
    max_depth - (int) Maximum number of levels to decend before aborting search
    """
    # Initialize accumulator
    if not visited_models:
        visited_models = []
    
    # See if this model has already been visited on recursion check
    if dj_model in visited_models:
        return dj_model
    else: 
        visited_models.append(dj_model)
        
    # Create list of all fields in model
    fields = [field for field in 
                            dj_model._meta.local_fields +
                            dj_model._meta.many_to_many]
    
    recursion_path = []
    for field in fields:
        if max_depth <= 0:
            recursion_path.append((field, None))
        else:
            next_dj_model = None        
            if isinstance(field, dj_models.ForeignKey):
                next_dj_model = field.rel.to
            elif isinstance(field, dj_models.ManyToManyField):
                if (not field.rel.through is None and
                    len(field.rel.through._meta.fields) > 3):
                    # There is data associated with the relation
                    # Generate a Model instance from assoc model excluding fk reference
                    # back to the parent type to prevent circular references
                    next_dj_model = field.rel.through
                else:
                    next_dj_model = field.rel.to   
            if next_dj_model:
                circles = find_circular_relationships(next_dj_model, max_depth - 1, visited_models)
                if circles:
                    recursion_path.append((field, circles))
#                recursion_path.append((field, next_dj_model))
    return recursion_path


def create_field(dj_field, **kwargs):
    """Factory method for creating Field instance based on Django type
    
    Args:
    dj_field - (django field) - a django model field instance
    """
    if isinstance(dj_field, dj_models.OneToOneField):
        return field.OneToOne.from_dj_field(dj_field, **kwargs)
    elif isinstance(dj_field, dj_models.ForeignKey):
        return field.ForeignKey.from_dj_field(dj_field, **kwargs)
    elif isinstance(dj_field, dj_models.ManyToManyField):
        return field.ManyToMany.from_dj_field(dj_field, **kwargs)
    else:
        return field.Field.from_dj_field(dj_field, **kwargs)


class Model(object):
    """Class mapping to a django model
    """

    @staticmethod
    def from_django_model(dj_model, no_follow_fields=None, no_follow_models={}, **kwargs):
        """Create a model instance from a supplied django model
        """
        """ Create a protocol buffer message from a django type.
            By default all args will be included in the new message.
            If follow_related is set messages will also be created for foreign key
            types.  A list of generated messages will be returned.
            Accepted Args:
            msg_name - (str) The name of the message
            dj_model - (Type) A reference to the django
                                  model type
            include - (List) A list of field names from the model to
                      be included in the mapping
            exclude - (List) A list of field names to exclude from the
                      model.  Only used if included arg is []
            follow_related - (bool)Follow into relation fields if true or 
                       using pk if false
            no_follow_fields - (List) Field names which should not be followed.
                          Only used if follow_related=True
            no_follow_models - (List) Django models not to follow as relations
        """
        # Check for existing pbandj dj model.  If not found create one
        model = no_follow_models.get(dj_model, None)
        if model:
            return model
        else:
            model = no_follow_models.setdefault(dj_model, Model(dj_model._meta.object_name))
        
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
        include = kwargs.get('include', [])
        exclude = kwargs.get('exclude', [])
        if include != []: 
            # Assert that the fields all exist
            include_set = set(include)
            assert include_set == set(django_field_by_name.keys()) & include_set
            field_set = include_set
        else:
            useable_field_names = set(django_field_by_name.keys()) - set(exclude)
            field_set = useable_field_names
        
        # Add a field for each remaining django field in the set
        for field_name in field_set:
            field = django_field_by_name[field_name]
            model.fields.append(create_field(field, no_follow_models=no_follow_models, **kwargs))
       
        # Add a reverse field for reverse relationships
        related_field_list = dj_model._meta.get_all_related_objects() + dj_model._meta.get_all_related_many_to_many_objects()
        for related_field in related_field_list:
            model.related_fields.append(create_field(related_field.field, no_follow_models=no_follow_models, **kwargs))
            
        return model
        
    
    def __init__(self, name=None, fields=None, related_fields=None):
        self.name = name
        self.fields = fields if fields else []
        self.related_fields = related_fields if related_fields else []
             