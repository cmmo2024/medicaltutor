from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.core.mail import send_mail, BadHeaderError
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from urllib.parse import unquote
 
from datetime import datetime

from openai import OpenAI

from medicaltutordjapp.utils.Gift_to_html import gisfttohtml
from medicaltutordjapp.models import Plan, Quizzes, UserStats, Payment, Voucher

from math import floor

import json
import urllib

client = OpenAI(api_key='', base_url="https://openrouter.ai/api/v1")

def home(request):
    if request.user.is_authenticated:
        return redirect('chat')
    return render(request, "medicaltutordjapp/home.html")

def signup(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            # Create user with email as username
            user = User.objects.create_user(username=email, email=email, password=password)
            user.first_name = name
            user.save()
            
            # Log the user in
            login(request, user)
            return redirect('chat')
            
        except IntegrityError:
            return redirect('/?error=' + 'El correo electrónico ya está registrado')
        except Exception as e:
            return redirect('/?error=' + str(e))
    
    return redirect('home')

@receiver(user_logged_in)
def on_user_login(sender, user, request, **kwargs):
    """
    Signal handler to restore user's session data when they log in
    """
    # Restore last active subject and topic if they exist in the user's profile
    if hasattr(user, 'profile'):
        request.session['current_subject'] = getattr(user.profile, 'last_subject', None)
        request.session['current_topic'] = getattr(user.profile, 'last_topic', None)
        request.session.modified = True

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(username=email, password=password)
        if user is not None:
            login(request, user)
            
            # Restore session data
            if 'current_subject' in request.session:
                request.session['restored_subject'] = request.session['current_subject']
            if 'current_topic' in request.session:
                request.session['restored_topic'] = request.session['current_topic']
            
            return redirect('chat')
        else:
            return redirect('/?error=' + 'Correo electrónico o contraseña incorrectos')
    
    return redirect('home')

@login_required
def logout_view(request):
    # Save current session data to user profile before logging out
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        request.user.profile.last_subject = request.session.get('current_subject')
        request.user.profile.last_topic = request.session.get('current_topic')
        request.user.profile.save()
    
    logout(request)
    return redirect('home')

def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            users = User.objects.filter(email=email)
            if users.exists():
                user = users[0]
                subject = "Password Reset Requested"
                email_template_name = "medicaltutordjapp/password_reset/password_reset_email.html"
                context = {
                    "email": user.email,
                    'domain': request.get_host(),
                    'site_name': 'Medical Tutor',
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "user": user,
                    'token': default_token_generator.make_token(user),
                    'protocol': 'https' if request.is_secure() else 'http',
                }
                email_content = render_to_string(email_template_name, context)
                try:
                    send_mail(subject, email_content, None, [user.email])
                except BadHeaderError:
                    return JsonResponse({"error": "Invalid header found."})
                return redirect("password_reset_done")
            else:
                messages.error(request, "No user found with that email address.")
    else:
        form = PasswordResetForm()
    return render(request, "medicaltutordjapp/password_reset/password_reset.html", {"form": form})

def password_reset_done(request):
    return render(request, "medicaltutordjapp/password_reset/password_reset_done.html")

def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                return redirect("password_reset_complete")
        else:
            form = SetPasswordForm(user)
        return render(request, "medicaltutordjapp/password_reset/password_reset_confirm.html", {"form": form})
    else:
        messages.error(request, "The reset link is no longer valid.")
        return redirect("home")

def password_reset_complete(request):
    return render(request, "medicaltutordjapp/password_reset/password_reset_complete.html")

def plans(request):
    all_plans = Plan.objects.all()
    # Get the receiver payment information from the Payment model's constants
    receiver_id_card = Payment.RECEIVER_ID_CARD
    return render(request, 'medicaltutordjapp/plans.html', {
        'plans': all_plans,
        'receiver_id_card': receiver_id_card
    })

def subscribe(request, plan_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        transaction_id = request.POST.get('transaction_id')
        
        try:
            plan = Plan.objects.get(pk=plan_id)
            
            # Check if transaction_id has already been used in a payment
            if Payment.objects.filter(transaction_id=transaction_id).exists():
                error_message = "Este número de transacción ya ha sido utilizado."
                return redirect(f'/plans/?error={urllib.parse.quote(error_message)}&plan_id={plan_id}')
            
            # Check if voucher exists and hasn't been used

            # Create payment record
            payment = Payment.objects.create(
                user=request.user,
                transaction_id=transaction_id,
                amount=plan.price,
                payment_date=datetime.now()
            )
            
            # Check if there's a matching voucher
            try:
                voucher = Voucher.objects.get(
                    transaction_id=transaction_id,
                    amount=plan.price,
                    card_id=Payment.RECEIVER_ID_CARD,
                    used=False  # Only get unused vouchers
                )
                
                # Create payment record
                payment = Payment.objects.create(
                    user=request.user,
                    transaction_id=transaction_id,
                    amount=plan.price,
                    payment_date=datetime.now()
                )
                
                # Mark voucher as used
                voucher.mark_as_used()
                
                # Update user's profile with the new plan
                user_profile = request.user.profile
                user_profile.update_plan(plan)
                
                # If voucher exists, payment is valid
                # Update user's profile with the new plan
                user_profile = request.user.profile
                user_profile.plan = plan
                user_profile.save()                
                messages.success(request, f"¡Pago exitoso! Te has suscrito al plan {plan.plan_name}.")
                return redirect('chat')
                
            except Voucher.DoesNotExist:
                # If no matching voucher found, payment is invalid
                payment.delete()  # Remove the invalid payment record
                error_message = "Pago no válido. Por favor verifica los datos de la transacción."
                return redirect(f'/plans/?error={urllib.parse.quote(error_message)}&plan_id={plan_id}')
                
        except Plan.DoesNotExist:
            error_message = "Plan no encontrado."
            return redirect(f'/plans/?error={urllib.parse.quote(error_message)}')
        except Exception as e:
            error_message = f"Error al procesar el pago: {str(e)}"
            return redirect(f'/plans/?error={urllib.parse.quote(error_message)}&plan_id={plan_id}')
    
    return redirect('plans')

@login_required
def chat(request):
    return render(request, "medicaltutordjapp/chat.html")

@require_GET
def ask_gpt(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'User not authenticated'}, status=401)

    # Extract parameters with default values
    subject = request.GET.get('subject', '')
    topic = request.GET.get('topic', '')
    message = request.GET.get('message')

    # Ensure the message is not empty
    if not message:
        return JsonResponse({'error': 'Message parameter is missing'}, status=400)

    # Check if user has a paid plan with remaining queries
    user_profile = request.user.profile
    if user_profile.plan and user_profile.remaining_queries == 0:
        return JsonResponse({
            'error': 'Has alcanzado el límite de preguntas en tu plan actual. ' +
                    'Puedes seguir haciendo cuestionarios o adquirir un nuevo plan.'
        })

    try:
        # Prepare the conversation history
        conversation = []
        
        system_message = "You are a knowledgeable professor. Respond with detailed, informative, and professional answers."
        if subject:
            system_message += f" Specializing in {subject}."
        
        conversation.append({
            "role": "system", 
            "content": system_message
        })

        if topic:
            conversation.append({"role": "system", "content": f"The current topic of discussion is: {topic}"})

        conversation.append({"role": "user", "content": message})
        
        # Make the API call to OpenAI
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=conversation,
        )

        # Extract the assistant's reply
        assistant_reply = response.choices[0].message.content

        # Only decrement queries if the response was successful
        if user_profile.plan:
            user_profile.decrement_queries()
            # Check if both counters are 0 and reset to free plan
            if user_profile.remaining_queries == 0 and user_profile.remaining_quizzes == 0:
                user_profile.plan = None
                user_profile.save()

        return JsonResponse({'response': assistant_reply})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def check_quiz_limit(request):
    """Check if user can take a quiz based on their plan limits"""
    if not request.user.is_authenticated:
        return JsonResponse({'can_take_quiz': False})
        
    user_profile = request.user.profile
    if user_profile.plan:
        if user_profile.remaining_quizzes > 0:
            return JsonResponse({'can_take_quiz': True})
        else:
            return JsonResponse({
                'can_take_quiz': False,
                'message': 'Has alcanzado el límite de cuestionarios en tu plan actual. ' +
                          'Puedes seguir haciendo preguntas o adquirir un nuevo plan.'
            })
    return JsonResponse({'can_take_quiz': True})

