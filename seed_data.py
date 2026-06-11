import os, sys, django
sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grad_project.settings')
django.setup()

from django.contrib.auth.models import User, Group
from api.models import Department, SystemSettings, Project, JoinRequest, Notification, Report, Announcement, Attendance, DefenseCommittee, Evaluation, UserProfile

# ───────────────────────────────
# 1. التأكد من وجود مجموعة Dean
# ───────────────────────────────
dean_group, _ = Group.objects.get_or_create(name='Dean')

# ───────────────────────────────
# 2. إنشاء المستخدمين (4 أدوار)
# ───────────────────────────────

# عميد
dean, _ = User.objects.get_or_create(username='dean', email='dean@university.com')
dean.set_password('123456')
dean.is_staff = True
dean.is_superuser = True
dean.first_name = 'عميد'
dean.last_name = 'الجامعة'
dean.save()
dean.groups.add(dean_group)

# رئيس قسم
hod, _ = User.objects.get_or_create(username='hod', email='hod@university.com')
hod.set_password('123456')
hod.is_staff = True
hod.is_superuser = True
hod.first_name = 'رئيس'
hod.last_name = 'القسم'
hod.save()

# مشرف
supervisor, _ = User.objects.get_or_create(username='supervisor', email='supervisor@university.com')
supervisor.set_password('123456')
supervisor.is_staff = True
supervisor.first_name = 'مشرف'
supervisor.last_name = 'أول'
supervisor.save()

# مشرف ثاني
supervisor2, _ = User.objects.get_or_create(username='supervisor2', email='supervisor2@university.com')
supervisor2.set_password('123456')
supervisor2.is_staff = True
supervisor2.first_name = 'مشرف'
supervisor2.last_name = 'ثاني'
supervisor2.save()

# طالب 1
student1, _ = User.objects.get_or_create(username='student1', email='student1@university.com')
student1.set_password('123456')
student1.first_name = 'طالب'
student1.last_name = 'أول'
student1.save()

# طالب 2
student2, _ = User.objects.get_or_create(username='student2', email='student2@university.com')
student2.set_password('123456')
student2.first_name = 'طالب'
student2.last_name = 'ثاني'
student2.save()

# طالب 3
student3, _ = User.objects.get_or_create(username='student3', email='student3@university.com')
student3.set_password('123456')
student3.first_name = 'طالب'
student3.last_name = 'ثالث'
student3.save()

print('[OK] تم إنشاء المستخدمين:')
print('   عميد:   dean / 123456')
print('   رئيس قسم: hod / 123456')
print('   مشرف:    supervisor / 123456')
print('   مشرف 2:  supervisor2 / 123456')
print('   طالب 1:  student1 / 123456')
print('   طالب 2:  student2 / 123456')
print('   طالب 3:  student3 / 123456')

# ───────────────────────────────
# 3. إنشاء قسم
# ───────────────────────────────
dept, _ = Department.objects.get_or_create(
    name='هندسة المعلومات',
    code='IT',
    defaults={'description': 'قسم هندسة المعلومات', 'head': hod}
)

# ───────────────────────────────
# 4. إنشاء بروفايلات جميع المستخدمين
# ───────────────────────────────
UserProfile.objects.get_or_create(user=hod, defaults={'department': dept, 'phone': '0111111111', 'address': 'الجامعة'})
UserProfile.objects.get_or_create(user=supervisor, defaults={'department': dept, 'phone': '0222222222', 'address': 'الجامعة'})
UserProfile.objects.get_or_create(user=supervisor2, defaults={'department': dept, 'phone': '0233333333', 'address': 'الجامعة'})
UserProfile.objects.get_or_create(user=dean, defaults={'phone': '0333333333', 'address': 'مكتب العميد'})
UserProfile.objects.get_or_create(user=student1, defaults={'department': dept, 'phone': '0444444444', 'address': 'سكن الطلاب'})
UserProfile.objects.get_or_create(user=student2, defaults={'department': dept, 'phone': '0555555555', 'address': 'سكن الطلاب'})
UserProfile.objects.get_or_create(user=student3, defaults={'department': dept, 'phone': '0666666666', 'address': 'سكن الطلاب'})

print('[OK] تم إنشاء الأقسام والبروفايلات لجميع المستخدمين')

# ───────────────────────────────
# 5. إنشاء إعدادات النظام
# ───────────────────────────────
settings, _ = SystemSettings.objects.get_or_create(id=1, defaults={'max_students_per_project': 3})
print('[OK] تم إنشاء إعدادات النظام')

# ───────────────────────────────
# 6. إنشاء مشاريع (مع الحقول الجديدة)
# ───────────────────────────────

