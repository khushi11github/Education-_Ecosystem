from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime

from .models import (
    Profile, Course, Lesson, Assignment, Submission,
    ComplianceReport, Feedback, Announcement, Attendance, ConductReport
)
from .forms import (
    UserRegisterForm, ProfileForm, AdminUserCreateForm, CourseForm,
    LessonForm, AssignmentForm, SubmissionForm, GradingForm,
    ComplianceReportForm, FeedbackForm, FeedbackResponseForm,
    AnnouncementForm, AttendanceForm, ConductReportForm, CourseEnrollmentForm
)


# ============================================
# AUTHENTICATION VIEWS
# ============================================

def register_view(request):
    """User registration"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    """User login with role-based redirection"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'registration/login.html')


@login_required
def logout_view(request):
    """User logout"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


# ============================================
# DASHBOARD VIEWS (Role-based)
# ============================================

@login_required
def dashboard_view(request):
    """Role-based dashboard redirection"""
    # Ensure user has a profile (create if missing)
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        # Create profile for users without one (e.g., superusers created via createsuperuser)
        profile = Profile.objects.create(
            user=request.user,
            role='admin' if request.user.is_superuser else 'student'
        )
        messages.info(request, 'Profile created. Please update your settings.')
    
    user_role = profile.role
    
    if user_role == 'admin':
        return redirect('dashboard_admin')
    elif user_role == 'teacher':
        return redirect('dashboard_teacher')
    elif user_role == 'student':
        return redirect('dashboard_student')
    elif user_role == 'parent':
        return redirect('dashboard_parent')
    else:
        messages.error(request, 'Invalid user role.')
        return redirect('login')


@login_required
def dashboard_admin(request):
    """Admin Dashboard - Redirect to Django Admin Panel"""
    # Ensure profile exists
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={'role': 'admin' if request.user.is_superuser else 'student'}
    )
    
    if profile.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard')
    
    # Redirect admins to the built-in Django admin panel
    messages.info(request, 'Welcome Admin! Redirecting to the administration panel.')
    return redirect('/admin/')


@login_required
def dashboard_teacher(request):
    """Teacher Dashboard - Enhanced with detailed statistics"""
    if request.user.profile.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('dashboard')
    
    # Get teacher's courses
    courses = Course.objects.filter(teacher=request.user)
    
    # Count lessons created
    total_lessons = Lesson.objects.filter(course__in=courses).count()
    
    # Get assignments and submissions
    assignments = Assignment.objects.filter(created_by=request.user)
    all_submissions = Submission.objects.filter(assignment__in=assignments)
    pending_submissions = all_submissions.filter(status='pending')[:10]  # Limit to 10 most recent
    graded_submissions = all_submissions.filter(status='graded')
    
    # Get recent feedback
    feedbacks = Feedback.objects.filter(category='course')[:5]
    
    # Get total enrolled students across all courses
    total_students = User.objects.filter(
        courses_enrolled__in=courses,
        profile__role='student'
    ).distinct().count()
    
    # Get recent attendance records
    from datetime import timedelta
    from django.utils import timezone
    week_ago = timezone.now() - timedelta(days=7)
    recent_attendance = Attendance.objects.filter(
        course__in=courses,
        date__gte=week_ago
    ).select_related('student', 'course').order_by('-date')[:10]
    
    # Get active announcements created by teacher
    teacher_announcements = Announcement.objects.filter(
        created_by=request.user,
        is_active=True
    ).order_by('-created_at')[:5]
    
    # Calculate attendance statistics
    total_attendance_records = Attendance.objects.filter(course__in=courses).count()
    present_count = Attendance.objects.filter(course__in=courses, status='present').count()
    absent_count = Attendance.objects.filter(course__in=courses, status='absent').count()
    late_count = Attendance.objects.filter(course__in=courses, status='late').count()
    
    # Calculate attendance percentage
    attendance_percentage = round((present_count / total_attendance_records * 100), 1) if total_attendance_records > 0 else 0
    
    context = {
        'courses': courses,
        'total_lessons': total_lessons,
        'assignments': assignments,
        'total_assignments': assignments.count(),
        'pending_submissions': pending_submissions,
        'pending_count': all_submissions.filter(status='pending').count(),
        'graded_submissions': graded_submissions,
        'graded_count': graded_submissions.count(),
        'total_students': total_students,
        'feedbacks': feedbacks,
        'recent_attendance': recent_attendance,
        'teacher_announcements': teacher_announcements,
        'attendance_percentage': attendance_percentage,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'total_attendance_records': total_attendance_records,
    }
    return render(request, 'dashboard_teacher.html', context)


@login_required
def dashboard_student(request):
    """Student Dashboard"""
    if request.user.profile.role != 'student':
        messages.error(request, 'Access denied. Students only.')
        return redirect('dashboard')
    
    enrolled_courses = request.user.courses_enrolled.all()
    my_submissions = Submission.objects.filter(student=request.user)
    pending_assignments = Assignment.objects.filter(
        course__in=enrolled_courses
    ).exclude(
        submissions__student=request.user
    )
    conduct_reports = ConductReport.objects.filter(student=request.user)
    announcements = Announcement.objects.filter(is_active=True)[:5]
    
    context = {
        'enrolled_courses': enrolled_courses,
        'my_submissions': my_submissions,
        'pending_assignments': pending_assignments,
        'conduct_reports': conduct_reports,
        'announcements': announcements,
        'profile': request.user.profile,
    }
    return render(request, 'dashboard_student.html', context)


@login_required
def dashboard_parent(request):
    """Parent Dashboard"""
    if request.user.profile.role != 'parent':
        messages.error(request, 'Access denied. Parents only.')
        return redirect('dashboard')
    
    linked_student = request.user.profile.linked_student
    student_courses = None
    student_submissions = None
    conduct_reports = None
    
    if linked_student:
        student_courses = linked_student.courses_enrolled.all()
        student_submissions = Submission.objects.filter(student=linked_student)
        conduct_reports = ConductReport.objects.filter(student=linked_student)
    
    context = {
        'linked_student': linked_student,
        'student_courses': student_courses,
        'student_submissions': student_submissions,
        'conduct_reports': conduct_reports,
    }
    return render(request, 'dashboard_parent.html', context)


# ============================================
# USER MANAGEMENT (Admin Only)
# ============================================

@login_required
def user_list(request):
    """List all users (Admin only)"""
    if request.user.profile.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    users = User.objects.select_related('profile').all()
    return render(request, 'user_list.html', {'users': users})


@login_required
def user_create(request):
    """Create new user (Admin only)"""
    if request.user.profile.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AdminUserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('user_list')
    else:
        form = AdminUserCreateForm()
    
    return render(request, 'user_form.html', {'form': form, 'title': 'Create User'})


@login_required
def user_edit(request, user_id):
    """Edit user (Admin only)"""
    if request.user.profile.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, request.FILES, instance=user.profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('user_list')
    else:
        profile_form = ProfileForm(instance=user.profile)
    
    return render(request, 'user_edit.html', {
        'user': user,
        'profile_form': profile_form,
    })


@login_required
def user_delete(request, user_id):
    """Delete user (Admin only)"""
    if request.user.profile.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully!')
        return redirect('user_list')
    
    return render(request, 'user_confirm_delete.html', {'user': user})


# ============================================
# COURSE MANAGEMENT
# ============================================

@login_required
def course_list(request):
    """List all courses"""
    courses = Course.objects.all()
    return render(request, 'course_list.html', {'courses': courses})


@login_required
def course_create(request):
    """Create course (Admin/Teacher)"""
    if request.user.profile.role not in ['admin', 'teacher']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course {course.title} created successfully!')
            return redirect('course_list')
    else:
        form = CourseForm()
    
    return render(request, 'course_form.html', {'form': form, 'title': 'Create Course'})


@login_required
def course_detail(request, course_id):
    """View course details"""
    course = get_object_or_404(Course, id=course_id)
    lessons = course.lessons.all()
    assignments = course.assignments.all()
    students = course.students.all()
    
    context = {
        'course': course,
        'lessons': lessons,
        'assignments': assignments,
        'students': students,
    }
    return render(request, 'course_detail.html', context)


@login_required
def course_enroll(request, course_id):
    """Enroll students in course (Admin/Teacher) - Redirect to course detail"""
    if request.user.profile.role not in ['admin', 'teacher']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = CourseEnrollmentForm(request.POST)
        if form.is_valid():
            students = form.cleaned_data['students']
            course.students.set(students)
            messages.success(request, 'Students enrolled successfully!')
            return redirect('course_detail', course_id=course.id)
    
    # Redirect to course detail page with info message
    messages.info(request, 'Please manage student enrollment from the course detail page.')
    return redirect('course_detail', course_id=course.id)


@login_required
def course_edit(request, course_id):
    """Edit course (Admin/Teacher)"""
    if request.user.profile.role not in ['admin', 'teacher']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    course = get_object_or_404(Course, id=course_id)
    
    # Teachers can only edit their own courses
    if request.user.profile.role == 'teacher' and course.teacher != request.user:
        messages.error(request, 'You can only edit your own courses.')
        return redirect('course_list')
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Course {course.title} updated successfully!')
            return redirect('course_detail', course_id=course.id)
    else:
        form = CourseForm(instance=course)
    
    return render(request, 'course_form.html', {'form': form, 'title': 'Edit Course', 'course': course})


@login_required
def course_delete(request, course_id):
    """Delete course (Admin/Teacher)"""
    if request.user.profile.role not in ['admin', 'teacher']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    course = get_object_or_404(Course, id=course_id)
    
    # Teachers can only delete their own courses
    if request.user.profile.role == 'teacher' and course.teacher != request.user:
        messages.error(request, 'You can only delete your own courses.')
        return redirect('course_list')
    
    if request.method == 'POST':
        course_title = course.title
        course.delete()
        messages.success(request, f'Course {course_title} deleted successfully!')
        return redirect('course_list')
    
    return render(request, 'course_confirm_delete.html', {'course': course})


# ============================================
# LESSON MANAGEMENT
# ============================================

@login_required
def lesson_create(request, course_id):
    """Create lesson (Teacher/Admin)"""
    if request.user.profile.role not in ['admin', 'teacher']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save()
            messages.success(request, f'Lesson {lesson.title} created successfully!')
            return redirect('course_detail', course_id=course.id)
    else:
        form = LessonForm(initial={'course': course})
    
    return render(request, 'lesson_form.html', {'form': form, 'course': course})


@login_required
def lesson_detail(request, lesson_id):
    """View lesson details"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render(request, 'lesson_detail.html', {'lesson': lesson})


