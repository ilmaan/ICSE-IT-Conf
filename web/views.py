from django.shortcuts import render

from .models import *

# Create your views here.


def home(request):
    return render(request, 'home.html')

def submissions(request):
    context = Information.objects.first()

    return render(request, 'submissions.html',{"context":context})


def travel(request):
    return render(request, 'travel.html')

def tbd(request):
    return render(request, 'tbd.html')

def registration(request):
    return render(request, 'registration.html')