# مشروع مقترح (بدون طلاب)
proj1, _ = Project.objects.get_or_create(
    title='نظام ذكاء اصطناعي للتشخيص الطبي',
    defaults={
        'description': 'مشروع يستخدم التعلم العميق لتشخيص الأمراض من الصور الطبية',
        'objectives': 'بناء نموذج تعلم عميق قادر على تشخيص الأمراض من صور الأشعة\n'
                      'تحقيق دقة تشخيص تتجاوز 95%\n'
                      'تطوير واجهة ويب سهلة الاستخدام للأطباء',
        'technologies': 'Python, TensorFlow, Django, React, PostgreSQL',
        'deliverables': 'نموذج التعلم العميق المدرب\n'
                        'تطبيق ويب كامل\n'
                        'تقرير المشروع النهائي\n'
                        'دليل المستخدم',
        'status': 'proposed',
        'supervisor': supervisor,
        'required_reports': 8,
    }
)

# مشروع قيد التنفيذ (مع طلاب)
proj2, _ = Project.objects.get_or_create(
    title='تطبيق حجوزات طبية',
    defaults={
        'description': 'تطبيق موبايل لحجز المواعيد في المستشفيات',
        'objectives': 'تسهيل عملية حجز المواعيد الطبية\n'
                      'ربط المرضى بالأطباء بشكل مباشر\n'
                      'تقليل وقت الانتظار في المستشفيات',
        'technologies': 'Flutter, Django REST, MySQL, Firebase',
        'deliverables': 'تطبيق موبايل (Android + iOS)\n'
                        'لوحة تحكم ويب للإدارة\n'
                        'API Documentation\n'
                        'تقرير المشروع',
        'status': 'in_progress',
        'supervisor': supervisor,
        'required_reports': 8,
    }
)
proj2.students.add(student1, student2)

# مشروع مكتمل
proj3, _ = Project.objects.get_or_create(
    title='منصة تعليم إلكتروني',
    defaults={
        'description': 'منصة ويب للتعليم عن بعد',
        'objectives': 'توفير بيئة تعليمية تفاعلية عن بعد\n'
                      'دعم التعلم الذاتي من خلال فيديوهات واختبارات\n'
                      'تمكين التواصل بين الطلاب والمدرسين',
        'technologies': 'React, Node.js, MongoDB, AWS',
        'deliverables': 'منصة ويب كاملة\n'
                        'تطبيق موبايل\n'
                        'قاعدة بيانات متكاملة\n'
                        'تقرير المشروع النهائي',
        'status': 'completed',
        'supervisor': supervisor2,
        'final_grade': 87.5,
        'required_reports': 8,
    }
)
proj3.students.add(student3)

print('[OK] تم إنشاء المشاريع مع الحقول الجديدة (الأهداف، التقنيات، المخرجات)')

# ───────────────────────────────
# 7. إنشاء طلبات انضمام
# ───────────────────────────────
JoinRequest.objects.get_or_create(project=proj1, student=student1, defaults={'status': 'pending'})
JoinRequest.objects.get_or_create(project=proj1, student=student2, defaults={'status': 'pending'})
JoinRequest.objects.get_or_create(project=proj1, student=student3, defaults={'status': 'pending'})
print('[OK] تم إنشاء طلبات الانضمام')

# ───────────────────────────────
# 8. إنشاء تقارير (بحالات مختلفة)
# ───────────────────────────────
r1, _ = Report.objects.get_or_create(
    project=proj2, student=student1,
    defaults={'file_title': 'التقرير الأول - تحليل المتطلبات', 'status': 'accepted', 'feedback': 'عمل ممتاز، تحليل شامل للمتطلبات'}
)
r2, _ = Report.objects.get_or_create(
    project=proj2, student=student2,
    defaults={'file_title': 'التقرير الأول - تصميم النظام', 'status': 'pending'}
)
r3, _ = Report.objects.get_or_create(
    project=proj2, student=student1,
    defaults={'file_title': 'التقرير الثاني - النموذج الأولي', 'status': 'accepted', 'feedback': 'نموذج أولي جيد، بعض التحسينات مطلوبة في الواجهة'}
)
r4, _ = Report.objects.get_or_create(
    project=proj3, student=student3,
    defaults={'file_title': 'التقرير النهائي', 'status': 'accepted', 'feedback': 'تقرير ممتاز، عمل متكامل'}
)
print('[OK] تم إنشاء التقارير (4 تقارير بحالات مختلفة)')

# ───────────────────────────────
# 9. إنشاء إعلانات + حضور
# ───────────────────────────────
from datetime import datetime, timedelta
from django.utils import timezone

ann1, _ = Announcement.objects.get_or_create(
    project=proj2,
    defaults={
        'title': 'اجتماع مناقشة التقدم الأول',
        'content': 'سيتم عقد اجتماع لمناقشة التقدم المحرز في المشروع. يرجى تجهيز العروض التقديمية.',
        'meeting_time': timezone.now() + timedelta(days=7),
    }
)
Attendance.objects.get_or_create(announcement=ann1, student=student1, defaults={'is_present': True})
Attendance.objects.get_or_create(announcement=ann1, student=student2, defaults={'is_present': False})

