from django.urls import path
from . import views

urlpatterns = [
    path('', views.select_subject, name='select_subject'),
    path('upload/', views.upload_file, name='upload_file'),
    path('start_quiz/', views.start_quiz, name='start_quiz'),  # クイズ開始
    path('quiz/<str:subject>/<int:history_id>/', views.quiz_page, name='quiz_page'),
    path('api/question/<str:subject>/', views.get_random_question, name='get_random_question'),  # 科目別API
    #path('api/question/', views.get_random_question, name='get_random_question'),  # 問題取得API
    path('submit/', views.submit_answer, name='submit_answer'),
    path('history/', views.history, name='history'),
    path('history/<int:history_id>/', views.history_detail, name='history_detail'),
    path('api/question_by_id/<int:question_id>/', views.get_question_by_id, name='get_question_by_id'),
    path("question_performance/", views.question_performance, name="question_performance"), 
    path("delete_questions_by_batch/<str:batch_id>/", views.delete_questions_by_batch, name="delete_questions_by_batch"),
]
