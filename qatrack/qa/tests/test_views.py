from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import setup_test_environment
from django.utils import unittest,timezone
from qatrack.qa import models,views,forms
from qatrack import settings

import django.forms
import json
import os
import random
import utils

#====================================================================================
class TestURLS(TestCase):
    """just test urls to make sure at the very least they are valid and return 200"""

    #---------------------------------------------------------------------------
    def setUp(self):
        u = utils.create_user()
        self.client.login(username="user",password="password")
        g = utils.create_group()
        u.groups.add(g)
        u.save()
    #---------------------------------------------------------------------------
    def returns_200(self,url,method="get"):
        return getattr(self.client,method)(url).status_code == 200

    def test_qa_urls(self):

        utils.create_status()
        u1 = utils.create_unit(number=1,name="u1")
        utils.create_unit(number=2,name="u2",)
        utc = utils.create_unit_test_collection(unit=u1)
        tli = utils.create_test_list_instance(unit_test_collection=utc)

        url_names = (
            ("home",{}),

            ("all_lists",{}),

            ("charts",{}),
            ("export_data",{}),
            ("chart_data",{}),
            ("control_chart",{}),
            ("review_all",{}),
            ("review_utc",{"pk":"1"}),
            ("choose_review_frequency",{}),
            ("review_by_frequency",{"frequency":"short-interval"}),
            ("review_by_frequency",{"frequency":"daily/monthly"}),
            ("choose_review_unit",{}),
            ("review_by_unit",{"unit_number":"1"}),
            ("review_by_unit",{"unit_number":"1/2"}),

            ("complete_instances",{}),

            ("review_test_list_instance",{"pk":"1"}),

            ("unreviewed",{}),

            ("in_progress",{}),

            ("edit_tli",{"pk":"1"}),
            ("choose_unit",{}),
            ("perform_qa",{"pk":"1"}),
            ("qa_by_frequency_unit",{"unit_number":"1","frequency":"short-interval"}),
            ("qa_by_unit",{"unit_number":"1"}),
            ("qa_by_frequency_unit",{"unit_number":"1","frequency":"short-interval"}),
            ("qa_by_unit_frequency",{"unit_number":"1","frequency":"short-interval"}),
            ("qa_by_frequency",{"frequency":"short-interval"}),
        )

        for url,kwargs in url_names:
            self.assertTrue(self.returns_200(reverse(url,kwargs=kwargs)))
    #---------------------------------------------------------------------------
    def test_login(self):
        self.assertTrue(self.returns_200(settings.LOGIN_URL))
    #---------------------------------------------------------------------------
    def test_login_redirect(self):
        self.assertTrue(self.returns_200(settings.LOGIN_REDIRECT_URL))
    #----------------------------------------------------------------------
    def test_composite(self):
        url = reverse("composite")

        self.assertTrue(self.returns_200(url,method="post"))
    #--------------------------------------------------------------------------
    def test_perform(self):
        utils.create_status()
        utils.create_unit_test_collection()
        url = reverse("perform_qa",kwargs={"pk":"1"})
        self.assertTrue(self.returns_200(url))
        url = reverse("perform_qa",kwargs={"pk":"2"})

        self.assertTrue(404==self.client.get(url).status_code)