ann2, _ = Announcement.objects.get_or_create(
    project=proj2,
    defaults={
        'title': 'اجتماع مراجعة الكود',
        'content': 'اجتماع لمراجعة الكود المصدري للتطبيق والتأكد من اتباع معايير البرمجة.',
        'meeting_time': timezone.now() + timedelta(days=14),
    }
)
Attendance.objects.get_or_create(announcement=ann2, student=student1, defaults={'is_present': False})
Attendance.objects.get_or_create(announcement=ann2, student=student2, defaults={'is_present': False})

ann3, _ = Announcement.objects.get_or_create(
    project=proj3,
    defaults={
        'title': 'اجتماع مناقشة نهائي',
        'content': 'الاجتماع النهائي لمناقشة نتائج المشروع والتحضير للعرض النهائي.',
        'meeting_time': timezone.now() - timedelta(days=5),
    }
)
Attendance.objects.get_or_create(announcement=ann3, student=student3, defaults={'is_present': True})
print('[OK] تم إنشاء الإعلانات والحضور (3 إعلانات + حضور)')

# ───────────────────────────────
# 10. إنشاء لجنة مناقشة + تقييمات
# ───────────────────────────────
committee, _ = DefenseCommittee.objects.get_or_create(
    project=proj3,
    defaults={
        'date': timezone.now() - timedelta(days=30),
        'location': 'قاعة المناقشات - مبنى الهندسة',
        'is_finalized': False,
    }
)
committee.examiners.add(supervisor, hod)

Evaluation.objects.get_or_create(committee=committee, doctor=supervisor, defaults={'grade': 90, 'feedback': 'مشروع ممتاز، عمل متكامل وجهد واضح'})
Evaluation.objects.get_or_create(committee=committee, doctor=hod, defaults={'grade': 85, 'feedback': 'عمل جيد جداً، بعض النقاط تحتاج تحسين في التوثيق'})
print('[OK] تم إنشاء لجان المناقشة والتقييمات')

# ───────────────────────────────
# 11. إنشاء إشعارات
# ───────────────────────────────
Notification.objects.get_or_create(
    recipient=supervisor,
    project=proj1,
    defaults={'message': 'طلب انضمام جديد على مشروع نظام التشخيص الطبي', 'is_read': False}
)
Notification.objects.get_or_create(
    recipient=student1,
    project=proj2,
    defaults={'message': 'تم قبولك في مشروع تطبيق الحجوزات الطبية', 'is_read': True}
)
Notification.objects.get_or_create(
    recipient=student2,
    project=proj2,
    defaults={'message': 'تم قبولك في مشروع تطبيق الحجوزات الطبية', 'is_read': True}
)
Notification.objects.get_or_create(
    recipient=hod,
    project=proj3,
    defaults={'message': 'تم إضافة تقييم جديد لمشروع منصة التعليم الإلكتروني', 'is_read': False}
)
Notification.objects.get_or_create(
    recipient=supervisor,
    project=proj2,
    defaults={'message': 'تم رفع تقرير جديد من الطالب student1', 'is_read': False}
)
print('[OK] تم إنشاء الإشعارات (5 إشعارات)')

# ───────────────────────────────
# 12. ملخص البيانات
# ───────────────────────────────
print('\n' + '='*50)
print('✅ تم تجهيز قاعدة البيانات بالكامل')
print('='*50)
print(f'المستخدمين: {User.objects.count()}')
print(f'الأقسام: {Department.objects.count()}')
print(f'المشاريع: {Project.objects.count()}')
print(f'طلبات الانضمام: {JoinRequest.objects.count()}')
print(f'التقارير: {Report.objects.count()}')
print(f'الإعلانات: {Announcement.objects.count()}')
print(f'سجلات الحضور: {Attendance.objects.count()}')
print(f'اللجان: {DefenseCommittee.objects.count()}')
print(f'التقييمات: {Evaluation.objects.count()}')
print(f'الإشعارات: {Notification.objects.count()}')
print('\nلاختبار الدخول:')
print('   POST /api/login/')
print('   body: { "username": "...", "password": "123456" }')
print('\nالحسابات:')
print('   عميد:    dean / dean@university.com')
print('   رئيس قسم: hod / hod@university.com')
print('   مشرف:    supervisor / supervisor@university.com')
print('   مشرف 2:  supervisor2 / supervisor2@university.com')
print('   طالب 1:  student1 / student1@university.com')
print('   طالب 2:  student2 / student2@university.com')
print('   طالب 3:  student3 / student3@university.com')
