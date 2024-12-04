from django.urls import path
from medicaltutordjapp import views

urlpatterns = [
    path('', views.home, name='home'),
    path('ask_gpt', views.ask_gpt, name='ask_gpt'),
    path('generate_questions/', views.generate_questions, name='generate_questions'),  # Handle GET requests for the questions page
    path('questions/', views.questions, name='questions'),  # Handle POST requests for generating questions
    path('qualify_answers/', views.qualify_answers, name='qualify_answers'),
    path('qualified_answers/', views.qualified_answers, name='qualified_answers')
]
