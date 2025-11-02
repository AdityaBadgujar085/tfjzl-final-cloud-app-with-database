from django.db import models
from django.contrib.auth.models import User
import datetime

# ----- Provided base models (keep these if already present) -----
class Course(models.Model):
    name = models.CharField(null=False, max_length=30, default='online course')
    image = models.ImageField(upload_to='course_images/', null=True)
    description = models.CharField(max_length=1000)
    pub_date = models.DateField(null=True)
    total_enrollment = models.IntegerField(default=0)

    def __str__(self):
        return "Name: " + self.name + ", " + \
               "Description: " + self.description

class Lesson(models.Model):
    title = models.CharField(max_length=200, default="title")
    order = models.IntegerField(default=0)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    content = models.TextField()

class Instructor(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_time = models.BooleanField(default=True)
    total_learners = models.IntegerField()

class Learner(models.Model):
    STUDENT = 'student'
    DEVELOPER = 'developer'
    DATA_SCIENTIST = 'data_scientist'
    DATABASE_ADMIN = 'dba'
    OCCUPATION_CHOICES = [
        (STUDENT, 'Student'),
        (DEVELOPER, 'Developer'),
        (DATA_SCIENTIST, 'Data Scientist'),
        (DATABASE_ADMIN, 'Database Admin')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    occupation = models.CharField(max_length=20, choices=OCCUPATION_CHOICES, default=STUDENT)
    social_link = models.URLField(max_length=200, blank=True)

class Enrollment(models.Model):
    AUDIT = 'audit'
    HONOR = 'honor'
    BETA = 'BETA'
    MODES = [
        (AUDIT, 'Audit'),
        (HONOR, 'Honor'),
        (BETA, 'BETA')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date_enrolled = models.DateField(default=datetime.date.today)
    mode = models.CharField(max_length=5, choices=MODES, default=AUDIT)
    rating = models.FloatField(default=5.0)

# ----- NEW: Exam models -----

class Question(models.Model):
    """
    Question belongs to a Course (Many-to-One),
    has text and a grade (points).
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    question_text = models.TextField()
    grade = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.question_text[:50]}..."

    # method to calculate if the learner gets the score of the question
    def is_get_score(self, selected_ids):
        all_answers = self.choice_set.filter(is_correct=True).count()
        selected_correct = self.choice_set.filter(is_correct=True, id__in=selected_ids).count()
        # To prevent selecting extra wrong answers from passing, also ensure
        # no incorrect choices selected:
        selected_incorrect = self.choice_set.filter(is_correct=False, id__in=selected_ids).count()
        return all_answers == selected_correct and selected_incorrect == 0


class Choice(models.Model):
    """
    Choice belongs to a Question (Many-to-One),
    holds text and whether this choice is correct.
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.choice_text[:50]}..."


class Submission(models.Model):
    """
    Submission belongs to an Enrollment (Many-to-One),
    and links to many selected Choices (Many-to-Many).
    """
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    choices = models.ManyToManyField(Choice)

    def __str__(self):
        return f"Submission #{self.id} (Enrollment #{self.enrollment_id})"