#============================================================================
class TestControlChartImage(TestCase):

    #----------------------------------------------------------------------
    def setUp(self):
        self.factory = RequestFactory()
        self.old_cc_available = views.CONTROL_CHART_AVAILABLE

        self.view = views.ControlChartImage.as_view()
        self.url = reverse("control_chart")
    #----------------------------------------------------------------------
    def tearDown(self):
        views.CONTROL_CHART_AVAILABLE = self.old_cc_available

    #----------------------------------------------------------------------
    def test_cc_not_available(self):
        views.CONTROL_CHART_AVAILABLE = False
        from django.http import Http404
        request = self.factory.get(self.url)
        self.assertRaises(Http404,self.view,request)

    #----------------------------------------------------------------------
    def test_not_enough_data(self):
        request = self.factory.get(self.url)
        response =  self.view(request)

        self.assertTrue(response.get("content-type"),"image/png")
    #----------------------------------------------------------------------
    def test_baseline_subgroups(self):
        for n in [-1,0,1,2,"nonnumber"]:
            request = self.factory.get(self.url+"?n_base_subgroups=%s"%n)
            response =  self.view(request)
            self.assertTrue(response.get("content-type"),"image/png")
    #----------------------------------------------------------------------
    def test_baseline_subgroups(self):
        for n in [-1,0,1,2,200,"nonnumber"]:
            request = self.factory.get(self.url+"?subgroup_size=%s"%n)
            response =  self.view(request)
            self.assertTrue(response.get("content-type"),"image/png")
    #----------------------------------------------------------------------
    def test_include_fit(self):
        for f in ["true","false"]:
            request = self.factory.get(self.url+"?fit_data=%s"%f)
            response =  self.view(request)
            self.assertTrue(response.get("content-type"),"image/png")
    #----------------------------------------------------------------------
    def make_url(self,slug,unumber,from_date,to_date,sg_size=2,n_base=2,fit="true"):
        url = self.url+"?subgroup_size=%s&n_baseline_subgroups=%s&fit_data=%s" %(sg_size,n_base,fit)
        url+= "&slug=%s"%slug
        url+= "&unit=%s"%unumber
        url+= "&from_date=%s"%from_date.strftime(settings.SIMPLE_DATE_FORMAT)
        url+= "&to_date=%s"%to_date.strftime(settings.SIMPLE_DATE_FORMAT)
        return url
    #----------------------------------------------------------------------
    def test_valid(self):
        test = utils.create_test()
        unit = utils.create_unit()
        uti = utils.create_unit_test_info(test=test,unit=unit)

        status = utils.create_status()
        yesterday = timezone.datetime.today()-timezone.timedelta(days=1)
        yesterday = timezone.make_aware(yesterday,timezone.get_current_timezone())
        tomorrow = yesterday+timezone.timedelta(days=2)

        url = self.make_url(test.slug,unit.number,yesterday,yesterday)

        request = self.factory.get(url)
        response =  self.view(request)
        self.assertTrue(response.get("content-type"),"image/png")

        url = self.make_url(test.slug,unit.number,yesterday,tomorrow)

        for n in (1,1,8,90):
            for x in range(n):
                utils.create_test_instance(
                    unit_test_info=uti,
                    value=random.gauss(1,0.5),
                    status=status
                )


            request = self.factory.get(url)
            response =  self.view(request)
            self.assertTrue(response.get("content-type"),"image/png")

    #----------------------------------------------------------------------
    def test_invalid(self):
        test = utils.create_test()
        unit = utils.create_unit()
        uti = utils.create_unit_test_info(test=test,unit=unit)

        status = utils.create_status()
        yesterday = timezone.datetime.today()-timezone.timedelta(days=1)
        yesterday = timezone.make_aware(yesterday,timezone.get_current_timezone())
        tomorrow = yesterday+timezone.timedelta(days=2)

        url = self.make_url(test.slug,unit.number,yesterday,yesterday)
        request = self.factory.get(url)
        response =  self.view(request)
        self.assertTrue(response.get("content-type"),"image/png")

        url = self.make_url(test.slug,unit.number,yesterday,tomorrow,fit="true")


        #generate some data that the control chart fit function won't be able to fit
        for x in range(10):
            utils.create_test_instance(
                value=x,
                status=status,
                unit_test_info=uti
            )

        request = self.factory.get(url)
        response =  self.view(request)
        self.assertTrue(response.get("content-type"),"image/png")

