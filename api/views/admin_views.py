from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.models import User, Group
from django.db.models import Count, Avg
from ..models import Project, Report, Notification, DefenseCommittee, Evaluation, UserProfile, Department
from ..serializers import UserManagementSerializer, DepartmentSerializer


# صلاحية العميد فقط
class IsDean(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Dean').exists()


# لوحة تحكم العميد (إحصائيات)
# GET /api/admin/dashboard/
class AdminDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsDean]

    def get(self, request):
        total_users = User.objects.count()
        total_projects = Project.objects.count()
        total_reports = Report.objects.count()
        total_committees = DefenseCommittee.objects.count()

        students_count = User.objects.filter(is_staff=False, is_superuser=False).count()
        supervisors_count = User.objects.filter(is_staff=True, is_superuser=False).count()
        hods_count = User.objects.filter(is_staff=True, is_superuser=True).count()
        deans_count = User.objects.filter(groups__name='Dean').distinct().count()

        completed_projects = Project.objects.filter(status='completed').count()
        in_progress_projects = Project.objects.filter(status='in_progress').count()
        proposed_projects = Project.objects.filter(status='proposed').count()

        projects_with_students = Project.objects.filter(students__isnull=False).distinct().count()
        reports_accepted = Report.objects.filter(status='accepted').count()
        reports_pending = Report.objects.filter(status='pending').count()

        total_departments = Department.objects.count()

        departments_data = []
        for dept in Department.objects.all():
            students_in_dept = UserProfile.objects.filter(
                department=dept,
                user__is_staff=False,
                user__is_superuser=False,
            ).count()
            departments_data.append({
                'id': dept.id,
                'name': dept.name,
                'code': dept.code,
                'student_count': students_in_dept,
                'member_count': dept.members.count(),
            })

        return Response({
            'stats': {
                'total_users': total_users,
                'total_projects': total_projects,
                'total_reports': total_reports,
                'total_committees': total_committees,
                'total_departments': total_departments,
                'students_count': students_count,
                'supervisors_count': supervisors_count,
                'hods_count': hods_count,
                'deans_count': deans_count,
                'completed_projects': completed_projects,
                'in_progress_projects': in_progress_projects,
                'proposed_projects': proposed_projects,
                'projects_with_students': projects_with_students,
                'reports_accepted': reports_accepted,
                'reports_pending': reports_pending,
            },
            'departments': departments_data,
            'progress': {
                'proposed_submitted': projects_with_students,
                'proposed_total': total_projects,
                'reports_submitted': total_reports,
                'reports_required': total_projects * 8 if total_projects > 0 else 0,
                'final_submitted': completed_projects,
                'final_total': total_projects,
            },
        })


# قائمة المستخدمين (للعميد/رئيس القسم)
# GET /admin/users/
class AdminUserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserManagementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_superuser:
            raise PermissionDenied('هذه الصلاحية لرئيس القسم فقط')
        return User.objects.all()


# تعديل/حذف مستخدم (للعميد/رئيس القسم)
# GET/PUT/DELETE /admin/users/{id}/
class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserManagementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_superuser:
            raise PermissionDenied('هذه الصلاحية لرئيس القسم فقط')
        return User.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.get('partial', False)
        instance = self.get_object()

        email = request.data.get('email')
        if email and email != instance.email:
            if User.objects.filter(email=email).exclude(id=instance.id).exists():
                return Response({'error': 'البريد الإلكتروني مستخدم بالفعل'}, status=status.HTTP_400_BAD_REQUEST)

        role = request.data.get('role')
        department_id = request.data.get('department')
        if role == 'hod' or (role is None and instance.is_staff and instance.is_superuser):
            target_dept = department_id or (UserProfile.objects.filter(user=instance).first().department_id if UserProfile.objects.filter(user=instance).exists() else None)
            if target_dept:
                existing_hod = UserProfile.objects.filter(
                    department_id=target_dept,
                    user__is_staff=True,
                    user__is_superuser=True,
                ).exclude(user_id=instance.id).exists()
                if existing_hod:
                    return Response({'error': 'يوجد رئيس قسم بالفعل في هذا القسم'}, status=status.HTTP_400_BAD_REQUEST)

        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