@csrf_exempt
def generate_questions(request):
    if request.method == 'POST':
        try:
            # Parse request data
            data = json.loads(request.body)
            topic = data.get('topic', '')
            
            with open("../medicaltutordjproject/medicaltutordjapp/utils/Summaries.json", 'r', encoding='utf-8') as file:
                summaries = json.load(file)
            
            if topic not in summaries:
                summary = ", nevermind there's no summary about this topic"
            else:
                summary = summaries[topic]
            
            conversation = data.get('conversation', '')
            num_questions = data.get('numQuestions', 3)

            if not topic:
                return JsonResponse({'error': 'Topic is missing'}, status=400)

            # Detailed GIFT instructions
            instructions = """
            General instructions for GIFT format:

            - Questions should be numbered as "1. question text", "2. question text", "3. question text" and so on.
            - Each question must be followed by at least one blank line.
            - The question comes first, followed by answers enclosed in curly braces `{}`.
            - Use `=` for correct answers and `~` for incorrect answers.
            - Feedback for answers can be added using `#` (don't show this).
            - Use UTF-8 encoding to support special characters.
            - Ensure no introductory text, comments, or extra formatting in the output.

            Examples:
            - Multiple Choice with Single Right Answer: "Who is buried in Grant's tomb? {=Grant ~Napoleon ~Churchill}"
            - Multiple Choice with Multiple Right Answers (Checkboxes): 
              "What two people are entombed in Grant's tomb? { ~%-100%No one ~%50%Grant ~%50%Grant's wife ~%-100%Grant's father }"
            - True/False: "The sun rises in the East. {T}"
            - Short Answer: "Two plus two equals {=four =4}"
            - Matching: "Match countries to capitals: {=Canada -> Ottawa =India -> New Delhi}"
            - Numerical with Tolerance: "What is pi to 3 decimal places? {#3.141:0.001}"
            - Numerical Range: "What is the value of pi (to 3 decimal places)? {#3.141..3.142}"
            - Missing Word: "Mahatma Gandhi's birthday is in {~January =October ~March}."

            f"Generate clean GIFT format questions in the {conversation} language, strictly following these guidelines."
            """

            # Generate questions using GPT
            prompt = (
                f"Generate exactly {num_questions} GIFT-format questions about the topic: {topic} and this context: {conversation}. Prioritize this {summary}"
                f"Questions must strictly follow these GIFT formatting instructions:\n\n{instructions}"
            )
            response = client.chat.completions.create(
                model="deepseek/deepseek-r1:free",
                messages=[{"role": "user", "content": prompt}],
            )

            if not response or not hasattr(response, 'choices') or not response.choices:
                raise ValueError("GPT API did not return a valid response.")

            # Extract the GIFT questions
            questions_gift = response.choices[0].message.content.strip()

            if not questions_gift:
                raise ValueError("GPT API returned an empty response.")

            # Save the GIFT questions to a temporary file
            temp_file_path = '../medicaltutordjproject/medicaltutordjapp/tempfiles/generated_questions.gift'
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                f.write(questions_gift)

            # Parse the GIFT file into HTML format
            gift_parser = gisfttohtml(temp_file_path)
            html_file_path = '../medicaltutordjproject/medicaltutordjapp/templates/medicaltutordjapp/questions.html'
            gift_parser.save_file(html_file_path)

            # Only decrement the quiz count after successful generation and before redirecting
            if request.user.is_authenticated:
                user_profile = request.user.profile
                if user_profile.plan and user_profile.remaining_quizzes > 0:
                    user_profile.decrement_quizzes()

            # Return the redirect URL only if everything succeeds
            return JsonResponse({'redirect_url': '/questions/'})

        except Exception as e:
            return JsonResponse({'error': 'Failed to generate questions', 'details': str(e)}, status=500)

    # Handle GET requests
    return JsonResponse({'error': 'This endpoint only accepts POST requests.'}, status=400)

