from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Avg, Q
from ..models import Project, Report, Notification, JoinRequest, Attendance, DefenseCommittee, UserProfile, SystemSettings
from ..serializers import (
    ProjectSerializer, ReportSerializer, NotificationSerializer,
    JoinRequestSerializer, AnnouncementListSerializer
)


# عرض المشاريع المقترحة (للطلاب) وأيضاً مشاريع المشرف (للمشرف)
# GET /api/projects/
# يدعم البحث والتصفية:
#   ?search=كلمة         للبحث في العنوان والوصف
#   ?supervisor=id        لتصفية حسب المشرف
#   ?status=proposed|in_progress|completed   للتصفية حسب الحالة
#   ?technologies=كلمة    للبحث في التقنيات
class ProjectListView(generics.ListAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            queryset = Project.objects.filter(supervisor=user)
        else:
            queryset = Project.objects.filter(status='proposed')

        # البحث حسب الكلمة المفتاحية
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(technologies__icontains=search)
            )

        # تصفية حسب المشرف
        supervisor_id = self.request.query_params.get('supervisor')
        if supervisor_id:
            queryset = queryset.filter(supervisor_id=supervisor_id)

        # تصفية حسب الحالة
        status_filter = self.request.query_params.get('status')
        if status_filter and status_filter in dict(Project.STATUS_CHOICES):
            queryset = queryset.filter(status=status_filter)

        # تصفية حسب التقنيات
        tech_filter = self.request.query_params.get('technologies')
        if tech_filter:
            queryset = queryset.filter(technologies__icontains=tech_filter)

        return queryset