@login_required
def lesson_edit(request, lesson_id):
    """Edit lesson (Teacher/Admin)"""
    if request.user.profile.role not in ['admin', 'teacher']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    # Teachers can only edit lessons from their courses
    if request.user.profile.role == 'teacher' and lesson.course.teacher != request.user:
        messages.error(request, 'You can only edit lessons from your own courses.')
        return redirect('course_detail', course_id=lesson.course.id)
    
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, f'Lesson {lesson.title} updated successfully!')
            return redirect('course_detail', course_id=lesson.course.id)
    else:
        form = LessonForm(instance=lesson)
    
    return render(request, 'lesson_form.html', {'form': form, 'lesson': lesson, 'course': lesson.course})


@login_required
def lesson_delete(request, lesson_id):
    """Delete lesson (Teacher/Admin)"""
    if request.user.profile.role not in ['admin', 'teacher']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course_id = lesson.course.id
    
    # Teachers can only delete lessons from their courses
    if request.user.profile.role == 'teacher' and lesson.course.teacher != request.user:
        messages.error(request, 'You can only delete lessons from your own courses.')
        return redirect('course_detail', course_id=course_id)
    
    if request.method == 'POST':
        lesson_title = lesson.title
        lesson.delete()
        messages.success(request, f'Lesson {lesson_title} deleted successfully!')
        return redirect('course_detail', course_id=course_id)
    
    return render(request, 'lesson_confirm_delete.html', {'lesson': lesson})