#============================================================================
class TestComposite(TestCase):
    #----------------------------------------------------------------------
    def setUp(self):
        self.factory = RequestFactory()
        self.view = views.CompositeCalculation.as_view()
        self.url = reverse("composite")

        self.t1 = utils.create_test(name="test1")
        self.t2 = utils.create_test(name="test2")
        self.tc = utils.create_test(name="testc",test_type=models.COMPOSITE)
        self.tc.calculation_procedure = "result = test1 + test2"
        self.tc.save()

    #----------------------------------------------------------------------
    def test_composite(self):

        data =  {
            u'qavalues': [
                u'{"testc":{"name":"testc","current_value":""},"test1":{"name":"test1","current_value":1},"test2":{"name":"test2","current_value":2}}'
            ],
            u'composite_ids': [u'{"testc":"3"}']
        }


        request = self.factory.post(self.url,data=data)
        response = self.view(request)
        values = json.loads(response.content)
        expected = {
            "errors": [],
            "results": {
                "testc": {
                    "value": 3.0,
                    "error": None
                }
            },
            "success": True
        }
        self.assertDictEqual(values,expected)
    #----------------------------------------------------------------------
    def test_invalid_values(self):

        data =  {u'composite_ids': [u'{"testc":"3"}']}

        request = self.factory.post(self.url,data=data)
        response = self.view(request)
        values = json.loads(response.content)

        expected = {
            "errors": ['Invalid QA Values'],
            "success": False
        }
        self.assertDictEqual(values,expected)
    #----------------------------------------------------------------------
    def test_no_composite(self):

        data =  {
            u'qavalues': [
                u'{"testc":{"name":"testc","current_value":""},"test1":{"name":"test1","current_value":1},"test2":{"name":"test2","current_value":2}}'
            ],
        }

        request = self.factory.post(self.url,data=data)
        response = self.view(request)
        values = json.loads(response.content)

        expected = {
            "errors": ["No Valid Composite ID's"],
            "success": False
        }
        self.assertDictEqual(values,expected)

    #----------------------------------------------------------------------
    def test_invalid_json(self):

        data =  {
            u'qavalues': ['{"testc"'],
        }

        request = self.factory.post(self.url,data=data)
        response = self.view(request)
        values = json.loads(response.content)

        self.assertEqual(values["success"],False)
    #----------------------------------------------------------------------
    def test_invalid_test(self):

        self.tc.calculation_procedure = "foo"
        self.tc.save()

        data =  {
            u'qavalues': [
                u'{"testc":{"name":"testc","current_value":""},"test1":{"name":"test1","current_value":1},"test2":{"name":"test2","current_value":2}}'
            ],
            u'composite_ids': [u'{"testc":"3"}']
        }

        request = self.factory.post(self.url,data=data)
        response = self.view(request)
        values = json.loads(response.content)
        expected = {
            "errors": [],
            "results": {
                "testc": {
                    "value": None,
                    "error": "Invalid Test",
                }
            },
            "success": True
        }
        self.assertDictEqual(values,expected)


