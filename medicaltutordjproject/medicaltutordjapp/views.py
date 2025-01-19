from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError

from pathlib import Path
from urllib.parse import unquote 
from medicaltutordjapp.utils.Gift_to_html import gisfttohtml
from medicaltutordjapp.models import Plans

from openai import OpenAI

import json
import openai

client = OpenAI(api_key='')

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

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('chat')
        else:
            return redirect('/?error=' + 'Correo electrónico o contraseña incorrectos')
    
    return redirect('home')

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

def plans(request):
    all_plans = Plans.objects.all()
    return render(request, 'medicaltutordjapp/plans.html', {'plans': all_plans})

@login_required
def chat(request):
    return render(request, "medicaltutordjapp/chat.html")

@require_GET
def ask_gpt(request):
    # Extract the user-provided topic, message, and subject from the GET parameters
    subject = request.GET.get('subject')
    topic = request.GET.get('topic')
    message = request.GET.get('message')

    # Ensure the message is not empty
    if not message:
        return JsonResponse({'error': 'Message parameter is missing'}, status=400)

    # Prepare the conversation history
    conversation = []
    
    # Add a directive for GPT to act like a professor
    conversation.append({"role": "system", "content": "You are a knowledgeable {subject} professor. Respond with detailed, informative, and professional answers."})
    
    # If a subject is provided, add it as a context
    if subject:
        conversation.append({"role": "system", "content": f"The subject is: {subject}"})

    # If a topic is provided, add it as additional context
    if topic:
        conversation.append({"role": "system", "content": f"The topic of discussion is: {topic}"})

    # Add the user's message
    conversation.append({"role": "user", "content": message})
    
    try:
        # Make the API call to OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",  # Or "gpt-3.5-turbo" if you don't have GPT-4 access
            messages=conversation,
        )

        # Extract the assistant's reply
        assistant_reply = response.choices[0].message.content

        # Return the response as JSON
        return JsonResponse({'response': assistant_reply})

    except openai.APIConnectionError as e:
        # Handle API connection errors
        return JsonResponse({'error': str(e.__cause__)}, status=500)

    except openai.PermissionDeniedError as e:
        # Handle permission errors (403)
        return JsonResponse({'error': e.body}, status=403)

    except openai.APIError as e:
        # Handle generic API errors
        return JsonResponse({'error': str(e)}, status=e.status_code)

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
                summary=", nevermind there's no summary about this topic"
            else:
                summary=summaries[topic]
            
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
            - Feedback for answers can be added using `#`.
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
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
            )

            # # Log the raw GPT response for debugging
            # print("Raw GPT Response:", response)

            # Validate the GPT response
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

            # Return the redirect URL only if everything succeeds
            return JsonResponse({'redirect_url': '/questions/'})

        except Exception as e:
            # Log the exception for debugging
            #print("Error generating questions:", e)
            return JsonResponse({'error': 'Failed to generate questions', 'details': str(e)}, status=500)

    # Handle GET requests
    return JsonResponse({'error': 'This endpoint only accepts POST requests.'}, status=400)

def questions(request):
    # This view only handles GET requests to render the questions page
    return render(request, 'medicaltutordjapp/questions.html')

@csrf_exempt
def qualify_answers(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Parse user answers from the request
            data = json.loads(request.body)
            user_answers = {key: value for key, value in data.items() if key.startswith('q')}

            # Directory path and filename handling
            directory_path = Path('../medicaltutordjproject/medicaltutordjapp/tempfiles')
            filename = ""
            if directory_path.exists() and directory_path.is_dir():
                for file in directory_path.iterdir():
                    if file.is_file():
                        filename = file.name
                        break
            else:
                return JsonResponse({'error': 'Directory not found'}, status=404)

            if not filename:
                return JsonResponse({'error': 'No file found in directory'}, status=404)

            # Initialize the GIFT parser
            gift_parser = gisfttohtml(f'../medicaltutordjproject/medicaltutordjapp/tempfiles/{filename}')

            # Qualify answers using gift_parser's method, which handles all logic
            results = gift_parser.qualify_answers(user_answers)
            questions = {str(idx): question.text for idx, question in enumerate(gift_parser.questions(), 1)}

            # Add user_answer to results for each question
            for question_id, result in results.items():
                user_answer = user_answers.get(f"q{question_id}", "No answer")
                # Handle cases where user_answer is a list
                if isinstance(user_answer, list):
                    result['user_answer'] = ", ".join(user_answer)
                else:
                    result['user_answer'] = user_answer.strip()

            # Calculate the total score based on correct answers
            correct_answers = sum(1 for result in results.values() if result['result'])
            total_possible_score = len(results)
            total_score = max(2, (correct_answers * 5) // total_possible_score) if total_possible_score > 0 else 2

            # Return the JSON response with total score, results, and question texts
            return JsonResponse({'total_score': total_score, 'result': results, 'questions': questions})

        except json.JSONDecodeError:
            #print("Error parsing JSON data:", e)
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            #print("Error during qualification:", e)
            return JsonResponse({'error': 'Error during qualification', 'details': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

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