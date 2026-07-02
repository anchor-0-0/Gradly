from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

from api.views.auth_views import RegisterView, LoginView, ForgotPasswordView, ResetPasswordView
from api.views.student_views import (
    ProjectListView, JoinProjectView, UploadReportView,
    MyReportsView, MyNotificationsView, StudentProjectDashboardView,
    StudentFinalResultView, StudentAnnouncementsView, StudentAttendanceView,
    StudentMyCommitteeView, StudentAttendanceSummaryView, ProfileView,
    StudentProjectDetailView, StudentPendingRequestView, StudentReportDetailView,
    StudentCancelPendingRequestView, PublicDepartmentListView, ValidateEmailView,
)
from api.views.supervisor_views import (
    ApproveJoinRequestView, RejectJoinRequestView,
    SupervisorCreateProject, SupervisorManageProject, SupervisorEvaluateReport,
    AnnouncementCreateView, MarkAttendanceView, SupervisorDashboardView,
    EvaluationViewSet, MyProjectsView, SupervisorProjectDetails,
    PendingJoinRequestsView, AnnouncementListSummaryView,
    AnnouncementDetailWithAttendanceView,
    SupervisorAttendanceSessionsView,
)
from api.views.head_views import (
    DefenseCommitteeViewSet, HeadProjectView, SystemSettingsView,
    HeadProjectDetailsView, DepartmentViewSet,
    HODDashboardView, HODNotificationsView,
)
from api.views.admin_views import AdminDashboardView, AdminUserListView, AdminUserDetailView, AdminCreateUserView, AdminDepartmentListView, AdminCreateDepartmentView, AdminDepartmentDetailView

router = DefaultRouter()
router.register(r'committees', DefenseCommitteeViewSet)
router.register(r'evaluation', EvaluationViewSet)
router.register(r'departments', DepartmentViewSet)

urlpatterns = [
    # Auth
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('api/reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    # Student
    path('api/projects/', ProjectListView.as_view(), name='project-list'),
    path('api/projects/<int:id>/details/', StudentProjectDetailView.as_view(), name='project-details-student'),
    path('api/projects/<int:id>/join/', JoinProjectView.as_view(), name='join-project'),
    path('api/validate-email/', ValidateEmailView.as_view(), name='validate-email'),
    path('api/reports/upload/', UploadReportView.as_view(), name='upload-report'),
    path('api/reports/<int:id>/', StudentReportDetailView.as_view(), name='report-detail'),
    path('api/student/pending-request/', StudentPendingRequestView.as_view(), name='student-pending-request'),
    path('api/student/pending-request/cancel/', StudentCancelPendingRequestView.as_view(), name='student-cancel-pending-request'),
    path('api/student/final_result/', StudentFinalResultView.as_view(), name='student-final-result'),
    path('api/student/announcements/', StudentAnnouncementsView.as_view(), name='student-announcements'),
    path('api/student/attendance/<int:project_id>/', StudentAttendanceView.as_view(), name='student-attendance'),
    path('api/student/my_committee/', StudentMyCommitteeView.as_view(), name='student-my-committee'),
    path('api/student/attendance-summary/', StudentAttendanceSummaryView.as_view(), name='student-attendance-summary'),
    path('student/project_dashboard/', StudentProjectDashboardView.as_view(), name='student-project-dashboard'),
    path('api/profile/', ProfileView.as_view(), name='profile'),
    path('api/admin/dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('api/system-settings/', SystemSettingsView.as_view(), name='system-settings'),
    path('api/announcements/summary/', AnnouncementListSummaryView.as_view(), name='announcement-summary'),
    path('api/announcements/<int:announcement_id>/details/', AnnouncementDetailWithAttendanceView.as_view(), name='announcement-details'),
    path('api/join_request/<int:request_id>/approve/', ApproveJoinRequestView.as_view(), name='approve-join-request'),
    path('api/join_request/<int:request_id>/reject/', RejectJoinRequestView.as_view(), name='reject-join-request'),
    # Supervisor
    path('supervisor/create-project/', SupervisorCreateProject.as_view(), name='supervisor-create-project'),
    path('supervisor/manage-project/<int:pk>/', SupervisorManageProject.as_view(), name='supervisor-manage-project'),
    path('supervisor/evaluate-report/<int:pk>/', SupervisorEvaluateReport.as_view(), name='supervisor-evaluate-report'),
    path('supervisor/dashboard/', SupervisorDashboardView.as_view(), name='supervisor-dashboard'),
    path('announcements/create/', AnnouncementCreateView.as_view(), name='announcement-create'),
    path('announcements/<int:announcement_id>/mark-attendance/', MarkAttendanceView.as_view(), name='mark-attendance'),
    path('my_projects/', MyProjectsView.as_view(), name='my-projects'),
    path('project_details/<int:project_id>/', SupervisorProjectDetails.as_view(), name='project-details'),
    path('api/projects/<int:project_id>/attendance-sessions/', SupervisorAttendanceSessionsView.as_view(), name='supervisor-attendance-sessions'),
    path('my-reports/', MyReportsView.as_view(), name='my-reports'),
    path('my-notifications/', MyNotificationsView.as_view(), name='my-notifications'),
    path('my-notifications/<int:pk>/', MyNotificationsView.as_view(), name='my-notification-detail'),
    path('join_requests/pending/', PendingJoinRequestsView.as_view(), name='pending-join-requests'),
    # Head
    path('head/dashboard/', HODDashboardView.as_view(), name='hod-dashboard'),
    path('head/notifications/', HODNotificationsView.as_view(), name='hod-notifications'),
    path('head/projects/', HeadProjectView.as_view(), name='head-projects'),
    path('head/projects/<int:project_id>/', HeadProjectDetailsView.as_view(), name='head-project-details'),
    # Public departments (for registration)
    path('api/departments/public/', PublicDepartmentListView.as_view(), name='public-departments'),
    # Admin (must be before Django admin site to avoid path conflict)
    path('admin/users/', AdminUserListView.as_view(), name='admin-users'),
    path('admin/users/create/', AdminCreateUserView.as_view(), name='admin-create-user'),
    path('admin/users/<int:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/departments/', AdminDepartmentListView.as_view(), name='admin-departments'),
    path('admin/departments/create/', AdminCreateDepartmentView.as_view(), name='admin-create-department'),
    path('admin/departments/<int:pk>/', AdminDepartmentDetailView.as_view(), name='admin-department-detail'),
    # Django admin (last — its /admin/ prefix would swallow custom admin/ routes if placed above)
    path('admin/', admin.site.urls),
    # Router
    path('', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