#============================================================================
class TestPerformQA(TestCase):

    #----------------------------------------------------------------------
    def setUp(self):
        self.factory = RequestFactory()
        self.view = views.PerformQA.as_view()
        self.status = utils.create_status()

        self.test_list = utils.create_test_list()

        self.t_simple = utils.create_test(name="test_simple")

        self.t_const = utils.create_test(name="test_const",test_type=models.CONSTANT)
        self.t_const.constant_value = 1
        self.t_const.save()

        self.t_comp = utils.create_test(name="test_comp",test_type=models.COMPOSITE)
        self.t_comp.calculation_procedure = "result = test_simple + test_const"
        self.t_comp.save()

        self.t_mult = utils.create_test(name="test_mult",test_type=models.MULTIPLE_CHOICE)
        self.t_mult.choices = "c1,c2,c3"
        self.t_mult.save()

        self.t_bool = utils.create_test(name="test_bool",test_type=models.BOOLEAN)
        self.t_bool.save()

        self.tests = [self.t_simple, self.t_const, self.t_comp, self.t_mult, self.t_bool]

        for test in self.tests:
            utils.create_test_list_membership(self.test_list,test)

        group = Group(name="foo")
        group.save()

        self.unit_test_list = utils.create_unit_test_collection(
            test_collection=self.test_list
        )

        self.unit_test_infos = []
        for test in self.tests:
            self.unit_test_infos.append(models.UnitTestInfo.objects.get(test=test,unit=self.unit_test_list.unit))
        self.url = reverse("perform_qa",kwargs={"pk":self.unit_test_list.pk})
        self.client.login(username="user",password="password")
        self.user = User.objects.get(username="user")
        self.user.save()
        self.user.groups.add(group)
        self.user.save()
    #----------------------------------------------------------------------
    def test_test_forms_present(self):
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["formset"].forms),len(self.tests))
    #----------------------------------------------------------------------
    def test_test_initial_constant(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.context["formset"].forms[self.tests.index(self.t_const)].initial["value"],
            self.t_const.constant_value
        )
    #----------------------------------------------------------------------
    def test_readonly(self):
        response = self.client.get(self.url)
        readonly = [self.t_comp, self.t_const]

        idxs = [self.tests.index(t) for t in readonly]
        for idx in idxs:
            self.assertEqual(
                response.context["formset"].forms[idx].fields["value"].widget.attrs["readonly"],
                "readonly"
            )
    #----------------------------------------------------------------------
    def test_bool_widget(self):
        response = self.client.get(self.url)
        idx = self.tests.index(self.t_bool)
        widget = response.context["formset"].forms[idx].fields["value"].widget

        self.assertIsInstance(widget,django.forms.RadioSelect)
        self.assertEqual(widget.choices,forms.BOOL_CHOICES )
    #----------------------------------------------------------------------
    def test_mult_choice_widget(self):
        response = self.client.get(self.url)
        idx = self.tests.index(self.t_mult)
        widget = response.context["formset"].forms[idx].fields["value"].widget

        self.assertTrue( isinstance(widget,django.forms.Select))
        self.assertEqual(widget.choices,[('',''),(0,'c1'),(1,'c2'),(2,'c3')])
    #---------------------------------------------------------------------------
    def test_perform_valid(self):
        data = {
            "work_started":"11-07-2012 00:09",
            "status":self.status.pk,
            "form-TOTAL_FORMS":len(self.tests),
            "form-INITIAL_FORMS":len(self.tests),
            "form-MAX_NUM_FORMS":"",
        }

        for test_idx, uti in enumerate(self.unit_test_infos):

            data["form-%d-value"%test_idx] =  1
            data["form-%d-comment"%test_idx]= ""


        response = self.client.post(self.url,data=data)

        #user is redirected if form submitted successfully
        self.assertEqual(response.status_code,302)
    #---------------------------------------------------------------------------
    def test_perform_valid_redirect(self):
        data = {
            "work_started":"11-07-2012 00:09",
            "status":self.status.pk,
            "form-TOTAL_FORMS":len(self.tests),
            "form-INITIAL_FORMS":len(self.tests),
            "form-MAX_NUM_FORMS":"",
        }

        for test_idx, uti in enumerate(self.unit_test_infos):

            data["form-%d-value"%test_idx] =  1
            data["form-%d-comment"%test_idx]= ""


        response = self.client.post(self.url+"?next=%s"%reverse("home"),data=data)

        #user is redirected if form submitted successfully
        self.assertEqual(response.status_code,302)
        self.assertEqual("http://testserver/",response._headers['location'][1])

        u2 = utils.create_user(is_staff=False,is_superuser=False,uname="u2")
        u2.groups.add(Group.objects.get(pk=1))
        u2.save()
        self.client.logout()
        self.client.login(username="u2",password="password")

        response = self.client.post(self.url,data=data)

        #user is redirected if form submitted successfully
        self.assertEqual(response.status_code,302)
        self.assertIn("short-interval",response._headers['location'][1])


    #---------------------------------------------------------------------------
    def test_perform_invalid(self):
        data = {

            "work_completed":"11-07-2012 00:10",
            "work_started":"11-07-2012 00:09",
            "status":self.status.pk,
            "form-TOTAL_FORMS":len(self.tests),
            "form-INITIAL_FORMS":len(self.tests),
            "form-MAX_NUM_FORMS":"",
        }

        for test_idx, test in enumerate(self.tests):
            data["form-%d-test" % test_idx] = test.pk
            data["form-%d-comment"%test_idx]= ""


        response = self.client.post(self.url,data=data)

        #no values sent so there should be form errors and a 200 status
        self.assertEqual(response.status_code,200)

        for f in response.context["formset"].forms:
            self.assertTrue(len(f.errors)>0)
    #---------------------------------------------------------------------------
    def test_skipped(self):
        data = {
            "work_completed":"11-07-2012 00:10",
            "status":self.status.pk,
            "form-TOTAL_FORMS":len(self.tests),
            "form-INITIAL_FORMS":"0",
            "form-MAX_NUM_FORMS":"",
        }

        for test_idx, test in enumerate(self.tests):
            data["form-%d-test" % test_idx] = test.pk
            data["form-%d-skipped" % test_idx] = "true"
            data["form-%d-comment"%test_idx]= ""

        response = self.client.post(self.url,data=data)

        #skipped but no comment so there should be form errors and a 200 status
        self.assertEqual(response.status_code,200)

        for f in response.context["formset"].forms:
            self.assertTrue(len(f.errors)>0)

    #----------------------------------------------------------------------
    def test_cycle(self):
        tl1 = utils.create_test_list(name="tl1")
        tl2 = utils.create_test_list(name="tl2")
        cycle = utils.create_cycle(test_lists=[tl1,tl2])
        utc = utils.create_unit_test_collection(
            test_collection=cycle,
            unit=self.unit_test_list.unit,
            frequency=self.unit_test_list.frequency,
        )
        url = reverse("perform_qa",kwargs={"pk":utc.pk})

        response = self.client.get(url)
        self.assertListEqual(response.context["days"],[1,2])
        self.assertEqual(response.context["current_day"],1)

    #----------------------------------------------------------------------
    def test_include_admin(self):

        #orig user is staff so admin should be included
        response = self.client.get(self.url)
        self.assertTrue(response.context["include_admin"])

        u2 = utils.create_user(is_staff=False,is_superuser=False,uname="u2")
        u2.groups.add(Group.objects.get(pk=1))
        u2.save()
        self.client.logout()
        self.client.login(username="u2",password="password")

        #new user is not staff so admin should not be included
        response = self.client.get(self.url)
        self.assertFalse(response.context["include_admin"])
    #----------------------------------------------------------------------
    def test_no_status(self):
        from django.contrib import messages
        models.TestInstanceStatus.objects.all().delete()
        response = self.client.get(self.url)
        self.assertTrue(len(list(response.context['messages']))==1)

    #---------------------------------------------------------------------------
    def test_perform_invalid_ref(self):
        data = {

            "work_completed":"11-07-2012 00:10",
            "work_started":"11-07-2012 00:09",
            "status":self.status.pk,
            "form-TOTAL_FORMS":len(self.tests),
            "form-INITIAL_FORMS":len(self.tests),
            "form-MAX_NUM_FORMS":"",
        }

        ref = utils.create_reference()
        ref.value = 0
        ref.save()

        tol = utils.create_tolerance()
        tol.type = models.PERCENT
        tol.save()

        self.unit_test_infos[0].reference = ref
        self.unit_test_infos[0].tolerance = tol
        self.unit_test_infos[0].save()

        for test_idx, uti in enumerate(self.unit_test_infos):
            data["form-%d-value"%test_idx] =  1
            data["form-%d-comment"%test_idx]= ""


        response = self.client.post(self.url,data=data)

        #no values sent so there should be form errors and a 200 status
        self.assertEqual(response.status_code,302)
        ti = models.TestInstance.objects.get(unit_test_info=self.unit_test_infos[0])
        self.assertIsNone(ti.value)
    #----------------------------------------------------------------------
    def test_missing_unit_test_info(self):
        self.unit_test_infos[0].delete()
        response = self.client.get(self.url)
        self.assertIn("do not treat",str(list(response.context['messages'])[0]).lower())

    #----------------------------------------------------------------------
    def test_invalid_day(self):

        tl1 = utils.create_test_list(name="tl1")
        tl2 = utils.create_test_list(name="tl2")
        cycle = utils.create_cycle(test_lists=[tl1,tl2])
        utc = utils.create_unit_test_collection(
            test_collection=cycle,
            unit=self.unit_test_list.unit,
            frequency=self.unit_test_list.frequency,
        )
        url = reverse("perform_qa",kwargs={"pk":utc.pk})+"?day=22"

        response = self.client.get(url)

        self.assertEqual(response.status_code,404)

