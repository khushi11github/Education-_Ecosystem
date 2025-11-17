from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import (Profile, Course, Lesson, Assignment, Submission, 
                     Feedback, Announcement, Attendance)


# User Registration Form
class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    role = forms.ChoiceField(
        choices=[
            ('student', 'Student'),
            ('teacher', 'Teacher'),
            ('parent', 'Parent'),
        ],
        required=True,
        help_text="Select your role in the education ecosystem"
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Profile is created by signal, now update it with the selected role
            profile, created = Profile.objects.get_or_create(user=user)
            profile.role = self.cleaned_data['role']
            profile.save()
        return user


# Profile Form
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['role', 'phone', 'address', 'profile_picture', 'linked_student']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['role'].disabled = True


# Course Form
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'teacher', 'course_code', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter to show only teachers
        self.fields['teacher'].queryset = User.objects.filter(profile__role='teacher')


# Lesson Form
class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['course', 'title', 'description', 'content_type', 'text_content', 
                  'video_url', 'file', 'alt_text', 'transcript', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'text_content': forms.Textarea(attrs={'rows': 5}),
            'video_url': forms.URLInput(attrs={'placeholder': 'https://www.youtube.com/watch?v=...'}),
            'alt_text': forms.Textarea(attrs={'rows': 2}),
            'transcript': forms.Textarea(attrs={'rows': 4}),
        }


# Assignment Form
class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['course', 'title', 'description', 'due_date', 'max_marks', 'attachment']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


# Submission Form
class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['file']


# Grading Form
class GradingForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['marks_obtained', 'feedback', 'status']
        widgets = {
            'feedback': forms.Textarea(attrs={'rows': 4}),
        }


# Feedback Form
class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['subject', 'message', 'category']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }


# Feedback Response Form
class FeedbackResponseForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['response', 'status']
        widgets = {
            'response': forms.Textarea(attrs={'rows': 4}),
        }


# Announcement Form
class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'target_roles', 'is_active']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }


# Attendance Form
class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'course', 'date', 'status', 'remarks']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = User.objects.filter(profile__role='student')


# Course Enrollment Form
class CourseEnrollmentForm(forms.Form):
    students = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(profile__role='student'),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