# -- إنشاء مستخدم جديد (شاشة Create User #47) --
# POST /admin/users/create/
# ينشئ مستخدم (طالب/مشرف/رئيس قسم) مع خيار تحديد القسم
class AdminCreateUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_superuser:
            raise PermissionDenied('هذه الصلاحية لرئيس القسم فقط')

        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        role = request.data.get('role')  # supervisor, hod
        department_id = request.data.get('department')

        if not all([username, email, password]):
            return Response({'error': 'جميع الحقول مطلوبة'}, status=status.HTTP_400_BAD_REQUEST)
        if role in ('supervisor', 'hod') and not department_id:
            return Response({'error': 'اختيار القسم إلزامي للمشرفين ورؤساء الأقسام'}, status=status.HTTP_400_BAD_REQUEST)
        if role == 'dean' and department_id:
            return Response({'error': 'العميد لا ينتمي لقسم محدد'}, status=status.HTTP_400_BAD_REQUEST)

        if len(password) < 6:
            return Response({'error': 'كلمة المرور يجب أن تكون 6 أحرف على الأقل'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'اسم المستخدم موجود بالفعل'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            return Response({'error': 'البريد الإلكتروني موجود بالفعل'}, status=status.HTTP_400_BAD_REQUEST)

        if role == 'hod':
            existing_hod = UserProfile.objects.filter(
                department_id=department_id,
                user__is_staff=True,
                user__is_superuser=True,
            ).exists()
            if existing_hod:
                return Response({'error': 'يوجد رئيس قسم بالفعل في هذا القسم'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = request.data.get('first_name', '')
        user.last_name = request.data.get('last_name', '')

        if role == 'supervisor':
            user.is_staff = True
        elif role == 'hod':
            user.is_staff = True
            user.is_superuser = True

        user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        if department_id:
            try:
                profile.department = Department.objects.get(id=department_id)
                profile.save()
            except Department.DoesNotExist:
                return Response({'error': 'القسم المحدد غير موجود'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': f'تم إنشاء المستخدم {username} بنجاح',
            'user': UserManagementSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


# ═══════════════ إدارة الأقسام (للعميد) ═══════════════

# قائمة الأقسام
# GET /admin/departments/
class AdminDepartmentListView(generics.ListAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_superuser:
            raise PermissionDenied('هذه الصلاحية للعميد فقط')
        return Department.objects.all()


# إنشاء قسم
# POST /admin/departments/create/
class AdminCreateDepartmentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_superuser:
            raise PermissionDenied('هذه الصلاحية للعميد فقط')

        name = request.data.get('name')
        code = request.data.get('code')

        if not all([name, code]):
            return Response({'error': 'الحقول التالية مطلوبة: name, code'},
                            status=status.HTTP_400_BAD_REQUEST)

        if Department.objects.filter(code=code).exists():
            return Response({'error': 'رمز القسم موجود بالفعل'}, status=status.HTTP_400_BAD_REQUEST)
        if Department.objects.filter(name=name).exists():
            return Response({'error': 'اسم القسم موجود بالفعل'}, status=status.HTTP_400_BAD_REQUEST)

        dept = Department.objects.create(name=name, code=code)
        return Response({
            'message': f'تم إنشاء القسم {name} بنجاح',
            'department': DepartmentSerializer(dept).data,
        }, status=status.HTTP_201_CREATED)


# تعديل/حذف قسم
# GET/PUT/DELETE /admin/departments/<id>/
class AdminDepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_superuser:
            raise PermissionDenied('هذه الصلاحية للعميد فقط')
        return Department.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        profile_ids = UserProfile.objects.filter(department=instance).values_list('user_id', flat=True)
        members = User.objects.filter(id__in=profile_ids).values('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser')
        members_list = list(members)
        projects_count = Project.objects.filter(department=instance).count()

        head_name = None
        head_email = None
        if instance.head:
            full_name = f"{instance.head.first_name} {instance.head.last_name}".strip()
            head_name = full_name if full_name else instance.head.username
            head_email = instance.head.email

        return Response({
            'id': instance.id,
            'name': instance.name,
            'code': instance.code,
            'head_id': instance.head_id,
            'head_name': head_name,
            'head_email': head_email,
            'members_count': len(members_list),
            'members': members_list,
            'projects_count': projects_count,
            'created_at': instance.created_at.isoformat() if instance.created_at else None,
        })

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        name = request.data.get('name')
        code = request.data.get('code')

        if name and name != instance.name:
            if Department.objects.filter(name=name).exclude(id=instance.id).exists():
                return Response({'error': 'اسم القسم موجود بالفعل'}, status=status.HTTP_400_BAD_REQUEST)
        if code and code != instance.code:
            if Department.objects.filter(code=code).exclude(id=instance.id).exists():
                return Response({'error': 'رمز القسم موجود بالفعل'}, status=status.HTTP_400_BAD_REQUEST)

        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        members_count = UserProfile.objects.filter(department=instance).count()
        projects_count = Project.objects.filter(department=instance).count()
        if members_count > 0 or projects_count > 0:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError(
                f'لا يمكن حذف القسم لوجود {members_count} مستخدم و {projects_count} مشروع مرتبط به'
            )
        instance.delete()
