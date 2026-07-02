from rest_framework import serializers, viewsets,generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from ..models import Notification, Project, Report ,Announcement ,Attendance , Evaluation , SystemSettings ,JoinRequest
from ..serializers import NotificationSerializer,ProjectSerializer, ReportSerializer, UserSerializer ,AnnouncementSerializer ,EvaluationSerializer, JoinRequestSerializer, AnnouncementListSerializer, AnnouncementDetailSerializer, AttendanceSerializer
from django.db.models import Avg


# الموافقة على طلب الانضمام من قبل المشرف
class ApproveJoinRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, request_id):

        join_request = get_object_or_404(JoinRequest, id=request_id)
        project = join_request.project
        if request.user != project.supervisor:
            return Response({"error" : "غير مسموح لك باتخاذ هذا الإجراء❌"} , status=status.HTTP_403_FORBIDDEN)

        if join_request.status != 'pending':
            return Response({"error":"تم معالجة الطلب مسبقاً"}, status=status.HTTP_400_BAD_REQUEST)

        settings = SystemSettings.objects.first()
        if not settings:
            return Response({"error" : "إعدادات النظام غير مهيأة بعد"} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if project.students.count() + join_request.students.count() > settings.max_students_per_project:
            return Response({"error": "لا يمكن إضافة هذا العدد، سيتجاوز الحد الأقصى للمشروع ❌"}, status=status.HTTP_400_BAD_REQUEST)

        join_request.status = "approved"
        join_request.save()

        for student in join_request.students.all():
            project.students.add(student)
            Notification.objects.create(
                recipient=student,
                project=project,
                message=f"تم قبولك في مشروع {project.title} 🎉"
            )

        if project.students.count() >= settings.max_students_per_project:
            project.status = "in_progress"
            project.save()

        return Response({"message": "تم قبول الطلب"})


# رفض طلب انضمام طالب لمشروع (المشرف فقط)
# POST /api/join_request/{id}/reject/
# يغير حالة الطلب إلى rejected ويرسل إشعار للطالب
class RejectJoinRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, request_id):
        join_request = get_object_or_404(JoinRequest, id=request_id)
        if request.user != join_request.project.supervisor:
            return Response({"error": "غير مسموح لك"}, status=status.HTTP_403_FORBIDDEN)
        if join_request.status != 'pending':
            return Response({"error": "تم معالجة الطلب مسبقاً"}, status=status.HTTP_400_BAD_REQUEST)

        join_request.status = 'rejected'
        join_request.save()

        for student in join_request.students.all():
            Notification.objects.create(
                recipient=student,
                project=join_request.project,
                message=f"عذراً، تم رفض انضمامك لمشروع {join_request.project.title}"
            )

        return Response({"message": "تم رفض الطلب"})



