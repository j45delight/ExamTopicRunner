import random
import json
import pandas as pd
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.db.models import Count, Sum, F
from .models import Question, UserResponse, QuizHistory
from urllib.parse import urlparse, parse_qs
import uuid
from django.contrib import messages
#import pprint

def upload_file(request):
    if request.method == "POST" and request.FILES["excel_file"]:
        # POSTデータからsubjectを取り出す
        subject = request.POST.get("subject")
        
        excel_file = request.FILES["excel_file"]
        fs = FileSystemStorage()
        file_name = fs.save(excel_file.name, excel_file)
        file_path = fs.path(file_name)

        # インポート単位のバッチIDを作成
        batch_id = str(uuid.uuid4())

        # Excelのデータを読み取る (ヘッダーなしで、カラム名を明示的に指定)
        df = pd.read_excel(file_path, header=None, usecols=[0, 1, 2, 3, 4])

        # 手動でカラム名を設定 (Excelの1行目を無視)
        df.columns = ["#","number", "question_text", "choices_raw", "correct_answers"]

        # 1行目 (ヘッダー行) をスキップ
        df = df.iloc[1:].reset_index(drop=True)

        # デバッグ: 先頭5行を表示してカラムのズレを確認
        print("Excel Data Preview:\n", df.head())

        for _, row in df.iterrows():
            try:
                # ここでデータが正しく取れているか確認
                print(f"🔍 Row Data: {row.to_list()}")  

                # subject = "Unknown" はもういらん。POSTから取得したsubjectを使う
                number = row["number"]  # 問題番号
                question_text = str(row["question_text"]).strip()  # 問題文
                choices_raw = str(row["choices_raw"]).strip()  # 選択肢 (A. 選択肢1\nB. 選択肢2 ...)
                correct_answers_raw = str(row["correct_answers"]).strip()

                # 問題番号が数値であることを保証
                try:
                    number = int(float(number))  # "145.0" のような場合にも対応
                except ValueError:
                    print(f"⚠️ Skipping row due to invalid number: {number}")
                    continue

                # 選択肢を辞書に変換 (改行対応)
                choices_dict = {}
                for opt in choices_raw.split("\n"):
                    if "." in opt:
                        key, value = opt.split(".", 1)
                        choices_dict[key.strip().upper()] = value.strip()

                # 正解のリストを作成
                correct_answers = [
                    ans.strip().upper() for ans in correct_answers_raw.split(",") if ans.strip()
                ]

                # デバッグ用ログ
                print(f"📌 Number: {number}, Question: {question_text}, Choices: {choices_dict}, Answer: {correct_answers}")

                # 各問題に batch_id をセット
                Question.objects.create(
                    subject=subject,
                    number=number,
                    question_text=question_text,
                    choices=choices_dict,
                    correct_answers=correct_answers,
                    batch_id=batch_id  # インポートごとに同じ batch_id をセット
                )
            except Exception as e:
                print(f"❌ Error processing row: {row.to_list()} - {e}")

        return redirect("select_subject")  # アップロード後に科目選択画面に遷移
    return render(request, "upload.html")


# ランダムな問題を取得
def get_random_question(request, subject):
    questions = Question.objects.filter(subject=subject)
    if not questions.exists():
        return JsonResponse({"error": "No questions found for this subject"}, status=404)

    question = random.choice(questions)
    return JsonResponse({
        "id": question.id,
        "question_text": question.question_text,
        "choices": question.choices
    })

# 回答のチェック
def submit_answer(request):
    """回答を送信する処理"""
    if request.method == "POST":
        question_id = request.POST.get("question_id")
        selected_answers = request.POST.getlist("answers")

        question = Question.objects.get(id=question_id)
        is_correct = set(selected_answers) == set(question.correct_answers)

        history_id = request.POST.get("history_id")  # 履歴IDを取得
        history = QuizHistory.objects.filter(id=history_id).first()

        if history:  # ✅ 履歴が存在する場合のみ記録
            UserResponse.objects.create(
                quiz_history=history,
                question=question,
                selected_answers=selected_answers,
                is_correct=is_correct
            )

        return JsonResponse({"is_correct": is_correct})

    return JsonResponse({"error": "Invalid request"}, status=400)

def quiz_page(request, subject, history_id):
    return render(request, 'quiz.html', {'subject': subject, 'history_id': history_id})


# ユーザーの回答履歴表示
def history(request):
    histories = QuizHistory.objects.all().order_by("timestamp")  # 🔄 古い順

    # 各履歴ごとの正解数と解答数を計算
    history_data = []
    for history in histories:
        responses = UserResponse.objects.filter(quiz_history=history)
        total_questions = responses.count()
        correct_answers = responses.filter(is_correct=True).count()
        accuracy = round((correct_answers / total_questions * 100), 1) if total_questions > 0 else 0

        history_data.append({
            "id": history.id,
            "timestamp": history.timestamp,
            "subject": history.subject,
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "accuracy": accuracy
        })

    return render(request, "history.html", {"histories": history_data})
'''
def select_subject(request):
    """科目選択画面（アップロード済み問題リストも表示）"""
    subjects = Question.objects.values_list("subject", flat=True).distinct()

    # ✅ `batch_id` ごとの問題数を取得
    batch_list = Question.objects.values("batch_id", "subject").annotate(question_count=Count("id"))

    return render(request, "select_subject.html", {"subjects": subjects, "batch_list": batch_list})
'''
def select_subject(request):
    """科目選択画面（アップロード済み問題リストも表示）"""
    # subjectごとに問題数をカウント
    subjects = (
        Question.objects
        .values('subject')
        .annotate(total_questions=Count('id'))
        .order_by('subject')
    )

    # ✅ `batch_id` ごとの問題数を取得
    batch_list = (
        Question.objects
        .values('batch_id', 'subject')
        .annotate(question_count=Count('id'))
        .order_by('subject')
    )

    return render(request, "select_subject.html", {
        "subjects": subjects,
        "batch_list": batch_list
    })


