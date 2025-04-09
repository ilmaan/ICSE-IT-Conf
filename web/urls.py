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
    path('subscribe-emails',views.unsubscribe_emails,name='subscribeemails'),
    path('config/', views.stripe_config),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('webhook/', views.stripe_webhook),
    path('success/', views.SuccessView.as_view()),
    path('cancelled/', views.CancelledView.as_view()),
    path('registration_info/', views.registration_info, name='registration_info'),
    path('check-payment-status/', views.check_payment_status, name='check_payment_status'),
]