from django.urls import path

from .views import grant_list

urlpatterns = [
    path("api/grants/", grant_list, name="grant-list"),
]
