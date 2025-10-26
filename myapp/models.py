from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


# User Profile Model - Extended User Information
class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    ]
    
    DISABILITY_CHOICES = [
        ('none', 'None'),
        ('visual', 'Visual Impairment'),
        ('hearing', 'Hearing Impairment'),
        ('mobility', 'Mobility Impairment'),
        ('learning', 'Learning Disability'),
        ('multiple', 'Multiple Disabilities'),
    ]
    
    CONTENT_PREFERENCE = [
        ('text', 'Text'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('mixed', 'Mixed'),
    ]
    
    FONT_SIZE_CHOICES = [
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    # Accessibility Fields
    disability_type = models.CharField(max_length=20, choices=DISABILITY_CHOICES, default='none')
    assistance_required = models.TextField(blank=True, null=True, help_text="Describe any special assistance needed")
    preferred_content_format = models.CharField(max_length=10, choices=CONTENT_PREFERENCE, default='mixed')
    high_contrast_mode = models.BooleanField(default=False)
    font_size = models.CharField(max_length=10, choices=FONT_SIZE_CHOICES, default='medium')
    
    # For Parent-Student linking
    linked_student = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                       related_name='parent_link', limit_choices_to={'profile__role': 'student'})
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    class Meta:
        ordering = ['-created_at']


# Course Model
class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught', 
                                limit_choices_to={'profile__role': 'teacher'})
    students = models.ManyToManyField(User, related_name='courses_enrolled', blank=True,
                                      limit_choices_to={'profile__role': 'student'})
    course_code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.course_code} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']


# Lesson Model
class Lesson(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('text', 'Text'),
        ('audio', 'Audio'),
        ('video', 'Video'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField()
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
    
    # File uploads
    text_content = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='lessons/', blank=True, null=True,
                           validators=[FileExtensionValidator(['pdf', 'doc', 'docx', 'txt', 
                                                               'mp3', 'wav', 'mp4', 'avi', 'mov'])])
    video_url = models.URLField(blank=True, null=True, help_text="YouTube or external video URL")
    
    # Sign Language Support
    sign_language_video_url = models.URLField(blank=True, null=True, 
                                              help_text="Sign language interpretation video URL (YouTube/Vimeo)")
    has_sign_language = models.BooleanField(default=False, 
                                            help_text="Check if sign language interpretation is available")
    
    # Accessibility
    alt_text = models.TextField(blank=True, null=True, help_text="Alternative text for screen readers")
    transcript = models.TextField(blank=True, null=True, help_text="Transcript for audio/video content")
    
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.course.course_code} - {self.title}"
    
    class Meta:
        ordering = ['course', 'order', 'created_at']


# Course Material Model - Videos, PDFs, Notes
class CourseMaterial(models.Model):
    MATERIAL_TYPE_CHOICES = [
        ('video', 'Video'),
        ('pdf', 'PDF Document'),
        ('notes', 'Notes/Document'),
        ('presentation', 'Presentation'),
        ('other', 'Other'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPE_CHOICES)
    
    # File upload
    file = models.FileField(upload_to='course_materials/%Y/%m/', 
                           validators=[FileExtensionValidator(['pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx',
                                                               'mp4', 'avi', 'mov', 'wmv', 'mkv', 'webm'])])
    
    # Video-specific fields
    video_url = models.URLField(blank=True, null=True, help_text="YouTube or external video URL")
    duration = models.CharField(max_length=20, blank=True, null=True, help_text="e.g., 15:30")
    
    # Sign Language Support
    sign_language_video_url = models.URLField(blank=True, null=True, 
                                              help_text="Sign language interpretation video URL")
    has_sign_language = models.BooleanField(default=False, 
                                            help_text="Check if sign language interpretation is available")
    
    # Accessibility
    transcript = models.TextField(blank=True, null=True, help_text="Transcript for videos")
    alt_description = models.TextField(blank=True, null=True, help_text="Alternative description")
    
    # Metadata
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_materials')
    file_size = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., 2.5 MB")
    is_downloadable = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.course.course_code} - {self.title} ({self.material_type})"
    
    class Meta:
        ordering = ['course', 'order', '-created_at']


# Assignment Model
class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateTimeField()
    max_marks = models.IntegerField(default=100)
    attachment = models.FileField(upload_to='assignments/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments_created')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.course.course_code} - {self.title}"
    
    class Meta:
        ordering = ['due_date']


# Submission Model
class Submission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('graded', 'Graded'),
    ]
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions',
                                limit_choices_to={'profile__role': 'student'})
    file = models.FileField(upload_to='submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    marks_obtained = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='graded_submissions')
    graded_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"
    
    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['assignment', 'student']


# Compliance Report Model
class ComplianceReport(models.Model):
    STATUS_CHOICES = [
        ('compliant', 'Compliant'),
        ('partial', 'Partially Compliant'),
        ('non_compliant', 'Non-Compliant'),
    ]
    
    institute_name = models.CharField(max_length=200)
    department = models.CharField(max_length=100, blank=True, null=True)
    accessibility_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    compliance_percentage = models.IntegerField(default=0, help_text="Percentage of accessibility achieved (0-100)")
    comments = models.TextField()
    improvement_suggestions = models.TextField(blank=True, null=True)
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compliance_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.institute_name} - {self.accessibility_status}"
    
    class Meta:
        ordering = ['-created_at']


# Feedback Model
class Feedback(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('addressed', 'Addressed'),
    ]
    
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('accessibility', 'Accessibility Issue'),
        ('course', 'Course Related'),
        ('technical', 'Technical Issue'),
        ('suggestion', 'Suggestion'),
        ('other', 'Other'),
    ], default='other')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    response = models.TextField(blank=True, null=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='feedback_responses')
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.submitted_by.username} - {self.subject}"
    
    class Meta:
        ordering = ['-created_at']


# Announcement Model
class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    target_roles = models.CharField(max_length=100, default='all', 
                                    help_text="Comma-separated roles: admin,teacher,student,parent or 'all'")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']


# Attendance Model (Optional)
class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance',
                                limit_choices_to={'profile__role': 'student'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    remarks = models.TextField(blank=True, null=True)
    marked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_marked')
    
    def __str__(self):
        return f"{self.student.username} - {self.course.course_code} - {self.date}"
    
    class Meta:
        ordering = ['-date']
        unique_together = ['student', 'course', 'date']


# Conduct Report Model
class ConductReport(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conduct_reports',
                                limit_choices_to={'profile__role': 'student'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='conduct_reports')
    behavior_rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], 
                                         help_text="1=Poor, 5=Excellent")
    participation_rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)],
                                               help_text="1=Poor, 5=Excellent")
    comments = models.TextField()
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conduct_reports_made')
    date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.username} - {self.course.course_code}"
    
    class Meta:
        ordering = ['-date']
