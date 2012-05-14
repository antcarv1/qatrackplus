import csv
import StringIO
from qatrack.formats.en.formats import DATETIME_FORMAT
import django.utils.dateformat as dateformat
import tastypie
from tastypie.resources import Resource, ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.utils import timezone
import qatrack.qa.models as models
from qatrack.units.models import Unit,Modality, UnitType
from tastypie.serializers import Serializer

def csv_date(dt):
    return dateformat.format(timezone.make_naive(dt),DATETIME_FORMAT)

class ValueResourceCSVSerializer(Serializer):

    formats = ['json', 'jsonp', 'csv']
    content_types = {
        'json': 'application/json',
        'jsonp': 'text/javascript',
        'csv': 'text/csv',
    }
    columns = [
        ("Dates","dates",),
        ("Values","values",),
        ("Act Low","tolerances","act_low"),
        ("Tol Low","tolerances","tol_low"),
        ("Reference","references",),
        ("Tol High","tolerances","tol_high"),
        ("Act High","tolerances","act_high"),
        ("Tol Type","tolerances","type"),
        ("Comment","comment",),
        ("Username","user","username"),
    ]

    #----------------------------------------------------------------------
    def instances_to_csv(self,instances):
        rows = [[x[0] for x in self.columns]]
        for i in instances:
            tol_type = ""
            al, tl, th, ah = "","","",""
            if i.tolerance:
                al, tl = i.tolerance.act_low,i.tolerance.tol_low
                ah, th = i.tolerance.act_high,i.tolerance.tol_high
                tol_type = i.tolerance.type
            r = ""
            if i.reference:
                r = i.reference.value

            rows.append([csv_date(i.work_completed),i.value,al,tl,r,th,ah,tol_type,i.comment,i.created_by.username])

        return rows
    #----------------------------------------------------------------------
    def to_csv(self, data, options=None):
        options = options or {}

        csv_data = StringIO.StringIO()
        writer = csv.writer(csv_data)

        for item in data["objects"]:
            headers  = ["Unit:","Unit%02d" %item.data["unit"],"Test:",item.data["name"]]
            column = [headers] + self.instances_to_csv(item.obj["data"])
            writer.writerows(column)

        return csv_data.getvalue()

#============================================================================
class ModalityResource(ModelResource):
    class Meta:
        queryset = Modality.objects.order_by("type").all()

#============================================================================
class UnitTypeResource(ModelResource):
    class Meta:
        queryset = UnitType.objects.order_by("name").all()

#============================================================================
class UnitResource(ModelResource):
    modalities = tastypie.fields.ToManyField("qatrack.qa.api.ModalityResource","modalities",full=True)
    type = tastypie.fields.ToOneField("qatrack.qa.api.UnitTypeResource","type",full=True)

    class Meta:
        queryset = Unit.objects.order_by("number").all()
        filtering = {
            "number": ALL_WITH_RELATIONS,
            "name":ALL,
        }

#============================================================================
class ReferenceResource(ModelResource):
    class Meta:
        queryset = models.Reference.objects.all()

#============================================================================
class ToleranceResource(ModelResource):
    class Meta:
        queryset = models.Tolerance.objects.all()


#============================================================================
class CategoryResource(ModelResource):
    class Meta:
        queryset = models.Category.objects.all()

#============================================================================
class TaskListResource(ModelResource):
    task_list_items = tastypie.fields.ToManyField("qatrack.qa.api.TaskListItemResource","task_list_items",full=True)
    frequencies = tastypie.fields.ListField()

    class Meta:
        queryset = models.TaskList.objects.order_by("name").all()
        filtering = {
            "pk":ALL,
            "slug":ALL,
            "name":ALL,
        }
    #----------------------------------------------------------------------
    def dehydrate_frequencies(self,bundle):
        return list(bundle.obj.unittasklists_set.values_list("frequency",flat=True).distinct())