# انضمام فريق طلاب لمشروع (إرسال إيميلات الفريق)
# POST /api/projects/{id}/join/
# ينشئ طلبات انضمام ويرسل إشعار للمشرف
class JoinProjectView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        project = get_object_or_404(Project, id=id)
        if request.user.is_staff:
            return Response({'error': 'المشرفين لا يمكنهم الانضمام للمشاريع'}, status=status.HTTP_403_FORBIDDEN)
        emails = request.data.get('emails', [])
        # إذا القائمة فاضية، منرجع خطأ
        if not emails:
            return Response({"error": "يرجى إرسال قائمة بإيميلات أعضاء الفريق 📩"}, status=status.HTTP_400_BAD_REQUEST)
        if request.user.email not in emails:
            emails.append(request.user.email)
        emails = list(set(emails))

        # التحقق من وجود إعدادات النظام والسعة المتوفرة
        settings = SystemSettings.objects.first()
        if not settings:
            return Response({"error": "إعدادات النظام غير مهيأة"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if project.students.count() + len(emails) > settings.max_students_per_project:
            return Response({"error": f"لا يمكن إضافة هذا العدد، الحد الأقصى {settings.max_students_per_project} طالب"}, status=status.HTTP_400_BAD_REQUEST)

        # التحقق من وجود مشرف للمشروع (لأنه قد يكون null)
        if not project.supervisor:
            return Response({"error": "المشروع ليس له مشرف حالياً، لا يمكن تقديم طلب"}, status=status.HTTP_400_BAD_REQUEST)

        for email in emails:
            try:
                student_user = User.objects.get(email=email)
                if student_user.student_projects.exists():
                    return Response({"error": f"هذا الحساب {email} بالفعل مسجل في مشروع آخر"}, status=status.HTTP_400_BAD_REQUEST)
                if JoinRequest.objects.filter(project=project, student=student_user).exists():
                    continue
                if project.students.filter(id=student_user.id).exists():
                    continue
                JoinRequest.objects.create(project=project, student=student_user)
            except User.DoesNotExist:
                return Response({"error": f"الإيميل {email} غير موجود في النظام"}, status=status.HTTP_404_NOT_FOUND)

        # إرسال إشعار واحد للمشرف بعد معالجة جميع الطلبات
        Notification.objects.create(
            recipient=project.supervisor,
            project=project,
            message=f"طلب انضمام فريق جديد على مشروع: {project.title}"
        )

        return Response({"message": "تم إرسال طلب الانضمام للمشرف"}, status=status.HTTP_200_OK)
    


# رفع تقرير جديد (للطالب)
# POST /api/reports/upload/
# يرسل إشعار للمشرف بعد الرفع
class UploadReportView(generics.CreateAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        project = serializer.validated_data['project']
        if not project.students.filter(id=self.request.user.id).exists():
            raise PermissionDenied('أنت لست ضمن فريق هذا المشروع')
        report = serializer.save(student=self.request.user)
        Notification.objects.create(
            recipient=project.supervisor,
            project=project,
            message=f"تم رفع تقرير جديد من {self.request.user.username} لمشروع {project.title}"
        )


# تقارير الفريق (كل التيم يشوف كل التقارير + اسم رافع التقرير)
# GET /my-reports/
class MyReportsView(generics.ListAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project = Project.objects.filter(students=self.request.user).first()
        if not project:
            return Report.objects.none()
        return Report.objects.filter(project=project)


# إشعارات المستخدم
# GET /my-notifications/
class MyNotificationsView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')


# الشاشة الرئيسية للطالب (داشبورد)
# GET /student/project_dashboard/
# يعرض: المشروع + شريط التقدم + التقارير المقبولة
class StudentProjectDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        project = Project.objects.filter(students=request.user).first()
        if not project:
            return Response({'error': 'لا يوجد مشروع مسجل لك'}, status=status.HTTP_404_NOT_FOUND)
        accepted_reports = project.reports.filter(status='accepted').count()
        if project.required_reports == 0:
            progress = 0
        else:
            progress = min((accepted_reports / project.required_reports) * 100, 100)
        return Response({
            'project_title': project.title,
            'project_description': project.description,
            'status': project.status,
            'accepted_reports': accepted_reports,
            'total_reports': project.reports.count(),
            'required_reports': project.required_reports,
            'progress': round(progress, 2),
            'supervisor': project.supervisor.username if project.supervisor else None,
        })


# نتيجة الطالب النهائية (بعد اعتماد رئيس القسم)
# GET /api/student/final_result/
class StudentFinalResultView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        project = Project.objects.filter(students=request.user).first()
        if not project:
            return Response({'error': 'لا يوجد مشروع مسجل لك'}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            'project_title': project.title,
            'final_grade': project.final_grade,
            'status': project.status,
        })


# إعلانات المشروع (للطالب - آخر الإعلانات)
# GET /api/student/announcements/
class StudentAnnouncementsView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        projects = Project.objects.filter(students=self.request.user)
        return Notification.objects.filter(project__in=projects).order_by('-created_at')


# سجل حضور الطالب لكل إعلان/اجتماع
# GET /api/student/attendance/{project_id}/
class StudentAttendanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id, students=request.user)
        attendances = Attendance.objects.filter(
            announcement__project=project,
            student=request.user
        )
        data = [
            {
                'announcement_id': a.announcement.id,
                'content': a.announcement.content,
                'meeting_time': a.announcement.meeting_time,
                'is_present': a.is_present,
            }
            for a in attendances
        ]
        return Response(data)


# لجنة المناقشة الخاصة بالطالب
# GET /api/student/my_committee/
# يعرض: أعضاء اللجنة + التاريخ + المكان
class StudentMyCommitteeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        project = Project.objects.filter(students=request.user).first()
        if not project:
            return Response({'error': 'لا يوجد مشروع'}, status=status.HTTP_404_NOT_FOUND)
        try:
            committee = DefenseCommittee.objects.get(project=project)
        except DefenseCommittee.DoesNotExist:
            return Response({'error': 'لم يتم تحديد لجنة مناقشة بعد'}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            'project_title': project.title,
            'date': committee.date,
            'location': committee.location,
            'examiners': [e.username for e in committee.examiners.all()],
            'is_finalized': committee.is_finalized,
        })


# إحصائية حضور الطالب
# GET /api/student/attendance-summary/
# يعرض: مجموع الاجتماعات + حاضر + غايب + نسبة %
class StudentAttendanceSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        projects = Project.objects.filter(students=request.user)
        total = Attendance.objects.filter(announcement__project__in=projects, student=request.user).count()
        present = Attendance.objects.filter(announcement__project__in=projects, student=request.user, is_present=True).count()
        rate = (present / total * 100) if total > 0 else 0
        return Response({
            'total_meetings': total,
            'present': present,
            'absent': total - present,
            'attendance_rate': round(rate, 2),
        })


# -- عرض تفاصيل مشروع معين للطالب (شاشة Project Details #6) --
# GET /api/projects/{id}/details/
# يعرض: العنوان، الوصف، الأهداف، التقنيات، المخرجات، المشرف، الحالة
# إذا كان الطالب ضمن فريق المشروع يعرض أيضاً التقدم والتقارير
class StudentProjectDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        project = get_object_or_404(Project, id=id)
        # الطالب العادي يشوف فقط المشاريع المقترحة أو مشروعه الخاص
        if not request.user.is_staff:
            if project.status != 'proposed' and not project.students.filter(id=request.user.id).exists():
                return Response({'error': 'غير مسموح بمشاهدة هذا المشروع'}, status=status.HTTP_403_FORBIDDEN)

        accepted = project.reports.filter(status='accepted').count()
        total_required = project.required_reports
        progress = min((accepted / total_required) * 100, 100) if total_required > 0 else 0

        return Response({
            'id': project.id,
            'title': project.title,
            'description': project.description,
            'objectives': project.objectives,
            'technologies': project.technologies,
            'deliverables': project.deliverables,
            'status': project.status,
            'supervisor': project.supervisor.username if project.supervisor else None,
            'available_seats': max(0, (SystemSettings.objects.first().max_students_per_project if SystemSettings.objects.first() else 5) - project.students.count()),
            'students': [s.username for s in project.students.all()],
            'accepted_reports': accepted,
            'required_reports': total_required,
            'progress': round(progress, 2),
        })


# -- عرض حالة طلب الانضمام المعلّق للطالب (شاشة Pending Request #8) --
# GET /api/student/pending-request/
# يرجع طلب (أو طلبات) الانضمام التي قدمها الطالب ولم يتم البتّ بها بعد
class StudentPendingRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.is_staff:
            return Response({'error': 'المشرفون لا يمكنهم تقديم طلبات انضمام'}, status=status.HTTP_403_FORBIDDEN)
        pending_requests = JoinRequest.objects.filter(
            student=request.user
        ).order_by('-created_at')
        serializer = JoinRequestSerializer(pending_requests, many=True)
        return Response(serializer.data)


# -- عرض تفاصيل تقرير محدّد للطالب (شاشة Report Details #12) --
# GET /api/reports/{id}/
# يعرض: معلومات التقرير + رابط الملف + الحالة + ملاحظات المشرف + تاريخ الرفع
class StudentReportDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        report = get_object_or_404(Report, id=id)
        # تحقق أن الطالب ضمن فريق المشروع أو أنه المشرف
        project = report.project
        is_team_member = project.students.filter(id=request.user.id).exists()
        is_supervisor = project.supervisor == request.user
        if not is_team_member and not is_supervisor and not request.user.is_superuser:
            return Response({'error': 'غير مسموح بمشاهدة هذا التقرير'}, status=status.HTTP_403_FORBIDDEN)

        return Response({
            'id': report.id,
            'file_title': report.file_title,
            'file_url': request.build_absolute_uri(report.file.url) if report.file else None,
            'status': report.status,
            'feedback': report.feedback,
            'uploaded_at': report.uploaded_at,
            'student': report.student.username if report.student else None,
            'project_title': project.title,
        })


# الملف الشخصي للمستخدم
# GET/PUT /api/profile/
# يعرض ويعدّل: الاسم، الإيميل، رقم الهاتف، القسم
# متاح لجميع المستخدمين (طالب/مشرف/رئيس قسم/عميد)
class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = getattr(user, 'profile', None)
        return Response({
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'department': profile.department.name if profile and profile.department else None,
            'phone': profile.phone if profile else '',
        })

    def put(self, request):
        user = request.user
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.email = request.data.get('email', user.email)
        user.save()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if 'phone' in request.data:
            profile.phone = request.data['phone']
        if 'address' in request.data:
            profile.address = request.data['address']
        profile.save()
        return Response({'message': 'تم تحديث الملف الشخصي'})
