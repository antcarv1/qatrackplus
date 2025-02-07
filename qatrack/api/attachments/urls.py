from django.urls import include, re_path
from rest_framework import routers

from qatrack.api.attachments import views

router = routers.DefaultRouter()
router.register(r'attachments', views.AttachmentViewSet)

urlpatterns = [
    re_path('^', include(router.urls)),
]
