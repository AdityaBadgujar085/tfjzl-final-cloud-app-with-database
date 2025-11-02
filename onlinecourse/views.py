from django.shortcuts import render
from django.http import HttpResponseRedirect
# <HINT> Import any new Models here
from .models import Course, Enrollment, Question, Choice, Submission
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


# ---- Exam helpers & views ----

def extract_answers(request):
    """
    Collect selected choice IDs from the submitted form.
    Supports multiple checkboxes per question (uses getlist).
    Expects names like 'choice_<question_id>'.
    """
    submitted_answers = []
    for key in request.POST:
        if key.startswith('choice_'):
            # may contain multiple values for this question
            values = request.POST.getlist(key)
            for v in values:
                try:
                    submitted_answers.append(int(v))
                except (TypeError, ValueError):
                    pass
    return submitted_answers


@login_required
def submit(request, course_id):
    """
    Create a Submission for the current user's Enrollment of this Course.
    Attach all selected Choice objects, then redirect to results page.
    """
    course = get_object_or_404(Course, pk=course_id)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)

    # Create submission
    submission = Submission.objects.create(enrollment=enrollment)

    # Collect selected choices
    selected_choice_ids = extract_answers(request)
    if selected_choice_ids:
        choices = Choice.objects.filter(id__in=selected_choice_ids)
        submission.choices.set(choices)

    submission.save()

    return redirect(reverse('onlinecourse:show_exam_result', args=[course.id, submission.id]))


@login_required
def show_exam_result(request, course_id, submission_id):
    """
    Evaluate a submission and render results with per-question feedback.
    Uses Question.is_get_score to decide correctness.
    Pass threshold = 60% (adjust if needed).
    """
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)

    total_points = 0
    earned_points = 0
    question_results = []

    # Build a set of selected Choice IDs for quick lookup
    selected_ids = set(submission.choices.values_list('id', flat=True))

    for question in course.question_set.all():
        total_points += question.grade

        # selected for this question
        q_selected_ids = set(
            submission.choices.filter(question=question).values_list('id', flat=True)
        )

        is_correct = question.is_get_score(q_selected_ids)
        if is_correct:
            earned_points += question.grade

        question_results.append({
            'question': question,
            'selected_choices': Choice.objects.filter(id__in=q_selected_ids),
            'is_correct': is_correct
        })

    score_percent = round((earned_points / total_points) * 100, 2) if total_points else 0.0
    passed = score_percent >= 60

    context = {
        'course': course,
        'submission': submission,
        'question_results': question_results,
        'earned': earned_points,
        'total': total_points,
        'score_percent': score_percent,
        'passed': passed
    }
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)