#============================================================================
class TestBaseEditTestListInstance(TestCase):
    #----------------------------------------------------------------------
    def setUp(self):
        self.view = views.BaseEditTestListInstance()
    #----------------------------------------------------------------------
    def test_form_valid_not_implemented(self):
        self.assertRaises(NotImplementedError,self.view.form_valid,None)

#============================================================================
class TestEditTestListInstance(TestCase):

    #----------------------------------------------------------------------
    def setUp(self):

        self.view = views.EditTestListInstance.as_view()
        self.factory = RequestFactory()

        self.status = utils.create_status()

        self.test_list = utils.create_test_list()
        self.test = utils.create_test(name="test_simple")
        utils.create_test_list_membership(self.test_list,self.test)

        self.utc = utils.create_unit_test_collection(test_collection=self.test_list)
        self.tli = utils.create_test_list_instance(unit_test_collection=self.utc)

        uti = models.UnitTestInfo.objects.get(pk=1)

        self.ti = utils.create_test_instance(unit_test_info=uti,value=1,status=self.status)
        self.ti.test_list_instance = self.tli
        self.ti.save()

        self.url = reverse("edit_tli",kwargs={"pk":self.tli.pk})
        self.client.login(username="user",password="password")
        self.user = User.objects.get(username="user")
        self.user.save()

        self.base_data = {
            "work_completed":"11-07-2012 00:10",
            "work_started":"11-07-2012 00:09",
            "status":self.status.pk,
            "testinstance_set-TOTAL_FORMS":"1",
            "testinstance_set-INITIAL_FORMS":"1",
            "testinstance_set-MAX_NUM_FORMS":"",
            "testinstance_set-0-id":self.ti.pk,
            "testinstance_set-0-value":1,
        }

    #----------------------------------------------------------------------
    def test_get(self):

        response = self.client.get(self.url)
        self.assertEqual(200,response.status_code)

    #----------------------------------------------------------------------
    def test_edit(self):

        self.base_data.update({
            "testinstance_set-0-value":88,
        })

        response = self.client.post(self.url,data=self.base_data)

        self.assertEqual(302,response.status_code)
        self.assertEqual(88,models.TestInstance.objects.get(pk=1).value)
    #----------------------------------------------------------------------
    def test_no_work_completed(self):

        self.base_data.update({
            "testinstance_set-0-value":88,
            "work_completed":""
        })

        response = self.client.post(self.url,data=self.base_data)

        self.assertEqual(302,response.status_code)
    #----------------------------------------------------------------------
    def test_no_value(self):

        self.base_data.update({
            "testinstance_set-0-value":None,
        })

        response = self.client.post(self.url,data=self.base_data)

        self.assertEqual(200,response.status_code)

    #----------------------------------------------------------------------
    def test_no_work_started(self):

        del self.base_data["work_started"]

        response = self.client.post(self.url,data=self.base_data)
        self.assertEqual(200,response.status_code)
    #----------------------------------------------------------------------
    def test_next_redirect(self):
        """"""
        response = self.client.post(self.url+"?next=%s"%reverse("home"),data=self.base_data)
        self.assertEqual(302,response.status_code)

    #----------------------------------------------------------------------
    def test_invalid_ref_on_edit(self):

        ref = utils.create_reference()
        tol = utils.create_tolerance()
        tol.type = models.PERCENT
        tol.save()


        self.ti.reference = ref
        self.ti.tolerance = tol
        self.ti.save()

        ref.value = 0
        ref.save()

        self.base_data.update({
            "testinstance_set-0-reference":ref.pk,
            "testinstance_set-0-tolerance":tol.pk,
        })

        response = self.client.post(self.url,data=self.base_data)
        ti = models.TestInstance.objects.get(pk=self.ti.pk)

        #if saved with inavlid ref, test list instance should be saved
        #and test instance should be saved with value of None and comment
        self.assertEqual(response.status_code,302)
        self.assertIsNone(ti.value)
        self.assertNotIn(ti.comment,("",None))

