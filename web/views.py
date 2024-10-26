from django.shortcuts import render

# Create your views here.


def home(request):
    return render(request, 'home.html')

def submissions(request):
    return render(request, 'submissions.html')


def travel(request):
    return render(request, 'travel.html')

def tbd(request):
    return render(request, 'tbd.html')

def registration(request):
    return render(request, 'registration.html')