# إنشاء مشروع جديد (المشرف فقط)
# POST /supervisor/create-project/
# ينشئ مشروع بحالة "proposed" ويربطه بالمشرف
class SupervisorCreateProject(generics.CreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("هذه الصلاحية للمشرفين فقط")
        dept = getattr(getattr(self.request.user, 'profile', None), 'department', None)
        serializer.save(supervisor=self.request.user, status='proposed', department=dept)
       

# إدارة المشاريع (تعديل/حذف) - المشرف فقط
# PUT /supervisor/manage-project/{id}/  → تعديل
# DELETE /supervisor/manage-project/{id}/ → حذف
# ممنوع التعديل إذا المشروع in_progress، ممنوع الحذف إذا فيه طلاب
class SupervisorManageProject(generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        # يرى ويعدل مشاريعه هو فقط
        return Project.objects.filter(supervisor=self.request.user)

    def perform_update(self, serializer):
        project = self.get_object()
        if project.status == 'in_progress':
            raise serializers.ValidationError({"error": "لا يمكن تعديل المشروع بعد بدء العمل عليه"})
        serializer.save()

    def perform_destroy(self, instance):
        if instance.status == 'in_progress' or instance.students.exists():
            raise serializers.ValidationError({"error": "لا يمكن حذف مشروع فيه طلاب"})
        instance.delete()

    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]


# تقييم تقارير الطلاب (المشرف فقط)
# PUT /supervisor/evaluate-report/{id}/
# يرسل (status + feedback) ويصير إشعار للطالب
class SupervisorEvaluateReport(generics.UpdateAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Report.objects.filter(project__supervisor=self.request.user)

    def perform_update(self, serializer):
        # 1. حفظ التقرير
        report = serializer.save()
        
        # 2. إرسال الإشعار بحذر 
        if report.student and report.student:
            # منحدد اسم المشروع لو موجود، وإذا مو موجود بنكتب "عام"
            project_name = report.project.title if report.project else "عام"
            
            Notification.objects.create(
                recipient=report.student,
                message=f"🔔تم تقييم تقريرك للمشروع : {report.project.title}.\n 🗒️الملاحظات:{report.feedback}"
            )
 
# إنشاء إعلان لمشروع معين (المشرف فقط)
# POST /announcements/create/
# ينشئ إعلان + يسجل حضور للطلاب (غياب افتراضي) + يرسل إشعار للطلاب
class AnnouncementCreateView(generics.CreateAPIView):
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]
    def perform_create(self, serializer):
        project = serializer.validated_data['project']
        if self.request.user != project.supervisor:
            raise PermissionDenied("لا يمكنك إنشاء إعلان لمشروع ليس لك")
        announcement = serializer.save()
        project = announcement.project
        project_students = project.students.all()
        attendance_records = []

        for student in project_students:
            attendance_records.append(
                Attendance(student=student, announcement=announcement, is_present=False)
            )
            # إشعار لكل طالب
            Notification.objects.create(
                recipient=student,
                project=project,
                message=f"🔔 إعلان جديد لمشروع {project.title}:\n{announcement.content}"
            )
        
        # لمنع تكرار البيانات في الداتابيز
        if attendance_records:
            Attendance.objects.bulk_create(attendance_records)


# تسجيل حضور الطلاب لإعلان/اجتماع معين (المشرف فقط)
# POST /announcements/{id}/mark-attendance/
# يستقبل قائمة: [{username, is_present}, ...]
class MarkAttendanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post (self , request ,announcement_id):
        #نجيب الاعلان اللي بدنا نسجل حضورو 
        announcement = get_object_or_404(Announcement , id = announcement_id)
        if request.user != announcement.project.supervisor:
            return Response({"error":"غير مسموح لك بتسجيل الحضور"}, status=status.HTTP_403_FORBIDDEN)
        #نستقبل قائمة الطلاب من الموبايل 
        attendance_list = request.data.get('attendance_list' , [])
 
        if not attendance_list:
            return Response({"error":"لم يتم إرسال بيانات حضور ❗"},status=status.HTTP_400_BAD_REQUEST)
        for item in attendance_list:
            try:
                student = User.objects.get(username = item["username"])
            except User.DoesNotExist:
                continue
            Attendance.objects.update_or_create(
                announcement = announcement,
                student = student,
                defaults = {'is_present': item['is_present']}
            )
        return Response({"message":"تم تحديث سجل الحضور بنجاح ☺️✅"} , status=status.HTTP_200_OK)
    

# لوحة تحكم المشرف (إحصائيات عامة وقائمة بالمشاريع)
# GET /supervisor/dashboard/
# تعرض: عدد المشاريع، عدد الطلاب، التقارير المعلقة، نسبة الحضور، آخر النشاطات، قائمة المشاريع
class SupervisorDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get (self , request):
        user = request.user
        projects = Project.objects.filter(supervisor=user)
        active_projects = projects.exclude(status='proposed')
        project_count = active_projects.count()
        students_count = User.objects.filter(student_projects__supervisor=user).distinct().count()
        pending_reports = Report.objects.filter(project__supervisor=user, status='pending').count()

        attendance_rate = Attendance.objects.filter(
            announcement__project__supervisor=user
        ).aggregate(avg_attendance=Avg('is_present'))
        avg_val = attendance_rate.get('avg_attendance') or 0
        avg_attendance_percentage = float(avg_val) * 100

        # آخر 5 نشاطات (آخر التقارير المرفوعة)
        recent_reports = Report.objects.filter(project__supervisor=user).order_by('-uploaded_at')[:5]
        recent_activity = [
            {
                'type': 'report',
                'message': f'تقرير "{r.file_title}" من {r.student.username if r.student else "طالب"}',
                'date': r.uploaded_at,
            }
            for r in recent_reports
        ]

        # قائمة المشاريع النشطة مع عدد الطلاب
        my_projects = [
            {
                'id': p.id,
                'title': p.title,
                'status': p.status,
                'team_count': p.students.count(),
            }
            for p in active_projects
        ]

        return Response({
            "stats": {
                "total_projects": project_count,
                "total_students": students_count,
                "pending_reports": pending_reports,
                "avg_attendance": round(avg_attendance_percentage, 2),
            },
            "recent_activity": recent_activity,
            "my_projects": my_projects,
        })
    

# إدارة التقييمات (لجنة المناقشة)
# GET /evaluation/ → عرض التقييمات
# POST /evaluation/ → إضافة تقييم
# - رئيس القسم: يشوف كل التقييمات
# - المشرف: يشوف تقييمات لجنة مشروعه فقط
# - الدكتور: يشوف تقييمو فقط
# عند إضافة تقييم: يرسل إشعار لرئيس القسم
class EvaluationViewSet(viewsets.ModelViewSet):
    queryset = Evaluation.objects.all()
    serializer_class = EvaluationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='HOD').exists() or user.is_superuser:
            dept = getattr(getattr(user, 'profile', None), 'department', None)
            if dept:
                return Evaluation.objects.filter(committee__project__department=dept)
            return Evaluation.objects.none()
        if user.is_staff:
            # المشرف يشوف تقييمات لجنة مشروعه فقط
            return Evaluation.objects.filter(committee__project__supervisor=user)
        # الدكتور يشوف تقييمو فقط
        return Evaluation.objects.filter(doctor=user)

    def perform_create(self, serializer):
        evaluation = serializer.save(doctor=self.request.user)
        committee = evaluation.committee
        project = committee.project
        # إشعار لرئيس القسم
        superusers = User.objects.filter(is_superuser=True)
        for su in superusers:
            Notification.objects.create(
                recipient=su,
                message=f"قام الدكتور {self.request.user.username} بتقييم مشروع {project.title} بـدرجة {evaluation.grade}"
            )


    
