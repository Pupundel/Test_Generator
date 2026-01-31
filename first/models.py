from django.db import models
from django.contrib.auth.models import User

class Temp(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='draft')
    current_topic = models.TextField(null=True, blank=True)
    # Храним сам файл для "памяти" между вопросами
    current_file = models.FileField(upload_to='temp_pdfs/', null=True, blank=True)
    current_complexity = models.CharField(max_length=20, default='medium')
    current_type = models.CharField(max_length=20, default='test')
    target_count = models.IntegerField(default=10)
    question_text = models.TextField(null=True, blank=True)
    answers_data = models.JSONField(null=True, blank=True)

class FinalQuestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question_text = models.JSONField(default=list)
    answers_data = models.JSONField(null=True, blank=True)