#============================================================================
class TaskListItemInstanceResource(ModelResource):
    task_list_item = tastypie.fields.ForeignKey("qatrack.qa.api.TaskListItemResource","task_list_item", full=True)
    reference = tastypie.fields.ForeignKey("qatrack.qa.api.ReferenceResource","reference", full=True,null=True)
    tolerance = tastypie.fields.ForeignKey("qatrack.qa.api.ToleranceResource","tolerance", full=True,null=True)
    unit = tastypie.fields.ForeignKey(UnitResource,"unit",full=True);

    class Meta:
        queryset = models.TaskListItemInstance.objects.all()
        resource_name = "values"
        allowed_methods = ["get","patch","put"]
        always_return_data = True
        filtering = {
            'task_list_item':ALL_WITH_RELATIONS,
            'work_completed':ALL,
            'id':ALL,
        }
        ordering= ["work_completed"]
        authentication = BasicAuthentication()
        authorization = DjangoAuthorization()

    #----------------------------------------------------------------------
    def build_filters(self,filters=None):
        """allow filtering by unit"""
        if filters is None:
            filters = {}

        orm_filters = super(TaskListItemInstanceResource,self).build_filters(filters)

        if "units" in filters:
            orm_filters["unit__number__in"] = filters["units"].split(',')

        if "from_date" in filters:
            try:
                orm_filters["work_completed__gte"] = timezone.datetime.datetime.strptime(filters["from_date"],"%d-%m-%Y")
            except ValueError:
                pass
        if "to_date" in filters:
            try:
                orm_filters["work_completed__lte"] = timezone.datetime.datetime.strptime(filters["to_date"],"%d-%m-%Y")
            except ValueError:
                pass

        if "review_status" in filters:
            orm_filters["status__in"] = filters["review_status"].split(',')

        if "short_names" in filters:
            orm_filters["task_list_item__short_name__in"] = [x.strip() for x in filters["short_names"].split(',')]
        #elif "task_list_item_id" in filters:
        #    orm_filters["task_list_item__pk"] = filters["pk"]
        return orm_filters

    #----------------------------------------------------------------------
    def is_authorized(self,request,obj=None):
        auth =super(TaskListItemInstanceResource,self).is_authorized(request,obj)
        return auth


#----------------------------------------------------------------------
def serialize_tasklistiteminstance(task_list_item_instance):
    """return a dictionary of task_list_item_instance properties"""
    tlii = task_list_item_instance
    info = {
        'value':tlii.value,
        'date':tlii.work_completed.isoformat(),
        'save_date':tlii.created.isoformat(),
        'comment':tlii.comment,
        'status':tlii.status,
        'reference':None,
        'tolerance': {'type':None,'act_low':None,'tol_low':None,'tol_high':None,'act_high':None,},
        'user':None,
        'unit':None,
        'task_list_item':None,
    }
    if tlii.reference:
        info["reference"] = tlii.reference.value

    if tlii.tolerance:
        info['tolerance'] = {
            'type':tlii.tolerance.type,
            'act_low':tlii.tolerance.act_low,
            'tol_low':tlii.tolerance.tol_low,
            'tol_high':tlii.tolerance.tol_high,
            'act_high':tlii.tolerance.act_high,
        }

    if tlii.task_list_item:
        info["task_list_item"] = tlii.task_list_item.short_name

    if tlii.unit:
        info["unit"] = tlii.unit.number

    if tlii.created_by:
        info["user"] = tlii.created_by.username

    if tlii.task_list_item:
        info["task_list_item"] = tlii.task_list_item.short_name

    return info

#============================================================================
class FrequencyResource(Resource):
    """available tasklistitem frequencies"""
    value = tastypie.fields.CharField()
    display = tastypie.fields.CharField()
    class Meta:
        allowed_methods = ["get"]
    #----------------------------------------------------------------------
    def dehydrate_value(self,bundle):
        return bundle.obj["value"]
    #----------------------------------------------------------------------
    def dehydrate_display(self,bundle):
        return bundle.obj["display"]
    #----------------------------------------------------------------------
    def get_object_list(self):
        return [{"value":x[0],"display":x[1]} for x in models.FREQUENCY_CHOICES]
    #----------------------------------------------------------------------
    def obj_get_list(self,request=None,**kwargs):
        return self.get_object_list()

#============================================================================
class StatusResource(Resource):
    """avaialable task list item statuses"""
    value = tastypie.fields.CharField()
    display = tastypie.fields.CharField()
    class Meta:
        allowed_methods = ["get"]
    #----------------------------------------------------------------------
    def dehydrate_value(self,bundle):
        return bundle.obj["value"]
    #----------------------------------------------------------------------
    def dehydrate_display(self,bundle):
        return bundle.obj["display"]
    #----------------------------------------------------------------------
    def get_object_list(self):
        return [{"value":x[0],"display":x[1]} for x in models.STATUS_CHOICES]
    #----------------------------------------------------------------------
    def obj_get_list(self,request=None,**kwargs):
        return self.get_object_list()


