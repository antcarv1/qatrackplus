from django.urls import include, re_path
from rest_framework import routers

from qatrack.api.contenttypes import views

router = routers.DefaultRouter()
router.register(r'contenttypes', views.ContentTypeViewSet)

urlpatterns = [
    re_path('^', include(router.urls)),
]