# ============================================
# ASSIGNMENT & SUBMISSION
# ============================================

@login_required
def assignment_create(request, course_id):
    """Create assignment (Teacher/Admin)"""
    if request.user.profile.role not in ['admin', 'teacher']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.created_by = request.user
            assignment.save()
            messages.success(request, f'Assignment {assignment.title} created successfully!')
            return redirect('course_detail', course_id=course.id)
    else:
        form = AssignmentForm(initial={'course': course})
    
    return render(request, 'assignment_form.html', {'form': form, 'course': course})


@login_required
def assignment_detail(request, assignment_id):
    """View assignment details"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submissions = assignment.submissions.all()
    
    # Check if current user has submitted
    user_submission = None
    if request.user.profile.role == 'student':
        user_submission = submissions.filter(student=request.user).first()
    
    context = {
        'assignment': assignment,
        'submissions': submissions,
        'user_submission': user_submission,
    }
    return render(request, 'assignment_detail.html', context)


@login_required
def submission_create(request, assignment_id):
    """Submit assignment (Student)"""
    if request.user.profile.role != 'student':
        messages.error(request, 'Access denied. Students only.')
        return redirect('dashboard')
    
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # Check if already submitted
    existing = Submission.objects.filter(assignment=assignment, student=request.user).first()
    if existing:
        messages.warning(request, 'You have already submitted this assignment.')
        return redirect('assignment_detail', assignment_id=assignment.id)
    
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.student = request.user
            submission.save()
            messages.success(request, 'Assignment submitted successfully!')
            return redirect('assignment_detail', assignment_id=assignment.id)
    else:
        form = SubmissionForm()
    
    return render(request, 'submission_form.html', {'form': form, 'assignment': assignment})


@login_required
def submission_grade(request, submission_id):
    """Grade submission (Teacher)"""
    if request.user.profile.role not in ['admin', 'teacher']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    submission = get_object_or_404(Submission, id=submission_id)
    
    if request.method == 'POST':
        form = GradingForm(request.POST, instance=submission)
        if form.is_valid():
            graded_submission = form.save(commit=False)
            graded_submission.graded_by = request.user
            graded_submission.graded_at = timezone.now()
            graded_submission.save()
            messages.success(request, 'Submission graded successfully!')
            return redirect('assignment_detail', assignment_id=submission.assignment.id)
    else:
        form = GradingForm(instance=submission)
    
    return render(request, 'submission_grade.html', {'form': form, 'submission': submission})


# ============================================
# COMPLIANCE REPORTS (Admin)
# ============================================

@login_required
def compliance_list(request):
    """List compliance reports (Admin)"""
    if request.user.profile.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    reports = ComplianceReport.objects.all()
    return render(request, 'compliance_list.html', {'reports': reports})


@login_required
def compliance_create(request):
    """Create compliance report (Admin)"""
    if request.user.profile.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ComplianceReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reported_by = request.user
            report.save()
            messages.success(request, 'Compliance report created successfully!')
            return redirect('compliance_list')
    else:
        form = ComplianceReportForm()
    
    return render(request, 'compliance_form.html', {'form': form})


# ============================================
# FEEDBACK SYSTEM
# ============================================

@login_required
def feedback_list(request):
    """List all feedback"""
    if request.user.profile.role == 'admin':
        feedbacks = Feedback.objects.all()
    else:
        feedbacks = Feedback.objects.filter(submitted_by=request.user)
    
    return render(request, 'feedback_list.html', {'feedbacks': feedbacks})


@login_required
def feedback_create(request):
    """Submit feedback"""
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.submitted_by = request.user
            feedback.save()
            messages.success(request, 'Feedback submitted successfully!')
            return redirect('feedback_list')
    else:
        form = FeedbackForm()
    
    return render(request, 'feedback_form.html', {'form': form})


@login_required
def feedback_respond(request, feedback_id):
    """Respond to feedback (Admin/Teacher)"""
    if request.user.profile.role not in ['admin', 'teacher']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    feedback = get_object_or_404(Feedback, id=feedback_id)
    
    if request.method == 'POST':
        form = FeedbackResponseForm(request.POST, instance=feedback)
        if form.is_valid():
            response = form.save(commit=False)
            response.responded_by = request.user
            response.responded_at = timezone.now()
            response.save()
            messages.success(request, 'Response submitted successfully!')
            return redirect('feedback_list')
    else:
        form = FeedbackResponseForm(instance=feedback)
    
    return render(request, 'feedback_response.html', {'form': form, 'feedback': feedback})


# ============================================
# PROFILE SETTINGS
# ============================================

@login_required
def profile_settings(request):
    """User profile settings"""
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard')
    else:
        form = ProfileForm(instance=request.user.profile)
    
    return render(request, 'profile_settings.html', {'form': form})


# AJAX Endpoints for Accessibility Settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

@login_required
@require_POST
def update_font_size(request):
    """Update user's font size preference via AJAX"""
    try:
        data = json.loads(request.body)
        font_size = data.get('font_size')
        
        if font_size in ['small', 'medium', 'large']:
            request.user.profile.font_size = font_size
            request.user.profile.save()
            return JsonResponse({'success': True, 'message': 'Font size updated'})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid font size'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def update_high_contrast(request):
    """Update user's high contrast mode via AJAX"""
    try:
        data = json.loads(request.body)
        high_contrast = data.get('high_contrast', False)
        
        request.user.profile.high_contrast_mode = high_contrast
        request.user.profile.save()
        return JsonResponse({'success': True, 'message': 'High contrast mode updated'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ============================================
# ATTENDANCE MANAGEMENT
# ============================================

@login_required
def attendance_list(request):
    """List attendance records"""
    if request.user.profile.role not in ['admin', 'teacher']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    from datetime import date as date_module
    
    # Get filter parameters
    course_id = request.GET.get('course')
    date_filter = request.GET.get('date')
    status_filter = request.GET.get('status')
    
    # If no date filter is provided, default to today
    if not date_filter or date_filter == '':
        date_filter = date_module.today().isoformat()
    
    # Base queryset
    if request.user.profile.role == 'admin':
        attendance_records = Attendance.objects.all()
        courses = Course.objects.all()
    else:
        attendance_records = Attendance.objects.filter(course__teacher=request.user)
        courses = Course.objects.filter(teacher=request.user)
    
    # Always apply date filter (defaults to today)
    attendance_records = attendance_records.filter(date=date_filter)
    
    # Apply other filters
    if course_id:
        attendance_records = attendance_records.filter(course_id=course_id)
    if status_filter:
        attendance_records = attendance_records.filter(status=status_filter)
    
    attendance_records = attendance_records.select_related('student', 'course', 'marked_by').order_by('-date', 'student__first_name')
    
    context = {
        'attendance_records': attendance_records,
        'courses': courses,
        'selected_date': date_filter,
        'today': date_module.today().isoformat(),
    }
    return render(request, 'attendance_list.html', context)


@login_required
def attendance_mark(request):
    """Mark attendance for students"""
    if request.user.profile.role not in ['admin', 'teacher']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get courses
    if request.user.profile.role == 'admin':
        courses = Course.objects.all()
    else:
        courses = Course.objects.filter(teacher=request.user)
    
    if request.method == 'POST':
        course_id = request.POST.get('course')
        date = request.POST.get('date')
        
        course = get_object_or_404(Course, id=course_id)
        students = course.students.all()
        
        # Check if attendance already exists for this course and date
        existing_count = Attendance.objects.filter(
            course=course,
            date=date
        ).count()
        
        updated_count = 0
        created_count = 0
        
        # Mark attendance for each student
        for student in students:
            status = request.POST.get(f'status_{student.id}')
            remarks = request.POST.get(f'remarks_{student.id}', '')
            
            if status:
                # Check if attendance already exists
                attendance, created = Attendance.objects.get_or_create(
                    student=student,
                    course=course,
                    date=date,
                    defaults={
                        'status': status,
                        'remarks': remarks,
                        'marked_by': request.user
                    }
                )
                
                # Update if already exists
                if not created:
                    attendance.status = status
                    attendance.remarks = remarks
                    attendance.marked_by = request.user
                    attendance.save()
                    updated_count += 1
                else:
                    created_count += 1
        
        if updated_count > 0:
            messages.warning(request, f'Attendance updated for {course.course_code}! {updated_count} records were updated, {created_count} new records created.')
        else:
            messages.success(request, f'Attendance marked successfully for {course.course_code}! {created_count} records created.')
        
        return redirect('attendance_list')
    
    from datetime import date as date_module
    context = {
        'courses': courses,
        'today': date_module.today().isoformat()
    }
    return render(request, 'attendance_mark.html', context)


# ============================================
# ANNOUNCEMENTS
# ============================================

@login_required
def announcement_list(request):
    """List announcements"""
    user_role = request.user.profile.role
    
    # Filter announcements based on target roles
    if user_role == 'admin':
        announcements = Announcement.objects.all()
    else:
        announcements = Announcement.objects.filter(
            Q(target_roles='all') | Q(target_roles__icontains=user_role),
            is_active=True
        )
    
    announcements = announcements.select_related('created_by').order_by('-created_at')
    
    return render(request, 'announcement_list.html', {'announcements': announcements})


@login_required
def announcement_create(request):
    """Create new announcement"""
    if request.user.profile.role not in ['admin', 'teacher']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        target_all = request.POST.get('target_all')
        is_active = request.POST.get('is_active') == 'on'
        
        # Determine target roles
        if target_all:
            target_roles = 'all'
        else:
            target_roles_list = request.POST.getlist('target_roles')
            target_roles = ','.join(target_roles_list) if target_roles_list else 'all'
        
        announcement = Announcement.objects.create(
            title=title,
            content=content,
            target_roles=target_roles,
            is_active=is_active,
            created_by=request.user
        )
        
        messages.success(request, 'Announcement created successfully!')
        return redirect('announcement_list')
    
    return render(request, 'announcement_form.html')


@login_required
def announcement_edit(request, announcement_id):
    """Edit announcement"""
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    # Check permission
    if request.user.profile.role not in ['admin'] and announcement.created_by != request.user:
        messages.error(request, 'Access denied.')
        return redirect('announcement_list')
    
    if request.method == 'POST':
        announcement.title = request.POST.get('title')
        announcement.content = request.POST.get('content')
        
        target_all = request.POST.get('target_all')
        if target_all:
            announcement.target_roles = 'all'
        else:
            target_roles_list = request.POST.getlist('target_roles')
            announcement.target_roles = ','.join(target_roles_list) if target_roles_list else 'all'
        
        announcement.is_active = request.POST.get('is_active') == 'on'
        announcement.save()
        
        messages.success(request, 'Announcement updated successfully!')
        return redirect('announcement_list')
    
    return render(request, 'announcement_form.html', {'announcement': announcement})


@login_required
def announcement_delete(request, announcement_id):
    """Delete announcement"""
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    # Check permission
    if request.user.profile.role not in ['admin'] and announcement.created_by != request.user:
        messages.error(request, 'Access denied.')
        return redirect('announcement_list')
    
    announcement.delete()
    messages.success(request, 'Announcement deleted successfully!')
    return redirect('announcement_list')


# ============================================
# API ENDPOINTS
# ============================================

@login_required
def course_students_api(request, course_id):
    """API endpoint to get students in a course"""
    try:
        course = get_object_or_404(Course, id=course_id)
        
        # Check permission
        if request.user.profile.role not in ['admin', 'teacher']:
            return JsonResponse({'error': 'Access denied - insufficient permissions'}, status=403)
        
        if request.user.profile.role == 'teacher' and course.teacher != request.user:
            return JsonResponse({'error': 'Access denied - not your course'}, status=403)
        
        # Get students enrolled in the course
        students = course.students.all().values('id', 'first_name', 'last_name', 'username')
        students_list = list(students)
        
        return JsonResponse({
            'students': students_list,
            'count': len(students_list),
            'course': {
                'id': course.id,
                'title': course.title,
                'code': course.course_code
            }
        })
    except Exception as e:
        return JsonResponse({
            'error': 'Failed to load students',
            'message': str(e)
        }, status=500)


@login_required
def attendance_check_api(request):
    """API endpoint to check if attendance already exists for a course and date"""
    try:
        course_id = request.GET.get('course')
        date = request.GET.get('date')
        
        if not course_id or not date:
            return JsonResponse({'exists': False})
        
        # Check if any attendance record exists for this course and date
        exists = Attendance.objects.filter(
            course_id=course_id,
            date=date
        ).exists()
        
        count = Attendance.objects.filter(
            course_id=course_id,
            date=date
        ).count()
        
        return JsonResponse({
            'exists': exists,
            'count': count
        })
    except Exception as e:
        return JsonResponse({
            'exists': False,
            'error': str(e)
        })

