from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from django.conf import settings


# جدول المشاريع 
class Project(models.Model):
    STATUS_CHOICES = [
        ('proposed', 'مقترح'),      
        ('in_progress', 'قيد التنفيذ'),   
        ('completed', 'منجز'),    
    ]
   
    
    title = models.CharField(max_length=200, verbose_name="عنوان المشروع")
    description = models.TextField(verbose_name="وصف المشروع")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='proposed',
        verbose_name="حالة المشروع"
    )
    
    # المشرف (المسؤول عن المشروع)
    supervisor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='supervised_projects',
        verbose_name="المشرف"
    )
    
    # الطلاب (فريق العمل - بحد أقصى 5 طلاب يتم التحكم بها في الـ Logic)
    students = models.ManyToManyField(
        User, 
        related_name='student_projects', 
        blank=True,
        verbose_name="الطلاب المشاركون"
    )
    final_grade = models.FloatField(null=True , blank=True ,verbose_name="العلامة النهائية:")
    required_reports = models.PositiveBigIntegerField(default=8 , verbose_name="عدد التقارير المطلوبة")

    # -- الحقول الإضافية لتفاصيل المشروع (مذكورة في شاشة Project Details) --
    objectives = models.TextField(blank=True, verbose_name="أهداف المشروع")
    technologies = models.TextField(blank=True, verbose_name="التقنيات المستخدمة")
    deliverables = models.TextField(blank=True, verbose_name="مخرجات المشروع")

    # القسم (جديد)
    department = models.ForeignKey(
        'Department', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='projects',
        verbose_name="القسم"
    )

    def __str__(self):
        return self.title

# جدول التقارير
class Report(models.Model):
    REPORT_STATUS =[
        ('pending','قيد المراجعة'),
        ('accepted','مقبول'),
        ('need_work','بحاجة تعديل'),
    ]

    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='reports',
        verbose_name="المشروع"
    )
    # الطالب الذي قام بعملية الرفع
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True,
        blank=True,
        related_name='submitted_reports',
        verbose_name="الطالب المرسل"
    )
    file_title = models.CharField(max_length=100, verbose_name="عنوان الملف")
    file = models.FileField(upload_to='reports/', null=True, verbose_name="ملف التقرير")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الرفع")
    status = models.CharField(max_length=20,choices= REPORT_STATUS ,default='pending')
    feedback = models.TextField(null=True, blank=True, verbose_name="ملاحظات المشرف")

    def __str__(self):
        return f"تقرير: {self.file_title} - {self.project.title}"

   

# جدول الاشعارات 
class Notification(models.Model):
    # المستلم (طالب او مشرف)
    recipient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        verbose_name="المستلم"
    )
    # المشروع المرتبط بالإشعار
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='notifications', 
        null=True,
        verbose_name="المشروع المرتبط"
    )
    message = models.TextField(verbose_name="نص الإشعار")
    is_read = models.BooleanField(default=False, verbose_name="هل قرئ؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإرسال")

    def __str__(self):
        project_name = str (self.project) if self.project else "لا يوجد"
        return f"إشعار لـ {self.recipient.username} -مشروع : {project_name}"

  


#جدول الإعلانات
class Announcement(models.Model):
    project = models.ForeignKey(Project , on_delete=models.CASCADE ,related_name='announcements')
    # -- حقل عنوان الإعلان (كان مفقوداً وأضيف ليتماشى مع شاشة Announcement Card) --
    title = models.CharField(max_length=200, default="إعلان", verbose_name="عنوان الإعلان")
    content = models.TextField()
    meeting_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Annoucement for {self.project.title} at {self.meeting_time}"
    


#جدول الحضور والغياب 
class Attendance(models.Model):
    announcement = models.ForeignKey(Announcement , on_delete=models.CASCADE ,related_name='attendances')
    student = models.ForeignKey(User , on_delete=models.CASCADE )
    is_present = models.BooleanField(default=False)
    marked_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        #ضفت هاد السطر مشان المشرف ما يسجل حضور لنفس الطالب اكتر من مرة ويصير تكرار بيانات 
        unique_together = ('announcement' , 'student')
    def __str__(self):
        status = "Present" if self.is_present else "Absent"
        return f"{self.student.username}-{status}"
    

#جدول لجنة المناقشة 
class DefenseCommittee(models.Model):
    project = models.OneToOneField(Project , on_delete=models.CASCADE , related_name='committee')
    examiners = models.ManyToManyField(settings.AUTH_USER_MODEL , related_name='defense_examinations')
    date = models.DateTimeField()
    location = models.CharField(max_length=255)
    is_finalized = models.BooleanField(default=False)
    def __str__(self):
        return f"لجنة مناقشة مشروع :{self.project.title} في {self.location}"
    

# جدول التقييمات 
class Evaluation (models.Model):
    committee = models.ForeignKey(DefenseCommittee ,on_delete=models.CASCADE , related_name='evaluations')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL , on_delete=models.CASCADE)
    grade = models.FloatField()
    feedback = models.TextField(blank=True ,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('committee' , 'doctor')

    def __str__(self):
        return f"تقييم {self.doctor.username} لمشروع {self.committee.project.title}"
    

# جدول خاص باعدادات النظام يسمح لرئيس اقسم بتحديد عدد اعضاء الفريق للمشروع الواحد
class SystemSettings(models.Model):
    department = models.OneToOneField('Department', on_delete=models.CASCADE, null=True, blank=True, related_name='settings')
    max_students_per_project = models.PositiveBigIntegerField(default=5)
    def __str__(self):
        return f"Settings - {self.department.name if self.department else 'Global'}"
    
# جدول طلب انضمام الطالب لمشروع
class JoinRequest(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    students = models.ManyToManyField(User, related_name='join_requests')

    status = models.CharField(max_length = 20 ,
    choices = [
        ("pending" , "قيد الانتظار"),
        ("approved" , "مقبول"),
        ("rejected" , "مرفوض")
    ],
    default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('project',)


# جدول الأقسام
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    head = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_departments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# -- جدول خاص برمز إعادة تعيين كلمة المرور (تستخدمه Forgot/Reset Password) --
# يتم إنشاء رمز عشوائي عند طلب "نسيت كلمة المرور" والتحقق منه عند إعادة التعيين
class PasswordResetCode(models.Model):
    email = models.EmailField(verbose_name="البريد الإلكتروني")
    code = models.CharField(max_length=100, unique=True, verbose_name="رمز التحقق")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    is_used = models.BooleanField(default=False, verbose_name="هل تم استخدامه؟")

    def __str__(self):
        return f"رمز إعادة تعيين لـ {self.email}"

# جدول البيانات الإضافية لجميع المستخدمين (الاسم، الهاتف، العنوان، القسم، تاريخ الميلاد)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)