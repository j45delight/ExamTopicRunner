from django.contrib import admin
from .models import Question, UserResponse, QuizHistory

class QuestionAdmin(admin.ModelAdmin):
    list_display = ("subject", "number", "question_text")  # ✅ 科目、番号、問題文を表示
    search_fields = ("subject", "question_text")  # ✅ 検索機能追加

admin.site.register(Question, QuestionAdmin)
admin.site.register(UserResponse)
admin.site.register(QuizHistory)
