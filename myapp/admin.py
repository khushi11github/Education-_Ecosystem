from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.models import User

from .models import (
	Profile, Course, Lesson, Assignment, Submission,
	ComplianceReport, Feedback, Announcement, Attendance, ConductReport, CourseMaterial
)


# Inline Profile inside User admin
class ProfileInline(admin.StackedInline):
	model = Profile
	can_delete = False
	verbose_name_plural = 'profile'
	fk_name = 'user'


# Use Django's default UserAdmin with just the Profile inline
class UserAdmin(DefaultUserAdmin):
	inlines = (ProfileInline,)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
	list_display = ('course_code', 'title', 'teacher', 'is_active', 'created_at')
	list_filter = ('is_active', 'teacher')
	search_fields = ('course_code', 'title', 'teacher__username')
	ordering = ('-created_at',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
	list_display = ('title', 'course', 'content_type', 'order', 'created_at')
	list_filter = ('content_type', 'course')
	search_fields = ('title', 'course__title')
	ordering = ('course', 'order')


@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
	list_display = ('title', 'course', 'material_type', 'uploaded_by', 'is_downloadable', 'created_at')
	list_filter = ('material_type', 'course', 'is_downloadable')
	search_fields = ('title', 'course__title', 'uploaded_by__username')
	ordering = ('course', 'order', '-created_at')
	readonly_fields = ('created_at', 'updated_at')


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
	list_display = ('title', 'course', 'due_date', 'created_by', 'created_at')
	list_filter = ('course', 'created_by')
	search_fields = ('title', 'course__title', 'created_by__username')
	ordering = ('-due_date',)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
	list_display = ('assignment', 'student', 'submitted_at', 'status', 'marks_obtained')
	list_filter = ('status', 'assignment__course')
	search_fields = ('student__username', 'assignment__title')
	readonly_fields = ('submitted_at',)
	actions = ['mark_graded']

	def mark_graded(self, request, queryset):
		updated = queryset.update(status='graded')
		self.message_user(request, f"Marked {updated} submission(s) as graded.")
	mark_graded.short_description = 'Mark selected submissions as graded'


@admin.register(ComplianceReport)
class ComplianceReportAdmin(admin.ModelAdmin):
	list_display = ('institute_name', 'accessibility_status', 'compliance_percentage', 'reported_by', 'created_at')
	list_filter = ('accessibility_status',)
	search_fields = ('institute_name', 'reported_by__username')
	actions = ['mark_compliant']

	def mark_compliant(self, request, queryset):
		updated = queryset.update(accessibility_status='compliant')
		self.message_user(request, f"Marked {updated} report(s) as compliant.")
	mark_compliant.short_description = 'Mark selected reports as compliant'


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
	list_display = ('subject', 'submitted_by', 'category', 'status', 'created_at')
	list_filter = ('status', 'category')
	search_fields = ('subject', 'submitted_by__username', 'message')
	actions = ['mark_addressed']

	def mark_addressed(self, request, queryset):
		updated = queryset.update(status='addressed')
		self.message_user(request, f"Marked {updated} feedback item(s) as addressed.")
	mark_addressed.short_description = 'Mark selected feedback as addressed'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
	list_display = ('title', 'created_by', 'is_active', 'created_at')
	list_filter = ('is_active',)
	search_fields = ('title', 'created_by__username')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
	list_display = ('student', 'course', 'date', 'status', 'marked_by')
	list_filter = ('status', 'course')
	search_fields = ('student__username', 'course__course_code')


@admin.register(ConductReport)
class ConductReportAdmin(admin.ModelAdmin):
	list_display = ('student', 'course', 'behavior_rating', 'participation_rating', 'date')
	list_filter = ('course', 'behavior_rating')
	search_fields = ('student__username', 'course__course_code')


# Re-register UserAdmin to include Profile inline
try:
	admin.site.unregister(User)
except Exception:
	# If User wasn't registered yet, ignore
	pass
admin.site.register(User, UserAdmin)

