from django.shortcuts import render

# Create your views here.


def home(request):
    return render(request, 'home.html')

def submissions(request):
    return render(request, 'submissions.html')

def tbd(request):
    return render(request, 'tbd.html')