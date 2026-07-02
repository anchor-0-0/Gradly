from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import Notification, Project, Report , Announcement ,Attendance ,DefenseCommittee , Evaluation, SystemSettings, JoinRequest, PasswordResetCode
from .models import Department,UserProfile
from django.utils import timezone


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        required=True,
        write_only=True,
    )

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name', 'department')

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("هذا الحساب موجود بالفعل، جرب تسجيل الدخول.")
        return value

    def create(self, validated_data):
        department = validated_data.pop('department', None)
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        try:
            user.groups.add(Group.objects.get(name='Student'))
        except Group.DoesNotExist:
            pass
        if department:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.department = department
            profile.save()
        return user

# -- سيرياليزر خاص بطلب إعادة تعيين كلمة المرور (التحقق من صحة الإيميل) --
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("لا يوجد حساب مرتبط بهذا البريد الإلكتروني")
        return value

# -- سيرياليزر خاص بتأكيد إعادة تعيين كلمة المرور --
class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=100)
    new_password = serializers.CharField(min_length=6)
    confirm_password = serializers.CharField(min_length=6)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("كلمة المرور الجديدة وتأكيدها غير متطابقين")
        # التحقق من صحة الرمز
        reset_code = PasswordResetCode.objects.filter(
            email=data['email'], code=data['code'], is_used=False
        ).first()
        if not reset_code:
            raise serializers.ValidationError("رمز التحقق غير صالح أو منتهي الصلاحية")
        return data

class ProjectSerializer(serializers.ModelSerializer):
    students = serializers.StringRelatedField(many = True,read_only=True,allow_null=True)
    supervisor_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    max_students_per_project = serializers.SerializerMethodField()
    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'status', 'students', 'required_reports',
                  'objectives', 'technologies', 'deliverables', 'final_grade', 'supervisor',
                  'supervisor_name', 'department', 'department_name', 'max_students_per_project']
        read_only_fields = ['department']
        
    # إظهار اسم المشرف للطلاب المنضمين ولجميع المشرفين/رؤساء القسم/العمداء
    def get_supervisor_name(self, obj):
        request = self.context.get('request')
        if request and request.user:
            if request.user.is_staff or request.user.is_superuser or obj.students.filter(id=request.user.id).exists():
                if obj.supervisor:
                    name = f"{obj.supervisor.first_name} {obj.supervisor.last_name}".strip()
                    return name if name else obj.supervisor.username
                return None
        return None
    
    # إظهار اسم القسم
    def get_department_name(self, obj):
        return obj.department.name if obj.department else None

    def get_max_students_per_project(self, obj):
        from .models import SystemSettings
        settings = SystemSettings.objects.first()
        return settings.max_students_per_project if settings else 5

class ReportSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = ['id', 'file_title', 'file', 'status', 'feedback', 'student', 'project', 'student_name']

    def get_student_name(self, obj):
        if obj.student:
            return obj.student.get_full_name() or obj.student.username
        return None

    def __init__(self, *args, **kwargs):
        super(ReportSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        
        # إذا اللي عم يطلب مو مشرف (يعني طالب)، منخلي التقييم للقراءة فقط
        if request and not request.user.is_staff:
            self.fields['status'].read_only = True
            self.fields['feedback'].read_only = True


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff']   


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'is_read', 'created_at']     


class AnnouncementSerializer(serializers.ModelSerializer):
    project_title = serializers.ReadOnlyField(source='project.title')
    class Meta:
        model = Announcement
        fields = ['id' , 'project' , 'project_title' , 'title' , 'content' , 'meeting_time' , 'created_at']

#ضفت فحص مشان نتأكد ان تاريخ الاجتماع مو بالماضي 
    def validate_meeting_time(self ,value):
        if value < timezone.now():
            raise serializers.ValidationError("لا يمكن تحديد موعد اجتماع في وقت سابق !")
        return value
    

class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.ReadOnlyField(source = 'student.username')
    class Meta :
        model = Attendance
        fields = ['id' , 'announcement' , 'student' , 'student_name' , 'is_present' , 'marked_at']


class JoinRequestSerializer(serializers.ModelSerializer):
    project_title = serializers.ReadOnlyField(source='project.title')
    students = serializers.SerializerMethodField()

    class Meta:
        model = JoinRequest
        fields = ['id', 'project', 'project_title', 'students', 'status', 'created_at']

    def get_students(self, obj):
        return [
            {
                'id': s.id,
                'username': s.username,
                'email': s.email,
                'full_name': f"{s.first_name} {s.last_name}".strip() or s.username,
            }
            for s in obj.students.all()
        ]


class DefenseCommitteeSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source = 'project.title')
    examiners_names = serializers.SerializerMethodField()
    class Meta :
        model = DefenseCommittee
        fields = ['id' , 'project' , 'project_name' , 'examiners' , 'examiners_names' , 'date' , 'location' , 'is_finalized']

    def get_examiners_names(self, obj):
        names = []
        for e in obj.examiners.all():
            name = f"{e.first_name} {e.last_name}".strip()
            names.append(name if name else e.username)
        return names


class EvaluationSerializer(serializers.ModelSerializer):
    doctor_name = serializers.ReadOnlyField(source = 'doctor.username')
    project_name = serializers.ReadOnlyField(source ='committee.project.title')
    class Meta:
        model = Evaluation
        fields = ['id' , 'committee' ,'doctor' , 'doctor_name' , 'grade', 'feedback']
        read_only_fields = ['doctor']


class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = ['id', 'max_students_per_project', 'department']


class DepartmentSerializer(serializers.ModelSerializer):
    head_name = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'head', 'head_name', 'members_count']

    def get_head_name(self, obj):
        if obj.head:
            name = f"{obj.head.first_name} {obj.head.last_name}".strip()
            return name if name else obj.head.username
        return None

    def get_members_count(self, obj):
        return obj.members.count()


class UserProfileSerializer(serializers.ModelSerializer):
    department = serializers.SerializerMethodField()
    class Meta:
        model = UserProfile
        fields = ['id', 'department', 'phone', 'address', 'birth_date']

    def get_department(self, obj):
        if obj.department:
            return {'id': obj.department.id, 'name': obj.department.name, 'code': obj.department.code}
        return None


class UserManagementSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    is_supervisor = serializers.ReadOnlyField(source='is_staff')
    department = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'is_active', 'profile', 'is_supervisor', 'department']

    def get_department(self, obj):
        profile = getattr(obj, 'profile', None)
        if profile and profile.department:
            return {'id': profile.department.id, 'name': profile.department.name, 'code': profile.department.code}
        return None


class AnnouncementListSerializer(serializers.ModelSerializer):
    project_title = serializers.ReadOnlyField(source='project.title')
    student_count = serializers.SerializerMethodField()
    attendance_count = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = ['id', 'project', 'project_title', 'title', 'content', 'meeting_time', 'created_at', 'student_count', 'attendance_count']

    def get_student_count(self, obj):
        return obj.project.students.count()

    def get_attendance_count(self, obj):
        return obj.attendances.count()


class AnnouncementDetailSerializer(serializers.ModelSerializer):
    project_title = serializers.ReadOnlyField(source='project.title')
    attendances = AttendanceSerializer(many=True, read_only=True)

    class Meta:
        model = Announcement
        fields = ['id', 'project', 'project_title', 'title', 'content', 'meeting_time', 'created_at', 'attendances']