#============================================================================
class TestReviewTestListInstance(TestCase):

    #----------------------------------------------------------------------
    def setUp(self):

        self.view = views.ReviewTestListInstance.as_view()
        self.factory = RequestFactory()

        self.status = utils.create_status()
        self.review_status = utils.create_status(name="reviewed",slug="reviewed",is_default=False)
        self.review_status.requires_review = False
        self.review_status.save()

        self.test_list = utils.create_test_list()
        self.test = utils.create_test(name="test_simple")
        utils.create_test_list_membership(self.test_list,self.test)

        self.utc = utils.create_unit_test_collection(test_collection=self.test_list)
        self.tli = utils.create_test_list_instance(unit_test_collection=self.utc)

        uti = models.UnitTestInfo.objects.get(pk=1)

        self.ti = utils.create_test_instance(unit_test_info=uti,value=1,status=self.status)
        self.ti.test_list_instance = self.tli
        self.ti.save()

        self.url = reverse("review_test_list_instance",kwargs={"pk":self.tli.pk})
        self.client.login(username="user",password="password")
        self.user = User.objects.get(username="user")
        self.user.save()

        self.base_data = {
            "testinstance_set-TOTAL_FORMS":"1",
            "testinstance_set-INITIAL_FORMS":"1",
            "testinstance_set-MAX_NUM_FORMS":"",
            "testinstance_set-0-id":self.ti.pk,
            "testinstance_set-0-value":1,
        }

    #----------------------------------------------------------------------
    def test_update(self):

        response = self.client.get(self.url)

        self.base_data.update({
            "testinstance_set-0-status":self.review_status.pk,
        })

        self.assertEqual(1,models.TestListInstance.objects.unreviewed().count())
        response = self.client.post(self.url,data=self.base_data)

        self.assertEqual(302,response.status_code)
        ti = models.TestInstance.objects.get(pk=self.ti.pk)
        self.assertEqual(ti.status,self.review_status)
        self.assertEqual(0,models.TestListInstance.objects.unreviewed().count())



if __name__ == "__main__":
    setup_test_environment()
    unittest.main()