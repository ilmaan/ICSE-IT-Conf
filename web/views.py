from django.shortcuts import render,redirect
from .models import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
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

@csrf_exempt
def unsubscribe(request):
    # Check if the request method is GET and if the email parameter is provided
    if request.method == "GET":
        email = request.GET.get("email", None)

        # Validate the email parameter
        if email is None or not email.strip():
            return JsonResponse({"error": "Email parameter is required"}, status=400)

        try:
            # Path to the unsubscribe file
            file_path = "unsubscribe_list.txt"
            
            # Open the file in append mode and write the email
            with open(file_path, "a") as file:
                file.write(email.strip() + "\n")

            # return JsonResponse({"message": "Email unsubscribed successfully"}, status=200)
            return redirect('/')

        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    # Return an error response for unsupported HTTP methods
    return JsonResponse({"error": "Invalid request method"}, status=405)
@csrf_exempt
def subscribe(request):
    # Check if the request method is GET and if the email parameter is provided
    if request.method == "GET":
        email = request.GET.get("email", None)

        # Validate the email parameter
        if email is None or not email.strip():
            return JsonResponse({"error": "Email parameter is required"}, status=400)

        try:
            # Path to the unsubscribe file
            file_path = "unsubscribe_list.txt"
            
            # Check if the file exists
            if not os.path.exists(file_path):
                return JsonResponse({"error": "Unsubscribe list does not exist"}, status=404)

            # Read the current file content
            with open(file_path, "r") as file:
                emails = file.readlines()

            # Check if the email exists in the list
            email = email.strip()
            if email + "\n" in emails:
                # Remove the email and overwrite the file
                emails.remove(email + "\n")
                with open(file_path, "w") as file:
                    file.writelines(emails)

                # return JsonResponse({"message": "Email subscribed successfully"}, status=200)
                return redirect('/')
            else:
                return JsonResponse({"error": "Email not found in unsubscribe list"}, status=404)

        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    # Return an error response for unsupported HTTP methods
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def unsubscribe_emails(request):
    if request.method == "GET":
        try:
            # Path to the unsubscribe list file
            unsubscribe_file_path = "unsubscribe_list.txt"
            
            # Check if the file exists
            if os.path.exists(unsubscribe_file_path):
                # Read all emails from the file
                with open(unsubscribe_file_path, "r") as file:
                    emails = [line.strip() for line in file.readlines() if line.strip()]
                
                return JsonResponse({"emails": emails}, status=200)
            else:
                return JsonResponse({"message": "Unsubscribe list file not found."}, status=404)
        
        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
    
    return JsonResponse({"error": "Invalid request method"}, status=405)
