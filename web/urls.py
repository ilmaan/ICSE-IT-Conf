from django.urls import path

from . import views


urlpatterns = [
    path('',views.home,name='home'),
    path('submissions',views.submissions,name='submissions'),
    path('travel',views.travel,name='travel'),
    path('registration',views.registration,name='registration'),
    path('tbd',views.tbd,name='tbd'),
    path('unsubscribe',views.unsubscribe,name='unsubscribe'),
    path('subscribe',views.subscribe,name='subscribe'),
    path('subscribeemails',views.unsubscribe_emails,name='subscribeemails'),
    

]