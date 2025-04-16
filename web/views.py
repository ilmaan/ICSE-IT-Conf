from django.shortcuts import render,redirect
from .models import *
from django.http import JsonResponse
from django.http.response import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import os
import stripe
from django.contrib import messages
from django.conf import settings
from django.views.generic.base import TemplateView
import json
from django.views.decorators.http import require_POST
from django.templatetags.static import static 
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

def registration_info(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        print(f"req:{name}")
        email = request.POST.get('email')
        paper_title = request.POST.get('paperDetails1')
        paper_number = request.POST.get('paperNumber')
        number_of_papers = request.POST.get('numberOfPapers')
        student_status = 0 if request.POST.get('registrationType') == 'student' else 1
        if RegistrationInfo.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'error': 'Email already registered'})

        # Create a new registration entry
        registration_info = RegistrationInfo.objects.create(
            name=name,
            email=email,
            paper_title=paper_title,
            paper_number=paper_number,
            number_of_papers=number_of_papers,
            student_status=student_status,
            payment_status=False
        )

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

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
            messages.success(request, "Email unsubscribed successfully.")
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

@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)

@csrf_exempt
@require_POST
def create_checkout_session(request):
    data = json.loads(request.body)
    email = data.get('email')
    if not email:
        return JsonResponse({'error': 'Email is required'}, status=400)

    try:
        registration_info = RegistrationInfo.objects.get(email=email)
    except RegistrationInfo.DoesNotExist:
        return JsonResponse({'error': 'No registration found for this email'}, status=404)

    # Calculate the total amount based on student status and number of papers
    base_fee = 550 if registration_info.student_status == 0 else 650
    extra_papers = max(0, registration_info.number_of_papers - 1)
    extra_fee = extra_papers * 500
    total_amount = base_fee + extra_fee

    domain_url = 'http://localhost:8000/'
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        checkout_session = stripe.checkout.Session.create(
            client_reference_id=email,
            success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + 'cancelled/',
            payment_method_types=['card'],
            mode='payment',
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Conference Registration Fee',
                        'description': 'The International Conference on Software Engineering of Emerging Technologies (SEET-2025) will serve as a premier global forum for engineers and scientists from industry and academia to showcase ongoing work, share research insights and experiences, and discuss effective Software Engineering practices.',
                       'images': ['https://seet25.sw-conf.com/static/app/images/SEET_rev2.png']
                    },
                    'unit_amount': total_amount * 100,
                    'tax_behavior': 'exclusive',
                },
                'quantity': 1,
            }],
            automatic_tax={'enabled': True}, 
        )
        return JsonResponse({'sessionId': checkout_session['id']})
    except Exception as e:
        return JsonResponse({'error': str(e)})

@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        email = session.get('client_reference_id')
        print(f"Session data: {session}")
        print(f"Client reference ID (email): {email}")
        
        if email:
            try:
                registration_info = RegistrationInfo.objects.get(email=email)
                registration_info.payment_status = True
                registration_info.save()
                print("Payment was successful and updated in the database.")
            except RegistrationInfo.DoesNotExist:
                print("No registration found for this email.")

    return HttpResponse(status=200)

@csrf_exempt
@require_POST
def check_payment_status(request):
    data = json.loads(request.body)
    email = data.get('email')
    if not email:
        return JsonResponse({'error': 'Email is required'}, status=400)

    try:
        registration_info = RegistrationInfo.objects.get(email=email)
        if registration_info.payment_status:
            return JsonResponse({'paymentDone': True})
        else:
            return JsonResponse({'paymentDone': False})
    except RegistrationInfo.DoesNotExist:
        return JsonResponse({'error': 'No registration found for this email'}, status=404)

class SuccessView(TemplateView):
    template_name = 'success.html'

class CancelledView(TemplateView):
    template_name = 'cancelled.html'