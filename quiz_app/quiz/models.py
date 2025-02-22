from django.db import models
from django.utils.timezone import now

def create_default_quiz_history():
    history, _ = QuizHistory.objects.get_or_create(subject="Unknown")  # 既にある場合は取得
    return history.id  # ID を返す

class Question(models.Model):
    subject = models.CharField(max_length=255)  # ✅ 科目
    number = models.IntegerField()  # ✅ 問題番号
    question_text = models.TextField()
    choices = models.JSONField()
    correct_answers = models.JSONField()
    batch_id = models.CharField(max_length=255, blank=True, null=True)  # ✅ インポート単位のID

    def __str__(self):
        return f"{self.subject} - Q{self.number}"  # ✅ 科目名 + 問題番号 で表示


class QuizHistory(models.Model):
    subject = models.CharField(max_length=255)  # どの科目を受けたか
    timestamp = models.DateTimeField(default=now)  # 受験日時

    def __str__(self):
        return f"{self.subject} ({self.timestamp.strftime('%Y-%m-%d %H:%M:%S')})"

class UserResponse(models.Model):
    quiz_history = models.ForeignKey(QuizHistory, on_delete=models.CASCADE)  # どの試験に属するか
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answers = models.JSONField()
    is_correct = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)

