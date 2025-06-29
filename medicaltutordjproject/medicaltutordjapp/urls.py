from medicaltutordjapp import views
from django.urls import path

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('plans/', views.plans, name='plans'),
    path('subscribe/<int:plan_id>/', views.subscribe, name='subscribe'),
    path('check_quiz_limit/', views.check_quiz_limit, name='check_quiz_limit'),
    path('chat/', views.chat, name='chat'),
    path('ask_gpt', views.ask_gpt, name='ask_gpt'),
    path('generate_questions/', views.generate_questions, name='generate_questions'),
    path('questions/', views.questions, name='questions'),
    path('qualify_answers/', views.qualify_answers, name='qualify_answers'),
    path('qualified_answers/', views.qualified_answers, name='qualified_answers'),
    path('statistics/', views.statistics, name='statistics'),
    path('get_session_data/', views.get_session_data, name='get_session_data'),
    path('update_session/', views.update_session, name='update_session'),
    path('restore_quiz_count/', views.restore_quiz_count, name='restore_quiz_count'),
    path('cleanup_temp_files/', views.cleanup_temp_files, name='cleanup_temp_files'),
    path('password_reset/', views.password_reset_request, name='password_reset'),
    path('password_reset/done/', views.password_reset_done, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('reset/done/', views.password_reset_complete, name='password_reset_complete')
]