def quiz_page(request, subject, history_id):
    quiz_questions = request.session.get("quiz_questions", [])
    show_feedback = request.session.get("show_feedback", "yes")  # デフォルトは表示
    mode = request.GET.get("mode")  # ✅ GETリクエストから取得
    if mode:  # ✅ mode が None でなければセッションに保存
        request.session["mode"] = mode
    mode = request.session.get("mode", "random")  # ✅ セッションから取得
    print("Show feedback", show_feedback)  # ✅ セッションに保存されたか確認

    return render(request, "quiz.html", {
        "subject": subject,
        "history_id": history_id,
        "quiz_questions_json": json.dumps(quiz_questions),
        "show_feedback": show_feedback,
        "mode": mode  # ✅ モードをテンプレートに渡す
    })

def start_quiz(request):
    subject = request.GET.get("subject")
    num_questions = request.GET.get("num_questions", "all")
    mode = request.GET.get("mode", "random")  # ✅ デフォルトはランダムモード
    show_feedback = request.GET.get("show_feedback", "yes")

    if not subject:
        return redirect("select_subject")

    # ✅ 途中から再開のため、前回の `history_id` を取得
    last_history = QuizHistory.objects.filter(subject=subject).order_by("-timestamp").first()

    if mode == "sequential" and last_history:
        # ✅ 途中から再開: まだ解いていない問題を取得
        answered_question_ids = UserResponse.objects.filter(quiz_history=last_history).values_list("question_id", flat=True)
        remaining_questions = Question.objects.filter(subject=subject).exclude(id__in=answered_question_ids)
        
        if remaining_questions.exists():
            selected_questions = list(remaining_questions)[:int(num_questions)]
            quiz_history = last_history  # 既存の履歴を使う
        else:
            # ✅ すべて解き終わったら新しい履歴を作成
            selected_questions = list(Question.objects.filter(subject=subject)[:int(num_questions)])
            quiz_history = QuizHistory.objects.create(subject=subject)
    else:
        # ✅ ランダムモード: 毎回ランダムに出題
        questions = list(Question.objects.filter(subject=subject))
        selected_questions = random.sample(questions, min(int(num_questions), len(questions)))
        quiz_history = QuizHistory.objects.create(subject=subject)

    # ✅ 出題する問題のIDリストをセッションに保存
    request.session["quiz_questions"] = [q.id for q in selected_questions]
    request.session["show_feedback"] = show_feedback
    request.session["quiz_history_id"] = quiz_history.id  # ✅ 履歴IDを保存
    request.session["mode"] = mode

    return redirect("quiz_page", subject=subject, history_id=quiz_history.id)

def history_detail(request, history_id):
    history = QuizHistory.objects.get(id=history_id)
    responses = UserResponse.objects.filter(quiz_history=history)

    return render(request, "history_detail.html", {"history": history, "responses": responses})

def get_question_by_id(request, question_id):
    question = Question.objects.get(id=question_id)
    return JsonResponse({
        "id": question.id,
        "question_text": question.question_text,
        "choices": question.choices,
        "correct_answers": question.correct_answers,
    })

def question_performance(request):
    subjects = Question.objects.values_list("subject", flat=True).distinct()

    # フォームから選択された科目
    selected_subject = request.GET.get("subject", subjects[0] if subjects else None)

    # 選択された科目の全設問を取得
    questions = Question.objects.filter(subject=selected_subject)

    performance_data = []
    for question in questions:
        # ✅ 過去の解答履歴を取得（新しい順）
        user_responses = UserResponse.objects.filter(question=question).order_by('-timestamp')[:3]
        
        # ✅ 直近の3回分の結果を取得（なければ '-' にする）
        latest = "〇" if len(user_responses) > 0 and user_responses[0].is_correct else "×" if len(user_responses) > 0 else "-"
        second_last = "〇" if len(user_responses) > 1 and user_responses[1].is_correct else "×" if len(user_responses) > 1 else "-"
        third_last = "〇" if len(user_responses) > 2 and user_responses[2].is_correct else "×" if len(user_responses) > 2 else "-"

        # ✅ レンダリング用データ作成
        performance_data.append({
            "number": question.number,
            "question_text": question.question_text,
            "choices": question.choices,
            "correct_answers": question.correct_answers,
            "latest": latest,
            "second_last": second_last,
            "third_last": third_last,
        })

    return render(request, "question_performance.html", {
        "subjects": Question.objects.values_list("subject", flat=True).distinct(),
        "selected_subject": selected_subject,
        "performance_data": performance_data,
    })

def end_quiz(request, history_id):
    """クイズを終了する際の処理（1問も解いていない場合は履歴を削除）"""
    history = QuizHistory.objects.get(id=history_id)
    responses_count = UserResponse.objects.filter(quiz_history=history).count()

    if responses_count == 0:
        history.delete()  # ✅ 1問も解いていない場合は履歴を削除
        messages.info(request, "クイズを1問も解いていないため、履歴を保存しませんでした。")

    return redirect("/")


def delete_questions_by_batch(request, batch_id):
    """指定された batch_id の問題を削除"""
    if request.method == "POST":
        deleted_count, _ = Question.objects.filter(batch_id=batch_id).delete()
        messages.success(request, f"{deleted_count} 件の問題を削除しました！")

    return redirect("select_subject")