from django.urls import path

from . import views


urlpatterns = [
    path('',views.home,name='home'),
    path('submissions',views.submissions,name='submissions'),
    path('travel',views.travel,name='travel'),
    path('tbd',views.tbd,name='tbd'),
    

]