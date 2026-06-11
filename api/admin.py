from django.contrib import admin
from .models import Project, Report, Notification ,Announcement ,Attendance,DefenseCommittee,Evaluation,SystemSettings,Department,UserProfile
admin.site.register(Project)
admin.site.register(Report)
admin.site.register(Notification)
admin.site.register(Announcement)
admin.site.register(Attendance)
admin.site.register(DefenseCommittee)
admin.site.register(Evaluation)
admin.site.register(SystemSettings)
admin.site.register(Department)
admin.site.register(UserProfile)