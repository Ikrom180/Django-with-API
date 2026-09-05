# accounts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AccountViewSet

router = DefaultRouter()
router.register(r'account', AccountViewSet, basename='account')

urlpatterns = [
    path('1.0.0/', include(router.urls)),
]