from django.urls import include, path, re_path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register('registration', views.RegistrationView)
router.register('request', views.RequestView)
router.register('results', views.ResultsView)
router.register('messages', views.MessagesView)
router.register('tariffs', views.TariffView)
router.register('admin-request', views.AdminRequestView)

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]