from django.urls import path
from medicaltutordjapp import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('plans/', views.plans, name='plans'),
    path('chat/', views.chat, name='chat'),
    path('ask_gpt', views.ask_gpt, name='ask_gpt'),
    path('generate_questions/', views.generate_questions, name='generate_questions'),
    path('questions/', views.questions, name='questions'),
    path('qualify_answers/', views.qualify_answers, name='qualify_answers'),
    path('qualified_answers/', views.qualified_answers, name='qualified_answers')
]