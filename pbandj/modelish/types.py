from django.db import  models


def _make_type(name, ptype, pnum):
    return type(name, (), {'name': name,
                           'ptype': ptype,
                           'pnum' : pnum,
                           '__eq__': lambda x,y: isinstance(y, x.__class__) and x.ptype == y.ptype,
                           '__ne__': lambda x,y: not x.__eq__(y)})


PB_TYPE_DOUBLE   = _make_type('TYPE_DOUBLE'  ,'double'  , 1)
PB_TYPE_FLOAT    = _make_type('TYPE_FLOAT'   ,'float'   , 2)
PB_TYPE_INT64    = _make_type('TYPE_INT64'   ,'int64'   , 3)
PB_TYPE_UINT64   = _make_type('TYPE_UINT64'  ,'uint64'  , 4)
PB_TYPE_INT32    = _make_type('TYPE_INT32'   ,'int32'   , 5)
PB_TYPE_FIXED64  = _make_type('TYPE_FIXED64' ,'fixed64' , 6)
PB_TYPE_FIXED32  = _make_type('TYPE_FIXED32' ,'fixed32' , 7)
PB_TYPE_BOOL     = _make_type('TYPE_BOOL'    ,'bool'    , 8)
PB_TYPE_STRING   = _make_type('TYPE_STRING'  ,'string'  , 9)
PB_TYPE_GROUP    = _make_type('TYPE_GROUP'   ,'group'   ,10)
PB_TYPE_MESSAGE  = _make_type('TYPE_MESSAGE' ,'message' ,11)
PB_TYPE_BYTES    = _make_type('TYPE_BYTES'   ,'bytes'   ,12)
PB_TYPE_UINT32   = _make_type('TYPE_UINT32'  ,'uint32'  ,13)
PB_TYPE_ENUM     = _make_type('TYPE_ENUM'    ,'enum'    ,14)
PB_TYPE_SFIXED32 = _make_type('TYPE_SFIXED32','sfixed32',15)
PB_TYPE_SFIXED64 = _make_type('TYPE_SFIXED64','sfixed64',16)
PB_TYPE_SINT32   = _make_type('TYPE_SINT32'  ,'sint32'  ,17)
PB_TYPE_SINT64   = _make_type('TYPE_SINT64'  ,'sint64'  ,18)


DJ2PB = {models.CharField: PB_TYPE_STRING,
         models.DecimalField: PB_TYPE_DOUBLE,
         models.IntegerField: PB_TYPE_INT32,
         models.FloatField: PB_TYPE_FLOAT,
         models.DateTimeField: PB_TYPE_STRING,
         models.DateField: PB_TYPE_STRING,
         models.BooleanField: PB_TYPE_BOOL,
         models.NullBooleanField: PB_TYPE_BOOL,
         models.CommaSeparatedIntegerField: PB_TYPE_STRING,
         models.EmailField : PB_TYPE_STRING,
         models.FileField: PB_TYPE_STRING,
         models.FilePathField:  PB_TYPE_STRING,
         models.ImageField: PB_TYPE_STRING,
         models.IPAddressField: PB_TYPE_STRING,
         models.PositiveIntegerField: PB_TYPE_UINT32,
         models.PositiveSmallIntegerField: PB_TYPE_UINT32,
         models.SlugField: PB_TYPE_STRING,
         models.SmallIntegerField: PB_TYPE_INT32,
         models.TextField: PB_TYPE_STRING,
         models.TimeField: PB_TYPE_STRING,
         models.URLField: PB_TYPE_STRING,
         #models.XMLField: PB_TYPE_STRING,
         models.AutoField: PB_TYPE_INT32,
         models.ForeignKey: PB_TYPE_INT32,
         # TODO: Add a ManyToManyField mapping
         models.ManyToManyField: PB_TYPE_INT32 
         }


PB2DJ = dict([(DJ2PB[key], key) for key in DJ2PB])