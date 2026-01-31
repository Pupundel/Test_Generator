import os
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages

from .models import Temp, FinalQuestion
from .gemeni import fetch_ai_question_gemini, fetch_ai_answers_gemini


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('main')
    else:
        form = UserCreationForm()
    return render(request, 'first/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('main')
        else:
            messages.error(request, "Неверный логин или пароль")
    else:
        form = AuthenticationForm()
    return render(request, 'first/login.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    return redirect('login')



@login_required
def main_page(request):
    return render(request, 'first/main.html')











@login_required
def generate_question(request):
    draft, _ = Temp.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        topic = request.POST.get('topic', '').strip()
        if not topic:
            return JsonResponse({'error': 'Тема обязательна для заполнения!'}, status=400)

        pdf_file = request.FILES.get('pdf_file')
        if pdf_file:
            draft.current_file = pdf_file

        draft.current_topic = topic
        draft.current_complexity = request.POST.get('complexity', 'medium')
        draft.current_type = request.POST.get('q_type', 'test')
        try:
            draft.target_count = int(request.POST.get('q_count', 10))
        except:
            draft.target_count = 10
        draft.save()

    final, _ = FinalQuestion.objects.get_or_create(user=request.user)
    exclude_questions = [item['q'] for item in final.question_text if 'q' in item]

    pdf_bytes = None
    if draft.current_file:
        try:
            with draft.current_file.open('rb') as f:
                pdf_bytes = f.read()
        except:
            pdf_bytes = None

    try:
        q_text = fetch_ai_question_gemini(
            draft.current_topic, 
            draft.current_complexity,
            draft.current_type, 
            pdf_bytes,
            exclude_list=exclude_questions[-10:]
        )
        
        draft.question_text = q_text
        draft.answers_data = None
        draft.save()

        return JsonResponse({
            'question': q_text,
            'q_type': draft.current_type,
            'current_number': len(final.question_text) + 1,
            'target_count': draft.target_count
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def generate_answers(request):
    try:
        draft = Temp.objects.get(user=request.user)
        if not draft.question_text:
            return JsonResponse({'error': 'Сначала нужно сгенерировать вопрос!'}, status=400)

        answers = fetch_ai_answers_gemini(draft.question_text)
        
        draft.answers_data = answers
        draft.save()
        
        return JsonResponse({'answers': answers})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@transaction.atomic
def save_to_final(request):
    try:
        draft = Temp.objects.get(user=request.user)
        final, _ = FinalQuestion.objects.get_or_create(user=request.user)

        current_list = list(final.question_text)
        current_list.append({
            'q': draft.question_text,
            'a': draft.answers_data
        })
        final.question_text = current_list
        final.save()

        draft.question_text = None
        draft.answers_data = None
        draft.save()

        return JsonResponse({
            'status': 'success',
            'total_saved': len(current_list),
            'target_count': draft.target_count
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def reset_test(request):
    try:
        FinalQuestion.objects.filter(user=request.user).delete()
        Temp.objects.filter(user=request.user).update(
            question_text=None, 
            answers_data=None
        )
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def download_test_txt(request):
    try:
        final = FinalQuestion.objects.get(user=request.user)
        questions = final.question_text
        if not questions: 
            return HttpResponse("Тест пуст. Сохраните хотя бы один вопрос.")

        content = "ВАШ СГЕНЕРИРОВАННЫЙ ТЕСТ\n" + "="*30 + "\n\n"
        for i, q in enumerate(questions, 1):
            content += f"Вопрос №{i}: {q['q']}\n"
            if q.get('a'):
                for j, ans in enumerate(q['a'], 1):
                    mark = "[V]" if ans['is_correct'] else "[ ]"
                    content += f"  {j}. {mark} {ans['text']}\n"
            content += "\n"

        response = HttpResponse(content, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="my_test.txt"'
        return response
    except Exception:
        return HttpResponse("Ошибка при скачивании файла.")