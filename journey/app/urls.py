from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.JourneySearchView.as_view(), name='journey_search'),
]