# عرض مشاريع المشرف (قائمة)
# GET /my_projects/
class MyProjectsView (generics.ListAPIView):
    serializer_class = ProjectSerializer 
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Project.objects.filter(supervisor = self.request.user)
    
# تفاصيل مشروع للمشرف (طلاب، تقارير، تقدم، حضور)
# GET /project_details/{id}/
# يعرض: الطلاب، التقدم، التقارير المقبولة، عدد الإعلانات، نسبة الحضور
class SupervisorProjectDetails(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):

        project = get_object_or_404(
            Project,
            id=project_id,
            supervisor=request.user
        )

        students = [
            {
                "id": s.id,
                "username": s.username,
                "email": s.email,
                "full_name": f"{s.first_name} {s.last_name}".strip() or s.username,
            }
            for s in project.students.all()
        ]

        accepted_reports = project.reports.filter(
            status='accepted'
        ).count()

        if project.required_reports == 0:
            progress = 0
        else:
            progress = min((
                accepted_reports /
                project.required_reports
            ) * 100 , 100)

             # حساب نسبة الحضور
        attendance_avg = Attendance.objects.filter( 
            announcement__project=project
        ).aggregate(avg=Avg('is_present'))
        avg_val = attendance_avg["avg"] or 0

        attendance_rate = min(float(avg_val)*100 , 100)

        return Response({
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "status": project.status,
            "students": students,
            "supervisor_name": project.supervisor.username,
            "progress": round(progress, 2),
            "reports_count": project.reports.count(),
            "accepted_reports": accepted_reports,
            "announcements_count": project.announcements.count(),
            "attendance_rate": round(attendance_rate, 2),
            "technologies": project.technologies or [],
            "objectives": project.objectives or [],
            "deliverables": project.deliverables or [],
            "final_grade": project.final_grade,
        })
    

# عرض طلبات الانضمام المعلقة (للمشرف)
# GET /join_requests/pending/
# يعرض طلبات students اللي طلبوا ينضمو لمشاريع المشرف ولم يتم الرد عليهم بعد
class PendingJoinRequestsView(generics.ListAPIView):
    serializer_class = JoinRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JoinRequest.objects.filter(
            project__supervisor=self.request.user,
            status='pending'
        )


# قائمة الإعلانات مع إحصائيات (عدد الطلاب، عدد الحضور)
# GET /api/announcements/summary/
# المشرف: يشوف إعلانات مشاريعه، الطالب: يشوف إعلانات مشروعه
class AnnouncementListSummaryView(generics.ListAPIView):
    serializer_class = AnnouncementListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Announcement.objects.filter(project__supervisor=self.request.user).order_by('-created_at')
        return Announcement.objects.filter(project__students=self.request.user).order_by('-created_at')


# تفاصيل الإعلان مع الحضور
# GET /api/announcements/{id}/details/
# المشرف: يعرض الإعلان + حضور كل الطلاب
# الطالب: يعرض الإعلان + حالتو (حاضر/غايب)
class AnnouncementDetailWithAttendanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, announcement_id):
        announcement = get_object_or_404(Announcement, id=announcement_id)
        if not request.user.is_staff and not announcement.project.students.filter(id=request.user.id).exists():
            return Response({"error": "غير مسموح"}, status=status.HTTP_403_FORBIDDEN)

        base_data = {
            "id": announcement.id,
            "title": announcement.title,
            "content": announcement.content,
            "meeting_time": announcement.meeting_time,
            "created_at": announcement.created_at,
            "project_title": announcement.project.title,
        }

        if request.user.is_staff:
            # المشرف: يشوف حضور كل الطلاب
            serializer = AnnouncementDetailSerializer(announcement)
            return Response(serializer.data)
        else:
            # الطالب: يشوف حالتو فقط
            attendance = Attendance.objects.filter(announcement=announcement, student=request.user).first()
            base_data["is_present"] = attendance.is_present if attendance else None
            return Response(base_data)


# -- عرض جلسات الحضور لمشروع معين (شاشة Attendance Sessions #29) --
# GET /api/projects/{project_id}/attendance-sessions/
# للمشرف فقط: يعرض قائمة بالإعلانات/الاجتماعات مع إحصائيات الحضور لكل جلسة
class SupervisorAttendanceSessionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id, supervisor=request.user)
        announcements = Announcement.objects.filter(project=project).order_by('-meeting_time')

        sessions = []
        for ann in announcements:
            total_students = project.students.count()
            present_count = Attendance.objects.filter(announcement=ann, is_present=True).count()
            sessions.append({
                'id': ann.id,
                'title': ann.title,
                'content': ann.content,
                'meeting_time': ann.meeting_time,
                'total_students': total_students,
                'present_count': present_count,
                'absent_count': total_students - present_count,
            })

        return Response({
            'project_title': project.title,
            'sessions': sessions,
        })