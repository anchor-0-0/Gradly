from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.models import User, Group
from django.db.models import Count, Avg
from ..models import Project, Report, Notification, DefenseCommittee, Evaluation, UserProfile, Department
from ..serializers import UserManagementSerializer


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
        total_committees = DefenseCommittee.objects.count()
        avg_grade = Evaluation.objects.aggregate(avg=Avg('grade'))['avg']
        return Response({
            'stats': {
                'total_users': total_users,
                'total_projects': total_projects,
                'total_committees': total_committees,
                'students_count': User.objects.filter(is_staff=False, is_superuser=False).count(),
                'supervisors_count': User.objects.filter(is_staff=True, is_superuser=False).count(),
                'completed_projects': Project.objects.filter(status='completed').count(),
                'in_progress_projects': Project.objects.filter(status='in_progress').count(),
                'proposed_projects': Project.objects.filter(status='proposed').count(),
            }
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
        role = request.data.get('role', 'student')  # student, supervisor, hod
        department_id = request.data.get('department')

        if not all([username, email, password]):
            return Response({'error': 'الحقول التالية مطلوبة: username, email, password'},
                            status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'اسم المستخدم موجود بالفعل'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            return Response({'error': 'البريد الإلكتروني موجود بالفعل'}, status=status.HTTP_400_BAD_REQUEST)

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
                pass

        return Response({
            'message': f'تم إنشاء المستخدم {username} بنجاح',
            'user': UserManagementSerializer(user).data,
        }, status=status.HTTP_201_CREATED)
