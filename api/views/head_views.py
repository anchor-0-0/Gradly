from rest_framework import viewsets,generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.models import User
from ..models import Notification, Project,DefenseCommittee , Evaluation, SystemSettings, Department
from ..serializers import ProjectSerializer, DefenseCommitteeSerializer, SystemSettingsSerializer, DepartmentSerializer, NotificationSerializer
from django.db.models import  Avg


def _get_department(user):
    profile = getattr(user, 'profile', None)
    if profile:
        return profile.department
    return None


def _is_hod(user):
    return user.groups.filter(name='HOD').exists()


# واجهة التحكم باللجان (خاصة برئيس القسم)
# عرض/إنشاء/تعديل/حذف لجان المناقشة
# - رئيس القسم: يشوف كل اللجان ويقدر ينشئ ويعدل ويحذف ويعتمد النتيجة
# - الدكتور (عضو لجنة): يشوف بس اللجان اللي هو عضو فيها
# عند إنشاء لجنة: يرسل إشعار للطلاب (تاريخ+وقت+مكان+أسماء اللجنة) وللدكاترة (تم إضافتك كلجنة)
class DefenseCommitteeViewSet(viewsets.ModelViewSet):
    queryset = DefenseCommittee.objects.all()
    serializer_class = DefenseCommitteeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if _is_hod(user):
            dept = _get_department(user)
            if dept is None:
                return DefenseCommittee.objects.none()
            return DefenseCommittee.objects.filter(project__department=dept)
        return DefenseCommittee.objects.filter(examiners=user)

    def perform_create(self, serializer):
        # إنشاء لجنة جديدة: شرط أن يكون مشرف المشروع ضمن أعضاء اللجنة
        if not _is_hod(self.request.user):
            raise PermissionDenied("عذراً هذه الصلاحية لرئيس القسم فقط")
        project = serializer.validated_data['project']
        examiners = serializer.validated_data.get('examiners', [])
        if project.supervisor not in examiners:
            raise PermissionDenied("يجب أن يكون مشرف المشروع ضمن لجنة المناقشة")
        if len(examiners) < 2:
            raise PermissionDenied("يجب أن تضم اللجنة على الأقل مشرف المشروع وممتحن إضافي واحد")
        if len(examiners) > 3:
            raise PermissionDenied("الحد الأقصى لأعضاء اللجنة هو 3 (المشرف + 2 ممتحنين)")
        # تحقق أن جميع الممتحنين من نفس قسم المشروع
        dept = _get_department(self.request.user)
        if dept and project.department != dept:
            raise PermissionDenied("هذا المشروع ليس من قسمك")
        for examiner in examiners:
            examiner_dept = _get_department(examiner)
            if examiner_dept != dept:
                raise PermissionDenied(f"الممتحن {examiner.username} ليس من قسم {dept.name}")
        serializer.save()

        # إشعار للطلاب بموعد المناقشة
        examiners_names = [u.username for u in examiners]
        committee_date = serializer.validated_data['date']
        committee_details = (
            f"المشروع: {project.title}\n"
            f"التاريخ: {committee_date.strftime('%Y-%m-%d')}\n"
            f"الوقت: {committee_date.strftime('%H:%M')}\n"
            f"المكان: {serializer.validated_data['location']}\n"
            f"أعضاء اللجنة: {', '.join(examiners_names)}"
        )
        for student in project.students.all():
            Notification.objects.create(
                recipient=student,
                project=project,
                message=f"تم تحديد موعد مناقشة مشروعك\n{committee_details}"
            )
        # إشعار لأعضاء اللجنة (الدكاترة)
        for examiner in examiners:
            Notification.objects.create(
                recipient=examiner,
                project=project,
                message=f"تم إضافتك كلجنة مناقشة\n{committee_details}"
            )

    def perform_update(self, serializer):
        if not _is_hod(self.request.user):
            raise PermissionDenied("عذراً هذه الصلاحية لرئيس القسم فقط")
        examiners = serializer.validated_data.get('examiners', None)
        if examiners is not None:
            project = serializer.instance.project
            if project.supervisor not in examiners:
                raise PermissionDenied("يجب أن يكون مشرف المشروع ضمن لجنة المناقشة")
            if len(examiners) < 2:
                raise PermissionDenied("يجب أن تضم اللجنة على الأقل مشرف المشروع وممتحن إضافي واحد")
            if len(examiners) > 3:
                raise PermissionDenied("الحد الأقصى لأعضاء اللجنة هو 3 (المشرف + 2 ممتحنين)")
            dept = _get_department(self.request.user)
            for examiner in examiners:
                examiner_dept = _get_department(examiner)
                if examiner_dept != dept:
                    raise PermissionDenied(f"الممتحن {examiner.username} ليس من قسم {dept.name}")
        serializer.save()

    def perform_destroy(self, instance):
        # حذف لجنة (فقط لرئيس القسم)
        if not _is_hod(self.request.user):
            raise PermissionDenied("عذراً هذه الصلاحية لرئيس القسم فقط")
        instance.delete()

    @action(detail=True, methods=['post'], url_path='finalize')
    def finalize_result(self, request, pk=None):
        if not _is_hod(request.user):
            return Response(
                {"error": "غير مسموح لك باعتماد النتيجة"},
                status=status.HTTP_403_FORBIDDEN,
            )
        committee = self.get_object()
        result = Evaluation.objects.filter(committee_id=committee.id).aggregate(avg=Avg('grade'))
        avg_grade = result.get('avg')
        if avg_grade is None:
            return Response(
                {"error": "لا يوجد تقييمات مسجلة لهذه اللجنة بعد"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if avg_grade >= 60:
            subject = "تهنئة بالنجاح 🎓 \n"
            message = f"مبارك يا مهندس/ة 🥳🎉 \n نتيجتك النهائية :{avg_grade}\n نتمنى لك مستقبلاً باهراً 🫶🏻"
        else:
            subject = "نتائج مناقشة مشروع التخرج 🎓\n"
            message = f"عزيزي الطالب :\n تم رصد نتيجتك {avg_grade} \n حظاً أوفر بالمرات القادمة 💔"

        project = committee.project
        for student in project.students.all():
            full_notification_text = f"{subject}  \n{message}"
            Notification.objects.create(
                recipient=student, project=project, message=full_notification_text, is_read=False
            )
            project.final_grade = avg_grade
            project.save()

        committee.is_finalized = True
        committee.save()
        return Response(
            {"message": "تم اعتماد النتيجة وارسالها للطلاب بنجاح ✅", "final_grade": avg_grade},
            status=status.HTTP_200_OK,
        )


# -- لوحة تحكم رئيس القسم (شاشة HOD Dashboard #33) --
# GET /api/hod/dashboard/
# تعرض: إحصائيات (كل المشاريع، النشطة، المنجزة، اللجان) + قائمة بجميع المشاريع
class HODDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not _is_hod(request.user):
            raise PermissionDenied("هذه الصلاحية لرئيس القسم فقط")

        from api.models import UserProfile
        profile = UserProfile.objects.filter(user=request.user).first()
        dept = profile.department if profile else None

        base_qs = Project.objects.filter(department=dept) if dept else Project.objects.all()
        committee_base = DefenseCommittee.objects.filter(project__department=dept) if dept else DefenseCommittee.objects.all()
        student_ids = UserProfile.objects.filter(department=dept).values_list('user_id', flat=True) if dept else None
        student_qs = User.objects.filter(id__in=student_ids) if student_ids else User.objects.filter(is_staff=False, is_superuser=False)
        supervisor_qs = User.objects.filter(id__in=UserProfile.objects.filter(department=dept).values_list('user_id', flat=True)) if dept else User.objects.filter(is_staff=True)

        total_projects = base_qs.count()
        active_projects = base_qs.filter(status='in_progress').count()
        completed_projects = base_qs.filter(status='completed').count()
        total_committees = committee_base.count()
        total_students = student_qs.filter(is_staff=False, is_superuser=False).count()
        total_supervisors = supervisor_qs.filter(is_staff=True).count()
        pending_results = committee_base.filter(is_finalized=False).count()

        projects = base_qs.exclude(status='proposed').order_by('-id')[:10]
        projects_list = []
        for p in projects:
            accepted = p.reports.filter(status='accepted').count()
            required = p.required_reports if p.required_reports else 0
            progress = min((accepted / required) * 100, 100) if required > 0 else 0

            supervisor_name = None
            if p.supervisor:
                supervisor_name = f"{p.supervisor.first_name} {p.supervisor.last_name}".strip() or p.supervisor.username

            projects_list.append({
                'id': p.id,
                'title': p.title,
                'status': p.status,
                'supervisor': supervisor_name,
                'students_count': p.students.count(),
                'progress': round(progress, 1),
            })

        return Response({
            'stats': {
                'total_projects': total_projects,
                'active_projects': active_projects,
                'completed_projects': completed_projects,
                'total_committees': total_committees,
                'total_students': total_students,
                'total_supervisors': total_supervisors,
                'pending_results': pending_results,
            },
            'projects': projects_list,
        })


# -- إشعارات رئيس القسم (شاشة HOD Notifications #44) --
# GET /api/hod/notifications/
# يعرض جميع الإشعارات المرسلة إلى رئيس القسم
class HODNotificationsView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not _is_hod(self.request.user):
            raise PermissionDenied("هذه الصلاحية لرئيس القسم فقط")
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

    @action(detail =True , methods = ['post'], url_path='finalize')
    def finalize_result (self ,request ,pk=None):
        # اعتماد نتيجة المناقشة: يحسب متوسط تقييمات الدكاترة
        # >= 60 نجاح ويتم تخزين الدرجة في المشروع
        # يرسل إشعار للطلاب بالنتيجة (نجاح/رسوب)
            if not _is_hod(request.user):
                 return Response({"error":"غير مسموح لك باعتماد النتيجة ❌"} , status=status.HTTP_403_FORBIDDEN)
            committee = self.get_object()

            result = Evaluation.objects.filter(committee_id =committee.id).aggregate(avg=Avg('grade'))
            avg_grade = result.get('avg')
            if avg_grade is None :
                return Response( {
                                 "error":"لا يوجد تقييمات مسجلة لهذه اللجنة بعد 🙂‍↔️"
                                 } ,status=status.HTTP_400_BAD_REQUEST
                                )
            
            
            if avg_grade >=60 :
                subject = "تهنئة بالنجاح 🎓 \n"
                message = f"مبارك يا مهندس/ة 🥳🎉 \n نتيجتك النهائية :{avg_grade}\n نتمنى لك مستقبلاً باهراً 🫶🏻"
            else :
                subject = "نتائج مناقشة مشروع التخرج 🎓\n"
                message = f"عزيزي الطالب :\n تم رصد نتيجتك {avg_grade} \n حظاً أوفر بالمرات القادمة 💔"

            #ارسال النتيجة للطالب
            project = committee.project
            for student in project.students.all():
                full_notification_text = f"{subject}  \n{message}"
                Notification.objects.create(
                    recipient = student , project=project,message = full_notification_text,is_read=False
                )
                project.final_grade = avg_grade
                project.save()


            committee.is_finalized = True
            committee.save()
            return Response ({
                "message":"تم اعتماد النتيجة وارسالها للطلاب بنجاح ✅",
                "final_grade":avg_grade}
                ,status=status.HTTP_200_OK)
    

# واجهة خاصة برئيس القسم لعرض قائمة بجميع المشاريع (عنوان، وصف، حالة، طلاب)
class HeadProjectView(generics.ListAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        if not _is_hod(self.request.user):
            raise PermissionDenied("هذه الصلاحية لرئيس القسم فقط")
        dept = _get_department(self.request.user)
        if dept is None:
            return Project.objects.none()
        return Project.objects.filter(department=dept)
    
# إعدادات النظام (لرئيس القسم)
# GET: عرض الإعدادات الحالية (الحد الأقصى للطلاب لكل مشروع)
# PUT: تعديل الإعدادات
class SystemSettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not _is_hod(request.user):
            raise PermissionDenied("هذه الصلاحية لرئيس القسم فقط")
        dept = _get_department(request.user)
        if dept is None:
            return Response({'error': 'لا يوجد قسم مرتبط'}, status=status.HTTP_400_BAD_REQUEST)
        settings, _ = SystemSettings.objects.get_or_create(department=dept)
        serializer = SystemSettingsSerializer(settings)
        return Response(serializer.data)

    def put(self, request):
        if not _is_hod(request.user):
            raise PermissionDenied("هذه الصلاحية لرئيس القسم فقط")
        dept = _get_department(request.user)
        if dept is None:
            return Response({'error': 'لا يوجد قسم مرتبط'}, status=status.HTTP_400_BAD_REQUEST)
        settings, _ = SystemSettings.objects.get_or_create(department=dept)
        serializer = SystemSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(department=dept)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# تفاصيل مشروع محدد (لرئيس القسم)
# يعرض: المشرف، الطلاب، التقارير المطلوبة/المقبولة، نسبة التقدم %، الدرجة النهائية
class HeadProjectDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        # جلب تفاصيل مشروع معين بواسطة id

        if not _is_hod(request.user):
            raise PermissionDenied(
                "هذه الصلاحية لرئيس القسم فقط"
            )

        dept = _get_department(self.request.user)
        if dept is None:
            return Response({'error': 'لا يوجد قسم مرتبط'}, status=status.HTTP_400_BAD_REQUEST)
        project = get_object_or_404(Project, id=project_id, department=dept)

        accepted_reports = project.reports.filter(
            status='accepted'
        ).count()

        reports_count = project.reports.count()

        if project.required_reports == 0:
            progress = 0
        else:
            progress = min((
                accepted_reports /
                project.required_reports
            ) * 100 , 100)

        return Response({
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "status": project.status,

            "supervisor":
                project.supervisor.id
                if project.supervisor else None,

            "supervisor_name":
                f"{project.supervisor.first_name} {project.supervisor.last_name}".strip()
                if project.supervisor else None,

            "students": [
                student.username
                for student in project.students.all()
            ],

            "required_reports":
                project.required_reports,

            "reports_count":
                reports_count,

            "accepted_reports":
                accepted_reports,

            "progress":
                round(progress, 2),
  
            "final_grade":
                project.final_grade
        })
     


# إدارة الأقسام (لرئيس القسم)
# عرض/إضافة/تعديل/حذف الأقسام (قيد التطوير - مستخدم حالياً؟)
class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Dean').exists():
            return Department.objects.all()
        if _is_hod(user):
            dept = _get_department(user)
            if dept:
                return Department.objects.filter(id=dept.id)
        return Department.objects.none()

    def perform_create(self, serializer):
        # إضافة قسم جديد (فقط لرئيس القسم)
        if not _is_hod(self.request.user):
            raise PermissionDenied("هذه الصلاحية لرئيس القسم فقط")
        serializer.save()

    def perform_update(self, serializer):
        # تعديل قسم موجود (فقط لرئيس القسم)
        if not _is_hod(self.request.user):
            raise PermissionDenied("هذه الصلاحية لرئيس القسم فقط")
        serializer.save()

    def perform_destroy(self, instance):
        # حذف قسم (فقط لرئيس القسم)
        if not _is_hod(self.request.user):
            raise PermissionDenied("هذه الصلاحية لرئيس القسم فقط")
        instance.delete()

