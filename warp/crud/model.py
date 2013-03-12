from storm.locals import *

try:
    import json
except ImportError:
    import simplejson as json

from warp.crud import colproxy, columns
from warp import helpers


class CrudModel(object):

    editRenderers = {
        Int: colproxy.IntProxy,
        Unicode: colproxy.StringProxy,
        DateTime: colproxy.DateTimeProxy,
        Date: colproxy.DateProxy,
        Bool: colproxy.BooleanProxy,
        Reference: colproxy.ReferenceProxy,
        ReferenceSet: colproxy.ReferenceSetProxy,
        RawStr: colproxy.RawStringProxy,
        Float: colproxy.FloatProxy,
        Enum: colproxy.StormEnumProxy,

        # Warp column subclasses
        columns.NonEmptyUnicode: colproxy.NonEmptyStringProxy,
        columns.Text: colproxy.AreaProxy,
        columns.HTML: colproxy.HTMLAreaProxy,
        columns.Image: colproxy.ImageProxy,
        columns.Price: colproxy.PriceProxy,
        columns.UTCDateTime: colproxy.DateTimeProxy,
    }

    listAttrs = {}

    listTitles = None
    crudTitles = None

    showListLink = True
    allowCreate = True
    hideListActions = False

    gridAttrs = {
        'rowNum': "10",
        'rowList': "[10,20,30]",
        'sortname': "'id'",
        'sortorder': "'asc'",
        'viewrecords': "true",
    }

    extraFacets = ()
    noEdits = {
        # "created": ALREADY_SET("created", "Changing creation timestamp is wrong"),
        # "name": ALREADY_SET("id", "Name can only be set on creation"),
    }

    def __init__(self, obj):
        self.obj = obj


    def name(self, request):
        return self.obj.id


    def parentCrumb(self, request):
        parent = self.parent(request)
        if parent is not None:
            return helpers.getCrudObj(parent)


    def parent(self, request):
        return None

    def linkAsParent(self, request):
        return helpers.link(self.name(request),
                            helpers.getCrudNode(self),
                            "view",
                            [self.obj.id])


    def saveRedirect(self, request):
        return helpers.url(request.node, 'view', request.resource.args)

    def getProxy(self, colName, request):
        funcName = "render_proxy_%s" % colName
        if hasattr(self, funcName):
            return getattr(self, funcName)(request)
        return self.defaultProxy(colName)


    def defaultProxy(self, colName):
        val = getattr(self.obj, colName)
        # Avoid triggering the property __get__
        valType = self.obj.__class__.__dict__[colName].__class__
        return self.editRenderers[valType](self.obj, colName)


    def renderListView(self, colName, request):
        funcName = "render_list_%s" % colName
        if hasattr(self, funcName):
            return getattr(self, funcName)(request)
        return self.getProxy(colName, request).render_view(request)


    def renderView(self, colName, request):
        funcName = "render_%s" % colName
        if hasattr(self, funcName):
            return getattr(self, funcName)(request)
        return self.getProxy(colName, request).render_view(request)


    def renderEdit(self, colName, request):
        when = self.noEdits.get(colName)
        if when and when(self):
            return self.renderView(colName, request)

        funcName = "render_edit_%s" % colName
        if hasattr(self, funcName):
            return getattr(self, funcName)(request)
        return self.getProxy(colName, request).render_edit(request)


    def save(self, colName, val, request):
        when = self.noEdits.get(colName)
        if when:
            error = when(self)
            if error:
                return error

        funcName = "save_%s" % colName
        if hasattr(self, funcName):
            return getattr(self, funcName)(val, request)
        return self.getProxy(colName, request).save(val, request)


    @classmethod
    def listConditions(cls, model, request):
        conditions = []
        whereJSON = request.args.get('where', [None])[0]
        if whereJSON is not None:
            where = json.loads(whereJSON)
            for (k, v) in where.iteritems():
                conditions.append(getattr(model, k) == v)
        return conditions





def ALWAYS(self):
    return "Not editable"


def ALREADY_SET(colName, message):
    def when(self):
        if getattr(self.obj, colName, None) is None:
            return None
        else:
            return message
    return when


def noEdit(colNames, when = ALWAYS):
    def decorate(crudClass):
        crudClass.noEdits = crudClass.noEdits.copy()
        for colName in colNames:
            crudClass.noEdits[colName] = when
        return crudClass
    return decorate
