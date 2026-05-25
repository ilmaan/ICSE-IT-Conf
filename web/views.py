from django.shortcuts import render, redirect
from .models import RegistrationInfo, Information
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import logging
import os
import stripe
from django.contrib import messages
from django.conf import settings
from django.views.generic.base import TemplateView
import json
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

REGISTRATION_FEES_CENTS = {
    'regular': 75000,
    'src': 65000,
    'attendee': 55000,
    'phd': 40000,
    'secondary': 10000,
}

REGISTRATION_LABELS = {
    'regular': 'Regular Registration',
    'src': 'SRC Registration',
    'attendee': 'Attendee / Non-Author Registration',
    'phd': 'PhD Research Track',
    'secondary': 'Supplementary Registration',
}

PUBLIC_REGISTRATION_TYPES = {'regular', 'src', 'attendee', 'phd'}


def _get_site_url(request):
    site_url = getattr(settings, 'SITE_URL', '').strip()
    if site_url:
        return site_url if site_url.endswith('/') else f'{site_url}/'
    return request.build_absolute_uri('/')


def _registration_fee_cents(registration_type):
    return REGISTRATION_FEES_CENTS.get(registration_type)


def _is_valid_supplementary_token(token):
    expected = getattr(settings, 'SUPPLEMENTARY_REGISTRATION_TOKEN', '')
    return bool(expected) and token == expected


def _webhook_signing_secrets():
    secrets = []
    for setting_name in ('STRIPE_CLI_ENDPOINT_SECRET', 'STRIPE_ENDPOINT_SECRET'):
        value = (getattr(settings, setting_name, None) or '').strip()
        if value and value not in secrets:
            secrets.append(value)
    return secrets


def _construct_stripe_event(payload, sig_header):
    secrets = _webhook_signing_secrets()
    if not secrets:
        raise stripe.error.SignatureVerificationError(
            'No webhook signing secret configured',
            sig_header,
        )
    last_error = None
    for secret in secrets:
        try:
            return stripe.Webhook.construct_event(payload, sig_header, secret)
        except stripe.error.SignatureVerificationError as exc:
            last_error = exc
    raise last_error


def _email_from_checkout_session(session):
    email = (session.get('client_reference_id') or '').strip().lower()
    if email:
        return email
    customer_details = session.get('customer_details') or {}
    email = (customer_details.get('email') or '').strip().lower()
    if email:
        return email
    return (session.get('customer_email') or '').strip().lower()


def _mark_registration_paid(email):
    if not email:
        return False
    try:
        registration_info = RegistrationInfo.objects.get(email__iexact=email)
    except RegistrationInfo.DoesNotExist:
        logger.warning('No registration found for paid checkout email=%s', email)
        return False
    if registration_info.payment_status:
        return True
    registration_info.payment_status = True
    registration_info.save(update_fields=['payment_status'])
    return True


def fulfill_checkout_session(session_id):
    if not session_id:
        return False, 'Missing checkout session id'

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError as exc:
        logger.exception('Failed to retrieve Stripe session %s', session_id)
        return False, str(exc)

    if session.get('payment_status') != 'paid':
        return False, f"Payment not completed (status: {session.get('payment_status')})"

    email = _email_from_checkout_session(session)
    if not email:
        return False, 'No email found on checkout session'

    if _mark_registration_paid(email):
        return True, email
    return False, f'No registration found for {email}'


def home(request):
    return render(request, 'home.html')


def submissions(request):
    context = Information.objects.first()
    return render(request, 'submissions.html', {"context": context})


def travel(request):
    return render(request, 'travel.html')


def tbd(request):
    return render(request, 'tbd.html')


def registration(request):
    return render(request, 'registration.html')


def registration_secondary(request, token):
    if not _is_valid_supplementary_token(token):
        return render(request, 'registration_not_found.html', status=404)
    return render(request, 'registration_secondary.html', {
        'fee': 100,
        'supplementary_token': token,
    })