#============================================================================
class ValueResource(Resource):
    unit = tastypie.fields.IntegerField()
    name = tastypie.fields.CharField()
    short_name = tastypie.fields.CharField()
    data = tastypie.fields.DictField()

    #============================================================================
    class Meta:
        serializer = ValueResourceCSVSerializer()
        resource_name = "grouped_values"
        allowed_methods = ["get"]
    #----------------------------------------------------------------------
    def dehydrate_short_name(self,bundle):
        return bundle.obj["short_name"]
    #----------------------------------------------------------------------
    def dehydrate_name(self,bundle):
        return bundle.obj["name"]
    #----------------------------------------------------------------------
    def dehydrate_unit(self,bundle):
        return bundle.obj["unit"]
    #----------------------------------------------------------------------
    def dehydrate_data(self,bundle):
        """"""
        data = {
            'values':[],
            'references':[],

            'tolerances':[],
            'comments':[],
            'dates':[],
            'users':[]
        }
        for task_list_item_instance in bundle.obj["data"]:
            instance = serialize_tasklistiteminstance(task_list_item_instance)
            for prop in ('value','reference','date','user'):
                data[prop+'s'].append(instance.get(prop,None))
            data["tolerances"].append(instance["tolerance"])


        return data
    #----------------------------------------------------------------------
    def get_object_list(self,request):
        """return organized values"""
        objects = TaskListItemInstanceResource().obj_get_list(request)
        names = objects.order_by("task_list_item__name").values_list("task_list_item__short_name","task_list_item__name").distinct()
        units = objects.order_by("unit__number").values_list("unit__number",flat=True).distinct()
        self.dispatch
        organized = []
        for short_name,name in names:
            for unit in units:
                data = objects.filter(
                        task_list_item__short_name=short_name,
                        unit__number = unit,
                ).order_by("work_completed")

                organized.append({
                    'short_name':short_name,
                    'name':name,
                    'unit':unit,
                    'data':data,
                })
        return organized
    #----------------------------------------------------------------------
    def obj_get_list(self,request=None,**kwargs):
        return self.get_object_list(request)


#============================================================================
class TaskListItemResource(ModelResource):
    #values = tastypie.fields.ToManyField(TaskListItemInstanceResource,"tasklistiteminstance_set")
    category = tastypie.fields.ToOneField(CategoryResource,"category",full=True)
    class Meta:
        queryset = models.TaskListItem.objects.all()
        filtering = {
            "short_name": ALL,
            "id":ALL
        }
    #    excludes = ["values"]

    #----------------------------------------------------------------------
    def build_filters(self,filters=None):
        """allow filtering by unit"""
        if filters is None:
            filters = {}

        orm_filters = super(TaskListItemResource,self).build_filters(filters)

        if "unit" in filters:
            orm_filters["task_list_instance__task_list__unit__number"] = filters["unit"]
        return orm_filters

#============================================================================
class TaskListInstanceResource(ModelResource):
    unit = tastypie.fields.ForeignKey(UnitResource,"unit",full=True)
    task_list = tastypie.fields.ForeignKey(TaskListResource,"task_list",full=True)
    item_instances = tastypie.fields.ToManyField(TaskListItemInstanceResource,"tasklistiteminstance_set",full=True)
    review_status = tastypie.fields.ListField()

    class Meta:
        queryset = models.TaskListInstance.objects.all()
        filtering = {
            "unit":ALL_WITH_RELATIONS,
            "task_list": ALL_WITH_RELATIONS
        }

        ordering= ["work_completed"]

    #----------------------------------------------------------------------
    def dehydrate_review_status(self,bundle):
        reviewed = bundle.obj.tasklistiteminstance_set.exclude(status=models.UNREVIEWED).count()
        total = bundle.obj.tasklistiteminstance_set.count()
        if total == reviewed:
            #ugly
            item = bundle.obj.tasklistiteminstance_set.latest()
            review = (item.modified_by,item.modified)
        else:
            review = ()
        return review