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
from django.conf import settings
from django.template import Template, Context

from urllib.parse import unquote
 
from datetime import datetime

from openai import OpenAI

from medicaltutordjapp.utils.Gift_to_html import gisfttohtml
from medicaltutordjapp.models import Plan, Quizzes, UserStats, Payment, Voucher

from math import floor

import json
import urllib
import os
import uuid

client = OpenAI(api_key=os.environ.get("API_KEY"), base_url="https://openrouter.ai/api/v1")

def get_app_file_path(*path_parts):
    """Get absolute path to a file within the app directory"""
    return os.path.join(settings.BASE_DIR, 'medicaltutordjapp', *path_parts)

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
    if request.user.is_authenticated:
        # Save current chat state to user profile before logging out
        user_session_key = f'user_{request.user.id}_chat'
        user_session = request.session.get(user_session_key, {})
        
        user_profile = request.user.profile
        user_profile.last_subject = user_session.get('current_subject', '')
        user_profile.last_topic = user_session.get('current_topic', '')
        user_profile.last_chat_content = user_session.get('chat_content', '')
        user_profile.save()
        
        # Clear this user's session data
        if user_session_key in request.session:
            del request.session[user_session_key]
    
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
    return render(request, 'medicaltutordjapp/plans.html', {
        'plans': all_plans
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
            try:
                voucher = Voucher.objects.get(
                    transaction_id=transaction_id,
                    amount=plan.price,
                    card_id=plan.receiver_id_card,  # Use the plan's specific receiver_id_card
                    used=False
                )
                
                # Create payment record
                payment = Payment.objects.create(
                    user=request.user,
                    transaction_id=transaction_id,
                    amount=plan.price,
                    payment_date=datetime.now(),
                    receiver_id_card=plan.receiver_id_card  # Use the plan's specific receiver_id_card
                )
                
                # Mark voucher as used
                voucher.mark_as_used()
                
                # Update user's profile with the new plan
                user_profile = request.user.profile
                user_profile.update_plan(plan)
                
                messages.success(request, f"¡Pago exitoso! Te has suscrito al plan {plan.plan_name}.")
                return redirect('chat')
                
            except Voucher.DoesNotExist:
                # If no matching voucher found, payment is invalid
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
    # Create a unique session key for this user
    user_session_key = f'user_{request.user.id}_chat'
    
    # Only load user's last chat state if we haven't initialized their session yet
    if user_session_key not in request.session:
        request.session[user_session_key] = {
            'chat_content': request.user.profile.last_chat_content or '',
            'current_subject': request.user.profile.last_subject or '',
            'current_topic': request.user.profile.last_topic or ''
        }
    
    context = {
        'initial_chat_content': request.session[user_session_key]['chat_content'],
        'initial_subject': request.session[user_session_key]['current_subject'],
        'initial_topic': request.session[user_session_key]['current_topic']
    }
    
    return render(request, "medicaltutordjapp/chat.html", context)

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
        conversation = []
        
        system_message = "You are a knowledgeable professor. Respond with detailed, informative, and professional answers. Always repond in the user language."
        if subject:
            system_message += f" Specializing in {subject}. Answer questions only about this {subject}. For all other questions that are out of the scope of these subject, please respond politely that the question is out of your scope. In this case, do not answer it."
        
        conversation.append({
            "role": "system", 
            "content": system_message
        })

        if topic:
            system_message += f"The discussion topic is: {topic}."
            conversation.append({"role": "system", "content": system_message})

        conversation.append({"role": "user", "content": message})
        
        # Make the API call to OpenAI to generate the response
        response = client.chat.completions.create(
            model="qwen/qwq-32b:free",
            messages=conversation,
        )

        # Extract the assistant's reply
        assistant_reply = response.choices[0].message.content

        # Only decrement queries if the response was successful and relevant
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
            subject = data.get('subject', '')
            
            if not topic or not subject:
                return JsonResponse({'error': 'Topic and subject are required'}, status=400)
            
            json_path = get_app_file_path('utils', 'Summaries.json')
            
            # Create a unique file path for this user session
            user_id = request.user.id if request.user.is_authenticated else 'anonymous'
            session_id = request.session.session_key or 'default'
            temp_file_base = f'generated_questions_{user_id}_{session_id}'
            
            temp_gift_path = get_app_file_path('tempfiles', f'{temp_file_base}.gift')
            temp_html_path = get_app_file_path('tempfiles', f'{temp_file_base}.html')
            
            with open(json_path, 'r', encoding='utf-8') as file:
                summaries = json.load(file)
            
            if subject not in summaries or topic not in summaries[subject]:
                summary = ", nevermind there's no summary about this topic"
            else:
                summary = str(summaries[subject][topic])
            
            conversation = data.get('conversation', '')
            num_questions = data.get('numQuestions', 3)

            # Updated GIFT instructions without Short Answer
            instructions = """
            General instructions for GIFT format:

            1. Multiple Choice (Single Answer):
            Who's buried in Grant's tomb?{=Grant ~no one ~Napoleon ~Churchill}

            2. Multiple Choice (Multiple Answers):
            What two people are entombed in Grant's tomb? {
               ~%-100%No one
               ~%50%Grant
               ~%50%Grant's wife
               ~%-100%Grant's father
            }

            3. True/False:
            Grant was buried in a tomb in New York City.{T}
            The sun rises in the West.{FALSE}

            4. Matching:
            Match the following countries with their capitals. {
               =Canada -> Ottawa
               =Italy  -> Rome
               =Japan  -> Tokyo
               =India  -> New Delhi
            }

            5. Missing Word:
            Mahatma Gandhi's birthday is an Indian holiday on {~15th ~3rd =2nd} of October.

            6. Numerical:
            Simple range: When was Ulysses S. Grant born?{#1822:5}
            Precise value: What is pi (3 decimals)?{#3.141..3.142}
            Multiple ranges: When was Grant born?{#=1822:0 =%50%1822:2}

            Important formatting rules:
            - Questions must be numbered as "1. question text", "2. question text", "3. question text" and so on
            - Questions must be separated by blank lines
            - Use = for correct answers and ~ for incorrect ones
            - For multiple choice, one = and several ~ answers and don't show the part like "~%-100%" on the interface
            - For numerical, use # and specify ranges with : or ..
            - For matching, minimum three pairs with ->
            - Avoid HTML tags in questions/answers
            - Don't write the question's type
            - Don't show feedback for answers
            - Use UTF-8 encoding to support special characters
            - Ensure no introductory text, comments, or extra formatting in the output
            - DO NOT generate Short Answer questions
            """

            # Generate questions using GPT
            prompt = (
                f"Generate exactly {num_questions} GIFT-format questions in the user language about the topic: {topic} from {subject} and this context: {conversation}. "
                f"Prioritize this summary: {summary}. Questions must strictly follow these GIFT formatting instructions:\n\n{instructions}"
            )
            
            response = client.chat.completions.create(
                model="qwen/qwq-32b:free",
                messages=[{"role": "user", "content": prompt}],
            )

            if not response or not hasattr(response, 'choices') or not response.choices:
                raise ValueError("GPT API did not return a valid response.")

            # Extract the GIFT questions
            questions_gift = response.choices[0].message.content.strip()

            if not questions_gift:
                raise ValueError("GPT API returned an empty response.")
                
            # Save the GIFT questions to a temporary file
            with open(temp_gift_path, 'w', encoding='utf-8') as f:
                f.write(questions_gift)

            # Parse the GIFT file into HTML format
            gift_parser = gisfttohtml(temp_gift_path)
            gift_parser.save_file(temp_html_path)

            # Store the paths in the session for later use
            request.session['temp_gift_path'] = temp_gift_path
            request.session['temp_html_path'] = temp_html_path

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
    # Get the user-specific HTML file path from the session
    temp_html_path = request.session.get('temp_html_path')
    
    if not temp_html_path or not os.path.exists(temp_html_path):
        return redirect('chat')  # Redirect if no questions are generated
        
    try:
        with open(temp_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Parse the HTML content as a template
        template = Template(html_content)
        context = Context({'csrf_token': request.CSRF_token if hasattr(request, 'CSRF_token') else None})
        rendered_html = template.render(context)
        
        return render(request, 'medicaltutordjapp/questions.html', {'questions_html': rendered_html})
    except Exception as e:
        print(f"Error rendering questions: {e}")
        return redirect('chat')

def get_correct_subject(topic, subject_topics):
    """Helper function to get the correct subject for a given topic"""
    for subject, topics in subject_topics.items():
        if topic in topics:  # If we find the topic in a subject's topics
            return subject
    return 'Unknown'

@login_required
def get_session_data(request):
    """Get the current user's session data"""
    user_session_key = f'user_{request.user.id}_chat'
    user_session = request.session.get(user_session_key, {})
    
    data = {
        'subject': user_session.get('current_subject', ''),
        'topic': user_session.get('current_topic', ''),
        'chat_content': user_session.get('chat_content', '')
    }
    return JsonResponse(data)

@csrf_exempt
@login_required
def update_session(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            subject = data.get('subject')
            topic = data.get('topic')
            chat_content = data.get('chat_content')
            
            # Get or create user's session data
            user_session_key = f'user_{request.user.id}_chat'
            if user_session_key not in request.session:
                request.session[user_session_key] = {}
            
            # Update session data
            if subject is not None:
                request.session[user_session_key]['current_subject'] = subject
            if topic is not None:
                request.session[user_session_key]['current_topic'] = topic
            if chat_content is not None:
                request.session[user_session_key]['chat_content'] = chat_content
            
            # Update user profile
            user_profile = request.user.profile
            if subject is not None:
                user_profile.last_subject = subject
            if topic is not None:
                user_profile.last_topic = topic
            if chat_content is not None:
                user_profile.last_chat_content = chat_content
            
            user_profile.save()
            request.session.modified = True
            return JsonResponse({'status': 'success'})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def qualify_answers(request):
    if request.method == 'POST':
        try:
            # Get the answers from the request
            data = json.loads(request.body)
            
            # Get the GIFT file path from the session
            temp_gift_path = request.session.get('temp_gift_path')
            if not temp_gift_path or not os.path.exists(temp_gift_path):
                return JsonResponse({'error': 'Questions file not found'}, status=500)
            
            try:
                # Parse and qualify
                gift_parser = gisfttohtml(temp_gift_path)
                questions = {str(i+1): q.text for i, q in enumerate(gift_parser.questions())}
                results = gift_parser.qualify_answers(data)
                
                # Add user answers to results
                for q_id, result in results.items():
                    user_answer = data.get(f"q{q_id}")
                    if isinstance(user_answer, list):
                        result['user_answer'] = ', '.join(user_answer)
                    else:
                        result['user_answer'] = user_answer if user_answer else "Sin respuesta"
                
                # Calculate score using the original method
                correct_answers = sum(1 for result in results.values() if result['result'])
                total_questions = len(results)
                score = max(2,floor(5 * (correct_answers / total_questions)))
                
                # Save quiz results if user is authenticated
                if request.user.is_authenticated:
                    user_session_key = f'user_{request.user.id}_chat'
                    user_session = request.session.get(user_session_key, {})
                    current_subject = user_session.get('current_subject', '')
                    current_topic = user_session.get('current_topic', '')
                    
                    if current_subject and current_topic:
                        quiz = Quizzes.objects.create(
                            user=request.user,
                            topic=current_topic,
                            matter=current_subject,
                            questions_count=total_questions,
                            score=score,
                            created_at=datetime.now()
                        )
                        
                        # Update user stats
                        stats = request.user.profile.stats
                        if stats:
                            # Update total quizzes
                            stats.total_quizzes = (stats.total_quizzes or 0) + 1
                            stats.last_activity = datetime.now()
                            
                            # Update average score
                            if stats.average_score is None:
                                stats.average_score = score
                            else:
                                stats.average_score = (stats.average_score * (stats.total_quizzes - 1) + score) / stats.total_quizzes
                            
                            # Update subject averages
                            subject_averages = stats.subject_averages or {}
                            if current_subject in subject_averages:
                                old_avg = subject_averages[current_subject]
                                subject_count = sum(1 for q in Quizzes.objects.filter(user=request.user) if q.matter == current_subject)
                                new_avg = (old_avg * (subject_count - 1) + score) / subject_count
                                subject_averages[current_subject] = new_avg
                            else:
                                subject_averages[current_subject] = score
                            
                            stats.subject_averages = subject_averages
                            stats.save()
                
                # Keep the files until after the results are displayed
                return JsonResponse({
                    'result': results,
                    'total_score': score,
                    'questions': questions
                })
                
            except Exception as e:
                if os.path.exists(temp_gift_path):
                    os.remove(temp_gift_path)
                html_path = request.session.get('temp_html_path')
                if html_path and os.path.exists(html_path):
                    os.remove(html_path)
                raise e
                    
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Invalid request method'}, status=400)

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
    
    # Get the current subject and topic from the session
    user_session_key = f'user_{request.user.id}_chat'
    user_session = request.session.get(user_session_key, {})
    
    current_subject = user_session.get('current_subject', '')
    current_topic = user_session.get('current_topic', '')
    chat_content = user_session.get('chat_content', '')

    try:
        # Decode URL-encoded JSON
        results = json.loads(unquote(results_encoded))
        questions = json.loads(unquote(questions_encoded))
    except (ValueError, json.JSONDecodeError):
        results = {}
        questions = {}

    # Clean up temporary files after results are displayed
    temp_gift_path = request.session.get('temp_gift_path')
    if temp_gift_path and os.path.exists(temp_gift_path):
        os.remove(temp_gift_path)
    
    temp_html_path = request.session.get('temp_html_path')
    if temp_html_path and os.path.exists(temp_html_path):
        os.remove(temp_html_path)
    
    # Clear the file paths from session
    request.session.pop('temp_gift_path', None)
    request.session.pop('temp_html_path', None)

    return render(request, "medicaltutordjapp/qualified_answers.html", {
        'score': score,
        'results': results,
        'questions': questions,
        'subject': current_subject,
        'topic': current_topic,
        'chat_content': chat_content
    })

@login_required
def statistics(request):
    user_stats, created = UserStats.objects.get_or_create(user=request.user)
    recent_quizzes = Quizzes.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    json_path = get_app_file_path('utils', 'Summaries.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            subject_topics = json.load(file)
    except FileNotFoundError:
        subject_topics = {}
        print(f"Error: Summaries.json not found at {json_path}")
    except json.JSONDecodeError:
        subject_topics = {}
        print(f"Error: Invalid JSON in Summaries.json at {json_path}")
    
    subject_averages = []
    for subject, score in user_stats.subject_averages.items():
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