def questions(request):
    # This view only handles GET requests to render the questions page
    return render(request, 'medicaltutordjapp/questions.html')

def get_correct_subject(topic, subject_topics):
    """Helper function to get the correct subject for a given topic"""
    for subject, topics in subject_topics.items():
        if topic in topics:  # If we find the topic in a subject's topics
            return subject
    return 'Unknown'

@csrf_exempt
def update_session(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            subject = data.get('subject')
            topic = data.get('topic')
            
            if subject and topic:
                # Load subject-topic mapping
                with open("../medicaltutordjproject/medicaltutordjapp/utils/Summaries.json", 'r', encoding='utf-8') as file:
                    subject_topics = json.load(file)
                
                # Validate and get correct subject
                correct_subject = get_correct_subject(topic, subject_topics)
                
                # Store the correct subject and topic in session
                request.session['current_subject'] = correct_subject
                request.session['current_topic'] = topic
                request.session.modified = True
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'error': 'Missing subject or topic'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
@require_http_methods(["POST"])
def qualify_answers(request):
    """Handle quiz answer qualification"""
    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        
        # Get the GIFT file parser instance
        gift_parser = gisfttohtml('../medicaltutordjproject/medicaltutordjapp/tempfiles/generated_questions.gift')
        
        # Get questions for response
        questions = {i+1: q.text for i, q in enumerate(gift_parser.questions())}
        
        # Qualify the answers
        results = gift_parser.qualify_answers(data)
        
        # Calculate total score
        correct_answers = sum(1 for result in results.values() if result['result'])
        total_questions = len(results)
        
        # Calculate score with minimum of 2
        total_score = max(2, floor((correct_answers / total_questions) * 5))
        
        # Load the subject-topic mapping
        with open("../medicaltutordjproject/medicaltutordjapp/utils/Summaries.json", 'r', encoding='utf-8') as file:
            subject_topics = json.load(file)
            
        # Get current topic from session
        current_topic = request.session.get('current_topic', 'Unknown')
        
        # Determine the correct subject based on the topic
        current_subject = get_correct_subject(current_topic, subject_topics)
        
        # If subject wasn't found, use the session's subject as fallback
        if not current_subject:
            current_subject = request.session.get('current_subject', 'Unknown')
        
        # Save quiz results to database
        if request.user.is_authenticated:
            quiz = Quizzes.objects.create(
                user=request.user,
                topic=current_topic,
                matter=current_subject,
                questions_count=total_questions,
                score=total_score,
                created_at=datetime.now()
            )
            
            # Get or create user stats
            stats, created = UserStats.objects.get_or_create(user=request.user)
            
            # Update user stats
            stats.total_quizzes = (stats.total_quizzes or 0) + 1
            stats.last_activity = datetime.now()
            
            # Update average score
            if stats.average_score is None:
                stats.average_score = total_score
            else:
                stats.average_score = (stats.average_score * (stats.total_quizzes - 1) + total_score) / stats.total_quizzes
            
            stats.save()
            stats.update_subject_averages()
        
        return JsonResponse({
            'result': results,
            'questions': questions,
            'total_score': total_score
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def restore_quiz_count(request):
    """Restore quiz count when user cancels a quiz"""
    try:
        if request.user.is_authenticated:
            user_profile = request.user.profile
            if user_profile.plan:
                user_profile.remaining_quizzes += 1
                user_profile.save()
                return JsonResponse({'success': True, 'message': 'Quiz count restored'})
        return JsonResponse({'success': False, 'message': 'No plan found'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def qualified_answers(request):
    score = request.GET.get('score', 0)
    results_encoded = request.GET.get('results', '')
    questions_encoded = request.GET.get('questions', '')

    try:
        # Decode URL-encoded JSON
        results = json.loads(unquote(results_encoded))
        questions = json.loads(unquote(questions_encoded))
    except (ValueError, json.JSONDecodeError):
        #print("Error decoding results:", e)
        results = {}
        questions = {}

    return render(request, "medicaltutordjapp/qualified_answers.html", {
        'score': score,
        'results': results,
        'questions': questions
    })

@login_required
def statistics(request):
    # Get user stats
    user_stats, created = UserStats.objects.get_or_create(user=request.user)
    
    # Get the 10 most recent quizzes for the user
    recent_quizzes = Quizzes.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    # Load subject-topic mapping to validate subjects
    with open("../medicaltutordjproject/medicaltutordjapp/utils/Summaries.json", 'r', encoding='utf-8') as file:
        subject_topics = json.load(file)
    
    # Get subject averages from UserStats and validate them
    subject_averages = []
    for subject, score in user_stats.subject_averages.items():
        # Only include valid subjects from our mapping
        if subject in subject_topics:
            subject_averages.append({
                'matter': subject,
                'avg_score': score
            })
    
    return render(request, 'medicaltutordjapp/statistics.html', {
        'user_stats': user_stats,
        'recent_quizzes': recent_quizzes,
        'subject_averages': subject_averages
    })