def registration_info(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip().lower()
    registration_type = request.POST.get('registrationType', 'regular')
    supplementary_token = request.POST.get('supplementaryToken', '')
    paper_title = request.POST.get('paperDetails1', '')
    paper_number = request.POST.get('paperNumber', '')
    number_of_papers = request.POST.get('numberOfPapers') or 1
    affiliation = request.POST.get('affiliation', '').strip()

    if not name or not email:
        return JsonResponse({'success': False, 'error': 'Name and email are required'})

    if registration_type == 'secondary':
        if not _is_valid_supplementary_token(supplementary_token):
            return JsonResponse({'success': False, 'error': 'Invalid supplementary registration link'})
        if not affiliation:
            return JsonResponse({'success': False, 'error': 'Affiliation is required'})
        number_of_papers = 0
        paper_title = ''
        paper_number = ''
    elif registration_type not in PUBLIC_REGISTRATION_TYPES:
        return JsonResponse({'success': False, 'error': 'Invalid registration type'})

    try:
        number_of_papers = int(number_of_papers)
    except (TypeError, ValueError):
        number_of_papers = 1 if registration_type != 'secondary' else 0

    if registration_type == 'attendee':
        paper_title = paper_title or ''
        paper_number = paper_number or ''
        number_of_papers = 0
    elif registration_type == 'phd':
        if not affiliation:
            return JsonResponse({'success': False, 'error': 'University / affiliation is required'})
        number_of_papers = 0
        paper_number = paper_number or ''
    elif registration_type != 'secondary' and number_of_papers < 1:
        return JsonResponse({'success': False, 'error': 'Number of papers must be at least 1'})

    if RegistrationInfo.objects.filter(email=email).exists():
        return JsonResponse({'success': False, 'error': 'Email already registered'})

    RegistrationInfo.objects.create(
        name=name,
        email=email,
        paper_title=paper_title,
        paper_number=paper_number,
        number_of_papers=number_of_papers,
        registration_type=registration_type,
        affiliation=affiliation or None,
        payment_status=False,
    )

    fee_cents = _registration_fee_cents(registration_type)
    return JsonResponse({
        'success': True,
        'fee': fee_cents / 100 if fee_cents else 0,
        'registrationType': registration_type,
    })


@csrf_exempt
def unsubscribe(request):
    if request.method == "GET":
        email = request.GET.get("email", None)

        if email is None or not email.strip():
            return JsonResponse({"error": "Email parameter is required"}, status=400)

        try:
            file_path = "unsubscribe_list.txt"
            with open(file_path, "a") as file:
                file.write(email.strip() + "\n")

            messages.success(request, "Email unsubscribed successfully.")
            return redirect('/')

        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def subscribe(request):
    if request.method == "GET":
        email = request.GET.get("email", None)

        if email is None or not email.strip():
            return JsonResponse({"error": "Email parameter is required"}, status=400)

        try:
            file_path = "unsubscribe_list.txt"

            if not os.path.exists(file_path):
                return JsonResponse({"error": "Unsubscribe list does not exist"}, status=404)

            with open(file_path, "r") as file:
                emails = file.readlines()

            email = email.strip()
            if email + "\n" in emails:
                emails.remove(email + "\n")
                with open(file_path, "w") as file:
                    file.writelines(emails)

                return redirect('/')
            else:
                return JsonResponse({"error": "Email not found in unsubscribe list"}, status=404)

        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def unsubscribe_emails(request):
    if request.method == "GET":
        try:
            unsubscribe_file_path = "unsubscribe_list.txt"

            if os.path.exists(unsubscribe_file_path):
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
    email = (data.get('email') or '').strip().lower()
    if not email:
        return JsonResponse({'error': 'Email is required'}, status=400)

    try:
        registration_info = RegistrationInfo.objects.get(email=email)
    except RegistrationInfo.DoesNotExist:
        return JsonResponse({'error': 'No registration found for this email'}, status=404)

    if registration_info.payment_status:
        return JsonResponse({'error': 'Payment has already been completed for this email'}, status=400)

    total_amount_cents = _registration_fee_cents(registration_info.registration_type)
    if not total_amount_cents:
        return JsonResponse({'error': 'Invalid registration type'}, status=400)

    product_name = REGISTRATION_LABELS.get(
        registration_info.registration_type,
        'Conference Registration Fee',
    )
    domain_url = _get_site_url(request)
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        checkout_session = stripe.checkout.Session.create(
            client_reference_id=email,
            customer_email=email,
            success_url=domain_url + 'success/?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + 'cancelled/',
            payment_method_types=['card'],
            mode='payment',
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product_name,
                        'description': (
                            'The International Conference on Software Engineering of '
                            'Emerging Technologies (SEET-2026) registration fee.'
                        ),
                        'images': [domain_url + 'static/app/images/SEET_rev2.png'],
                    },
                    'unit_amount': total_amount_cents,
                    'tax_behavior': 'exclusive',
                },
                'quantity': 1,
            }],
            automatic_tax={'enabled': True},
            metadata={
                'registration_type': registration_info.registration_type,
                'registrant_name': registration_info.name,
            },
        )
        return JsonResponse({
            'sessionId': checkout_session['id'],
            'amount': total_amount_cents / 100,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)})


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    if not sig_header:
        logger.warning('Stripe webhook missing signature header')
        return HttpResponse(status=400)

    try:
        event = _construct_stripe_event(payload, sig_header)
    except ValueError:
        logger.warning('Stripe webhook invalid payload')
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.warning(
            'Stripe webhook signature verification failed. '
            'For local testing, copy the secret from `stripe listen` into '
            'STRIPE_CLI_ENDPOINT_SECRET in ICSE_ET/.env'
        )
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        email = _email_from_checkout_session(session)
        if email:
            _mark_registration_paid(email)
        else:
            logger.warning(
                'checkout.session.completed without email: session_id=%s',
                session.get('id'),
            )

    return HttpResponse(status=200)


@csrf_exempt
@require_POST
def check_payment_status(request):
    data = json.loads(request.body)
    email = (data.get('email') or '').strip().lower()
    if not email:
        return JsonResponse({'error': 'Email is required'}, status=400)

    try:
        registration_info = RegistrationInfo.objects.get(email=email)
        return JsonResponse({
            'paymentDone': registration_info.payment_status,
            'registrationType': registration_info.registration_type,
            'fee': (_registration_fee_cents(registration_info.registration_type) or 0) / 100,
        })
    except RegistrationInfo.DoesNotExist:
        return JsonResponse({'error': 'No registration found for this email'}, status=404)


class SuccessView(TemplateView):
    template_name = 'success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_id = self.request.GET.get('session_id')
        payment_confirmed = False
        payment_message = ''

        if session_id:
            payment_confirmed, payment_message = fulfill_checkout_session(session_id)
            if payment_confirmed:
                payment_message = (
                    f'Payment recorded for {payment_message}. '
                    'Thank you for registering.'
                )
            else:
                payment_message = (
                    f'Payment received by Stripe, but we could not update your '
                    f'registration automatically: {payment_message}. '
                    'Please email seet@sw-conf.com with your receipt.'
                )
        else:
            payment_message = (
                'If your payment completed, your registration will be confirmed '
                'shortly. Contact seet@sw-conf.com if status does not update.'
            )

        context['payment_confirmed'] = payment_confirmed
        context['payment_message'] = payment_message
        return context


class CancelledView(TemplateView):
    template_name = 'cancelled.html'
