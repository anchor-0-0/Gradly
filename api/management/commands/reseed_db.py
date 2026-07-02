from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta
from api.models import (
    Department, UserProfile, Project, JoinRequest, Report,
    Announcement, Attendance, DefenseCommittee, Evaluation,
    SystemSettings, Notification,
)


class Command(BaseCommand):
    help = 'Clears and reseeds the GPMS database with comprehensive demo data'

    def add_arguments(self, parser):
        parser.add_argument('--no-clear', action='store_true', help='Skip clearing existing data')
        parser.add_argument('--users-only', action='store_true', help='Seed users only (fast)')

    def handle(self, *args, **options):
        if not options['no_clear']:
            self._clear_all()

        self._create_groups()
        self._create_users()
        self._create_departments()
        self._create_user_profiles()

        if not options['users_only']:
            self._create_system_settings()
            self._create_projects()
            self._create_join_requests()
            self._create_reports()
            self._create_announcements()
            self._create_attendance()
            self._create_committees()
            self._create_evaluations()
            self._create_notifications()

        self._print_credentials()

    # ─────────────────────────────────────────────
    # CLEAR
    # ─────────────────────────────────────────────
    def _clear_all(self):
        self.stdout.write('Clearing existing data...')
        Notification.objects.all().delete()
        Evaluation.objects.all().delete()
        DefenseCommittee.objects.all().delete()
        Attendance.objects.all().delete()
        Announcement.objects.all().delete()
        Report.objects.all().delete()
        JoinRequest.objects.all().delete()
        SystemSettings.objects.all().delete()
        Project.objects.all().delete()
        UserProfile.objects.all().delete()
        Department.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        User.objects.filter(is_superuser=True).delete()
        Group.objects.all().delete()
        self.stdout.write('Database cleared\n')

    # ─────────────────────────────────────────────
    # GROUPS
    # ─────────────────────────────────────────────
    def _create_groups(self):
        self.stdout.write('Creating groups...')
        Group.objects.get_or_create(name='Dean')
        Group.objects.get_or_create(name='HOD')
        Group.objects.get_or_create(name='Supervisor')
        Group.objects.get_or_create(name='Student')
        self.stdout.write('  [OK] 4 groups created')

    # ─────────────────────────────────────────────
    # USERS
    # ─────────────────────────────────────────────
    def _create_users(self):
        self.stdout.write('Creating users...')

        # — Dean —
        self.dean, _ = User.objects.get_or_create(
            username='dean@gpms.edu',
            defaults={
                'email': 'dean@gpms.edu',
                'first_name': 'عمر',
                'last_name': 'الحسيني',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        self.dean.set_password('Dean@2025')
        self.dean.save()
        self.dean.groups.add(Group.objects.get(name='Dean'))

        # — 3 HODs —
        hods_data = [
            ('hod.net@gpms.edu', 'خالد', 'المالكي'),
            ('hod.sw@gpms.edu', 'نورة', 'السليمي'),
            ('hod.ai@gpms.edu', 'سعد', 'القرني'),
        ]
        self.hods = []
        hod_group = Group.objects.get(name='HOD')
        for username, first, last in hods_data:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': username,
                    'first_name': first,
                    'last_name': last,
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            user.set_password('Hod@2025')
            user.save()
            user.groups.add(hod_group)
            self.hods.append(user)

        # — 6 Supervisors (2 per dept) —
        supervisors_data = [
            ('sup.net1@gpms.edu', 'أحمد', 'الزهراني'),
            ('sup.net2@gpms.edu', 'فهد', 'العتيبي'),
            ('sup.sw1@gpms.edu', 'ليلى', 'المنصور'),
            ('sup.sw2@gpms.edu', 'هند', 'الشهري'),
            ('sup.ai1@gpms.edu', 'يوسف', 'البلوشي'),
            ('sup.ai2@gpms.edu', 'سارة', 'النعيمي'),
        ]
        self.supervisors = []
        sup_group = Group.objects.get(name='Supervisor')
        for username, first, last in supervisors_data:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': username,
                    'first_name': first,
                    'last_name': last,
                    'is_staff': True,
                    'is_superuser': False,
                }
            )
            user.set_password('Sup@2025')
            user.save()
            user.groups.add(sup_group)
            self.supervisors.append(user)

        # — 30 Students —
        students_data = [
            # s1-s5 → Networks, in project
            ('s1@gpms.edu',  'محمد',    'الغامدي'),
            ('s2@gpms.edu',  'فاطمة',   'الشهري'),
            ('s3@gpms.edu',  'عبدالله', 'القحطاني'),
            ('s4@gpms.edu',  'نورا',    'العنزي'),
            ('s5@gpms.edu',  'تركي',    'الدوسري'),
            # s6-s10 → Networks, unassigned
            ('s6@gpms.edu',  'ريم',     'الحربي'),
            ('s7@gpms.edu',  'سلطان',   'المطيري'),
            ('s8@gpms.edu',  'هند',     'السبيعي'),
            ('s9@gpms.edu',  'عمر',     'الرشيدي'),
            ('s10@gpms.edu', 'لمى',     'البدر'),

            # s11-s15 → Software, in completed project
            ('s11@gpms.edu', 'خالد',    'العجمي'),
            ('s12@gpms.edu', 'دانة',    'الفيصل'),
            ('s13@gpms.edu', 'راشد',    'الكندي'),
            ('s14@gpms.edu', 'سمية',    'الزعابي'),
            ('s15@gpms.edu', 'بدر',     'الصالح'),
            # s16-s20 → Software, unassigned
            ('s16@gpms.edu', 'منى',     'الضبيعي'),
            ('s17@gpms.edu', 'ناصر',    'المهري'),
            ('s18@gpms.edu', 'هاجر',    'العبيدي'),
            ('s19@gpms.edu', 'ماجد',    'الحمادي'),
            ('s20@gpms.edu', 'شيماء',   'البوسعيدي'),

            # s21-s25 → AI, in project
            ('s21@gpms.edu', 'أحمد',    'الدوسري'),
            ('s22@gpms.edu', 'مريم',    'الهاجري'),
            ('s23@gpms.edu', 'حسن',     'الكواري'),
            ('s24@gpms.edu', 'نورة',    'الخليفي'),
            ('s25@gpms.edu', 'علي',     'البوعينين'),
            # s26-s30 → AI, unassigned
            ('s26@gpms.edu', 'لطيفة',   'النعيمي'),
            ('s27@gpms.edu', 'سالم',    'العامري'),
            ('s28@gpms.edu', 'موزة',    'المنصوري'),
            ('s29@gpms.edu', 'خليفة',   'الحمادي'),
            ('s30@gpms.edu', 'أمل',     'الجاسم'),
        ]
        self.students = []
        stu_group = Group.objects.get(name='Student')
        for username, first, last in students_data:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': username,
                    'first_name': first,
                    'last_name': last,
                    'is_staff': False,
                    'is_superuser': False,
                }
            )
            user.set_password('Student@2025')
            user.save()
            user.groups.add(stu_group)
            self.students.append(user)

        # Named references by index
        self.net_students = self.students[0:10]       # s1-s10
        self.sw_students = self.students[10:20]       # s11-s20
        self.ai_students = self.students[20:30]       # s21-s30

        self.stdout.write('  [OK] 1 dean, 3 HODs, 6 supervisors, 30 students')

    # ─────────────────────────────────────────────
    # DEPARTMENTS
    # ─────────────────────────────────────────────
    def _create_departments(self):
        self.stdout.write('Creating departments...')

        self.dept_net, _ = Department.objects.get_or_create(
            code='NET',
            defaults={
                'name': 'شبكات الحاسوب',
                'description': 'قسم متخصص في شبكات الحاسوب وأمن المعلومات والبنية التحتية للاتصالات',
                'head': self.hods[0],
            }
        )

        self.dept_sw, _ = Department.objects.get_or_create(
            code='SW',
            defaults={
                'name': 'هندسة البرمجيات',
                'description': 'قسم متخصص في تطوير البرمجيات وهندسة النظم وإدارة المشاريع البرمجية',
                'head': self.hods[1],
            }
        )

        self.dept_ai, _ = Department.objects.get_or_create(
            code='AI',
            defaults={
                'name': 'الذكاء الاصطناعي',
                'description': 'قسم متخصص في تطبيقات الذكاء الاصطناعي والتعلم الآلي وتحليل البيانات',
                'head': self.hods[2],
            }
        )

        self.departments = [self.dept_net, self.dept_sw, self.dept_ai]

    # ─────────────────────────────────────────────
    # USER PROFILES
    # ─────────────────────────────────────────────
    def _create_user_profiles(self):
        self.stdout.write('Creating user profiles...')

        # Dean (no department)
        UserProfile.objects.get_or_create(
            user=self.dean,
            defaults={
                'phone': '0501234567',
                'address': 'مكتب العميد - المبنى الإداري',
                'birth_date': '1970-01-15',
            }
        )

        # HODs
        for i, hod in enumerate(self.hods):
            UserProfile.objects.get_or_create(
                user=hod,
                defaults={
                    'department': self.departments[i],
                    'phone': f'050{20000001 + i * 1111111}',
                    'address': f'مكتب رئيس القسم - مبنى {i + 1}',
                    'birth_date': f'197{i + 5}-0{i + 1}-15',
                }
            )

        # Supervisors
        dept_sup_map = [0, 0, 1, 1, 2, 2]  # sup index → dept index
        for i, sup in enumerate(self.supervisors):
            UserProfile.objects.get_or_create(
                user=sup,
                defaults={
                    'department': self.departments[dept_sup_map[i]],
                    'phone': f'050{30000000 + i * 1111111}',
                    'address': f'مكتب المشرف - مبنى {i + 1}',
                    'birth_date': f'198{i + 1}-{(i % 9) + 1:02d}-15',
                }
            )

        # Students: net_students[0..9] → NET, sw_students[0..9] → SW, ai_students[0..9] → AI
        dept_stu_map = [self.dept_net] * 10 + [self.dept_sw] * 10 + [self.dept_ai] * 10
        for i, stu in enumerate(self.students):
            UserProfile.objects.get_or_create(
                user=stu,
                defaults={
                    'department': dept_stu_map[i],
                    'phone': f'050{50000000 + i * 1000001}',
                    'address': 'سكن الطلاب',
                    'birth_date': f'200{1 + (i % 4)}-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}',
                }
            )

        self.stdout.write('  [OK] user profiles created')

    # ─────────────────────────────────────────────
    # SYSTEM SETTINGS
    # ─────────────────────────────────────────────
    def _create_system_settings(self):
        SystemSettings.objects.get_or_create(id=1, defaults={'max_students_per_project': 5})
        self.stdout.write('  [OK] system settings: max_students_per_project=5')

    # ─────────────────────────────────────────────
    # PROJECTS
    # ─────────────────────────────────────────────
    def _create_projects(self):
        self.stdout.write('Creating projects...')
        now = timezone.now()

        # ── Active project: Networks ──
        self.proj_net_active, _ = Project.objects.get_or_create(
            title='تطوير شبكة ذكية للمؤسسات',
            defaults={
                'description': 'تصميم وتنفيذ بنية شبكية ذكية قابلة للتوسع تدعم إنترنت الأشياء والأمن السيبراني للمؤسسات الكبرى',
                'status': 'in_progress',
                'supervisor': self.supervisors[1],
                'department': self.dept_net,
                'required_reports': 8,
                'objectives': 'تصميم بنية شبكية مرنة\nتطبيق بروتوكولات أمان متقدمة\nدمج تقنيات إنترنت الأشياء\nنظام مراقبة وتحليل الأداء',
                'technologies': 'Cisco, SDN, IoT, Wireshark, Python',
                'deliverables': 'بنية شبكية متكاملة\nنظام مراقبة وأمان\nتقرير المشروع\nدليل المستخدم',
            }
        )
        self.proj_net_active.students.add(*self.net_students[0:5])

        # ── Active project: Software (COMPLETED — waiting grade confirmation) ──
        self.proj_sw_completed, _ = Project.objects.get_or_create(
            title='نظام إدارة المكتبات الرقمية',
            defaults={
                'description': 'نظام متكامل لإدارة المكتبات الرقمية يشمل فهرسة الكتب وإدارة الإعارات والبحث الذكي',
                'status': 'completed',
                'supervisor': self.supervisors[2],
                'department': self.dept_sw,
                'final_grade': None,
                'required_reports': 8,
                'objectives': 'فهرسة آلية للكتب\nنظام إعارة ذكي\nبحث متقدم بالذكاء الاصطناعي\nتقارير إحصائية للمكتبة',
                'technologies': 'Flutter, Django, Elasticsearch, PostgreSQL',
                'deliverables': 'تطبيق ويب\nنظام إدارة المحتوى\nتقرير المشروع\nدليل المستخدم',
            }
        )
        self.proj_sw_completed.students.add(*self.sw_students[0:5])

        # ── Active project: AI ──
        self.proj_ai_active, _ = Project.objects.get_or_create(
            title='نظام التشخيص الطبي بالذكاء الاصطناعي',
            defaults={
                'description': 'نظام ذكي يساعد الأطباء في تشخيص الأمراض باستخدام تقنيات التعلم العميق وتحليل الصور الطبية',
                'status': 'in_progress',
                'supervisor': self.supervisors[5],
                'department': self.dept_ai,
                'required_reports': 8,
                'objectives': 'تحليل الصور الطبية\nتشخيص الأمراض باستخدام CNN\nنظام دعم القرار الطبي\nقاعدة بيانات للحالات',
                'technologies': 'Python, TensorFlow, PyTorch, FastAPI, React',
                'deliverables': 'نموذج ذكاء اصطناعي\nتطبيق ويب\nتقرير المشروع\nدليل المستخدم',
            }
        )
        self.proj_ai_active.students.add(*self.ai_students[0:5])

        # ── Proposed projects: Networks (7) ──
        net_proposed = [
            ('نظام إدارة الشبكات السحابية', 'تصميم منصة سحابية لإدارة وتشغيل الشبكات الافتراضية مع دعم التوسع التلقائي', self.supervisors[0]),
            ('تطبيق أمن المعلومات للمؤسسات', 'تطبيق متكامل لأمن المعلومات يشمل كشف الاختراقات ومنع الهجمات السيبرانية', self.supervisors[0]),
            ('نظام مراقبة الشبكات عن بعد', 'نظام لمراقبة أداء الشبكات واكتشاف الأعطال عن بعد باستخدام تقنيات SNMP و AI', self.supervisors[1]),
            ('منصة إدارة الخوادم الافتراضية', 'منصة متكاملة لإدارة الخوادم الافتراضية وجدولة الموارد في بيئات الحوسبة السحابية', self.supervisors[0]),
            ('تطبيق الشبكات المعرفة بالبرمجيات', 'تطبيق بنية SDN لإدارة حركة المرور بشكل ديناميكي وتحسين أداء الشبكات', self.supervisors[1]),
            ('نظام تحليل بيانات الشبكات', 'نظام لجمع وتحليل بيانات حركة المرور في الشبكات باستخدام تقنيات大数据', self.supervisors[0]),
            ('شبكة إنترنت الأشياء للمنازل الذكية', 'تصميم شبكة إنترنت أشياء متكاملة للمنازل الذكية مع نظام تحكم مركزي', self.supervisors[1]),
        ]
        self.net_proposed = []
        for title, desc, sup in net_proposed:
            proj, _ = Project.objects.get_or_create(
                title=title,
                defaults={
                    'description': desc,
                    'status': 'proposed',
                    'supervisor': sup,
                    'department': self.dept_net,
                    'required_reports': 8,
                    'objectives': 'تحليل المتطلبات\nتصميم النظام\nتطوير النموذج الأولي\nاختبار النظام',
                    'technologies': 'Python, Django, React, PostgreSQL',
                    'deliverables': 'تطبيق متكامل\nتوثيق المشروع\nدليل المستخدم',
                }
            )
            self.net_proposed.append(proj)

        # ── Proposed projects: Software (7) ──
        sw_proposed = [
            ('نظام إدارة الموارد البشرية', 'نظام متكامل لإدارة الموارد البشرية يشمل الرواتب والإجازات والتقييم', self.supervisors[2]),
            ('تطبيق إدارة المشاريع الاحترافية', 'تطبيق لإدارة المشاريع البرمجية باستخدام منهجيات Agile مع لوحات كانبان', self.supervisors[3]),
            ('منصة التجارة الإلكترونية المتكاملة', 'منصة تجارة إلكترونية متكاملة مع نظام دفع وإدارة مخزون', self.supervisors[2]),
            ('نظام إدارة علاقات العملاء', 'نظام CRM متكامل لإدارة العملاء وتتبع المبيعات والتسويق', self.supervisors[3]),
            ('تطبيق إدارة المستودعات الذكية', 'تطبيق لإدارة المستودعات باستخدام الباركود و RFID وتتبع المخزون', self.supervisors[2]),
            ('منصة الحجوزات الطبية', 'منصة حجوزات طبية تربط المرضى بالعيادات والمستشفيات', self.supervisors[3]),
            ('نظام إدارة المهام التعاوني', 'نظام تعاوني لإدارة المهام بين الفرق مع دعم المحادثات والملفات', self.supervisors[2]),
        ]
        self.sw_proposed = []
        for title, desc, sup in sw_proposed:
            proj, _ = Project.objects.get_or_create(
                title=title,
                defaults={
                    'description': desc,
                    'status': 'proposed',
                    'supervisor': sup,
                    'department': self.dept_sw,
                    'required_reports': 8,
                    'objectives': 'تحليل المتطلبات\nتصميم النظام\nتطوير النموذج الأولي\nاختبار النظام',
                    'technologies': 'Flutter, Django, PostgreSQL, Redis',
                    'deliverables': 'تطبيق متكامل\nتوثيق المشروع\nدليل المستخدم',
                }
            )
            self.sw_proposed.append(proj)

        # ── Proposed projects: AI (6) ──
        ai_proposed = [
            ('نظام التوصية الذكي للتسوق', 'نظام توصيات ذكي للتسوق الإلكتروني باستخدام تقنيات التصفية التعاونية', self.supervisors[4]),
            ('تطبيق التعرف على الوجوه', 'تطبيق للتعرف على الوجوه باستخدام تقنيات التعلم العميق والرؤية الحاسوبية', self.supervisors[4]),
            ('منصة تحليل المشاعر للنصوص', 'منصة لتحليل المشاعر في النصوص العربية باستخدام NLP والتعلم العميق', self.supervisors[5]),
            ('روبوت المحادثة للخدمات الحكومية', 'روبوت محادثة ذكي يقدم الخدمات الحكومية للمواطنين على مدار الساعة', self.supervisors[4]),
            ('نظام التنبؤ باستهلاك الطاقة', 'نظام للتنبؤ باستهلاك الطاقة في المباني باستخدام تقنيات التعلم الآلي', self.supervisors[5]),
            ('تطبيق الترجمة الفورية للنصوص', 'تطبيق للترجمة الفورية بين العربية والإنجليزية باستخدام نماذج Transformer', self.supervisors[4]),
        ]
        self.ai_proposed = []
        for title, desc, sup in ai_proposed:
            proj, _ = Project.objects.get_or_create(
                title=title,
                defaults={
                    'description': desc,
                    'status': 'proposed',
                    'supervisor': sup,
                    'department': self.dept_ai,
                    'required_reports': 8,
                    'objectives': 'تحليل المتطلبات\nتصميم النظام\nتطوير النموذج الأولي\nاختبار النظام',
                    'technologies': 'Python, TensorFlow, PyTorch, FastAPI',
                    'deliverables': 'نموذج ذكاء اصطناعي\nتطبيق متكامل\nتوثيق المشروع',
                }
            )
            self.ai_proposed.append(proj)

        self.all_projects = [
            self.proj_net_active, self.proj_sw_completed, self.proj_ai_active,
            *self.net_proposed, *self.sw_proposed, *self.ai_proposed,
        ]

        total = len(self.all_projects)
        self.stdout.write(f'  [OK] {total} projects (3 active, {total - 3} proposed)')

    # ─────────────────────────────────────────────
    # JOIN REQUESTS
    # ─────────────────────────────────────────────
    def _create_join_requests(self):
        self.stdout.write('Creating join requests...')

        try:
            # Unassigned Networks students → Networks proposed projects
            JoinRequest.objects.get_or_create(
                project=self.net_proposed[0], student=self.net_students[5],
                defaults={'status': 'pending'}
            )
            JoinRequest.objects.get_or_create(
                project=self.net_proposed[2], student=self.net_students[6],
                defaults={'status': 'pending'}
            )
            JoinRequest.objects.get_or_create(
                project=self.net_proposed[4], student=self.net_students[7],
                defaults={'status': 'rejected'}
            )
            JoinRequest.objects.get_or_create(
                project=self.net_proposed[1], student=self.net_students[8],
                defaults={'status': 'pending'}
            )
            JoinRequest.objects.get_or_create(
                project=self.net_proposed[3], student=self.net_students[9],
                defaults={'status': 'pending'}
            )

            # Unassigned Software students → Software proposed projects
            JoinRequest.objects.get_or_create(
                project=self.sw_proposed[0], student=self.sw_students[5],
                defaults={'status': 'pending'}
            )
            JoinRequest.objects.get_or_create(
                project=self.sw_proposed[2], student=self.sw_students[6],
                defaults={'status': 'approved'}
            )
            JoinRequest.objects.get_or_create(
                project=self.sw_proposed[4], student=self.sw_students[7],
                defaults={'status': 'rejected'}
            )
            JoinRequest.objects.get_or_create(
                project=self.sw_proposed[1], student=self.sw_students[8],
                defaults={'status': 'pending'}
            )
            JoinRequest.objects.get_or_create(
                project=self.sw_proposed[3], student=self.sw_students[9],
                defaults={'status': 'pending'}
            )

            # Unassigned AI students → AI proposed projects
            JoinRequest.objects.get_or_create(
                project=self.ai_proposed[0], student=self.ai_students[5],
                defaults={'status': 'pending'}
            )
            JoinRequest.objects.get_or_create(
                project=self.ai_proposed[2], student=self.ai_students[6],
                defaults={'status': 'pending'}
            )
            JoinRequest.objects.get_or_create(
                project=self.ai_proposed[4], student=self.ai_students[7],
                defaults={'status': 'approved'}
            )
            JoinRequest.objects.get_or_create(
                project=self.ai_proposed[1], student=self.ai_students[8],
                defaults={'status': 'rejected'}
            )
            JoinRequest.objects.get_or_create(
                project=self.ai_proposed[3], student=self.ai_students[9],
                defaults={'status': 'pending'}
            )

            self.stdout.write('  [OK] 15 join requests')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [ERROR] join requests: {e}'))

    # ─────────────────────────────────────────────
    # REPORTS
    # ─────────────────────────────────────────────
    def _create_reports(self):
        self.stdout.write('Creating reports...')
        now = timezone.now()

        try:
            # ── Networks Active Project (s1-s5) — 60% progress ──
            # s1: 5 reports (3 accepted, 1 need_work, 1 pending)
            Report.objects.get_or_create(
                project=self.proj_net_active, student=self.net_students[0],
                file_title='تحليل متطلبات الشبكة',
                defaults={'status': 'accepted', 'uploaded_at': now - timedelta(weeks=8)}
            )
            Report.objects.get_or_create(
                project=self.proj_net_active, student=self.net_students[0],
                file_title='تصميم البنية التحتية',
                defaults={'status': 'accepted', 'uploaded_at': now - timedelta(weeks=6)}
            )
            Report.objects.get_or_create(
                project=self.proj_net_active, student=self.net_students[0],
                file_title='تطبيق بروتوكولات الأمان',
                defaults={'status': 'accepted', 'uploaded_at': now - timedelta(weeks=4)}
            )
            Report.objects.get_or_create(
                project=self.proj_net_active, student=self.net_students[0],
                file_title='تقرير اختبار الأداء',
                defaults={
                    'status': 'need_work',
                    'feedback': 'يرجى تحسين نتائج اختبار الأداء وإضافة مقارنة مع الشبكات التقليدية',
                    'uploaded_at': now - timedelta(weeks=2),
                }
            )
            Report.objects.get_or_create(
                project=self.proj_net_active, student=self.net_students[0],
                file_title='تقرير تكامل إنترنت الأشياء',
                defaults={'status': 'pending', 'uploaded_at': now - timedelta(days=3)}
            )
            # s2: 3 reports (2 accepted, 1 need_work)
            Report.objects.get_or_create(
                project=self.proj_net_active, student=self.net_students[1],
                file_title='تحليل أمن الشبكات',
                defaults={'status': 'accepted', 'uploaded_at': now - timedelta(weeks=7)}
            )
            Report.objects.get_or_create(
                project=self.proj_net_active, student=self.net_students[1],
                file_title='تقرير الثغرات الأمنية',
                defaults={'status': 'accepted', 'uploaded_at': now - timedelta(weeks=4)}
            )
            Report.objects.get_or_create(
                project=self.proj_net_active, student=self.net_students[1],
                file_title='تقرير جدار الحماية',
                defaults={
                    'status': 'need_work',
                    'feedback': 'يحتاج إضافة قواعد تصفية متقدمة',
                    'uploaded_at': now - timedelta(weeks=1),
                }
            )
            # s3: 2 accepted
            Report.objects.get_or_create(
                project=self.proj_net_active, student=self.net_students[2],
                file_title='تصميم واجهة المراقبة',
                defaults={'status': 'accepted', 'uploaded_at': now - timedelta(weeks=5)}
            )
            Report.objects.get_or_create(
                project=self.proj_net_active, student=self.net_students[2],
                file_title='تقرير لوحة التحكم',
                defaults={'status': 'accepted', 'uploaded_at': now - timedelta(weeks=2)}
            )

            # ── AI Active Project (s21-s25) — 40% progress ──
            # s21: 3 reports (1 accepted, 1 need_work, 1 pending)
            Report.objects.get_or_create(
                project=self.proj_ai_active, student=self.ai_students[0],
                file_title='دراسة الجدوى وجمع البيانات',
                defaults={'status': 'accepted', 'uploaded_at': now - timedelta(weeks=6)}
            )
            Report.objects.get_or_create(
                project=self.proj_ai_active, student=self.ai_students[0],
                file_title='تقرير معالجة البيانات',
                defaults={
                    'status': 'need_work',
                    'feedback': 'تحتاج تنظيف البيانات من القيم الشاذة وإعادة المعالجة',
                    'uploaded_at': now - timedelta(weeks=3),
                }
            )
            Report.objects.get_or_create(
                project=self.proj_ai_active, student=self.ai_students[0],
                file_title='تقرير النموذج الأولي',
                defaults={'status': 'pending', 'uploaded_at': now - timedelta(days=5)}
            )
            # s22: 2 reports (1 accepted, 1 pending)
            Report.objects.get_or_create(
                project=self.proj_ai_active, student=self.ai_students[1],
                file_title='تحليل الصور الطبية',
                defaults={'status': 'accepted', 'uploaded_at': now - timedelta(weeks=4)}
            )
            Report.objects.get_or_create(
                project=self.proj_ai_active, student=self.ai_students[1],
                file_title='تقرير تدريب النموذج',
                defaults={'status': 'pending', 'uploaded_at': now - timedelta(days=2)}
            )
            # s23: 1 accepted
            Report.objects.get_or_create(
                project=self.proj_ai_active, student=self.ai_students[2],
                file_title='تقرير واجهة المستخدم',
                defaults={'status': 'accepted', 'uploaded_at': now - timedelta(weeks=2)}
            )

            # ── Completed Project (s11-s15) — all reports accepted ──
            Report.objects.get_or_create(
                project=self.proj_sw_completed, student=self.sw_students[0],
                file_title='تقرير تحليل المتطلبات',
                defaults={'status': 'accepted', 'uploaded_at': now - timedelta(weeks=16)}
            )
            Report.objects.get_or_create(
                project=self.proj_sw_completed, student=self.sw_students[0],
                file_title='تقرير تصميم النظام',
                defaults={'status': 'accepted', 'uploaded_at': now - timedelta(weeks=14)}
            )
            Report.objects.get_or_create(
                project=self.proj_sw_completed, student=self.sw_students[0],
                file_title='تقرير تطوير قاعدة البيانات',
                defaults={'status': 'accepted', 'uploaded_at': now - timedelta(weeks=12)}
            )
            Report.objects.get_or_create(
                project=self.proj_sw_completed, student=self.sw_students[0],
                file_title='تقرير تطوير الواجهة الخلفية',
                defaults={'status': 'accepted', 'uploaded_at': now - timedelta(weeks=10)}
            )
            Report.objects.get_or_create(
                project=self.proj_sw_completed, student=self.sw_students[0],
                file_title='تقرير تطوير الواجهة الأمامية',
                defaults={'status': 'accepted', 'uploaded_at': now - timedelta(weeks=8)}
            )
            Report.objects.get_or_create(
                project=self.proj_sw_completed, student=self.sw_students[1],
                file_title='تقرير اختبار النظام',
                defaults={'status': 'accepted', 'uploaded_at': now - timedelta(weeks=6)}
            )
            Report.objects.get_or_create(
                project=self.proj_sw_completed, student=self.sw_students[2],
                file_title='تقرير الأمان والصلاحيات',
                defaults={'status': 'accepted', 'uploaded_at': now - timedelta(weeks=4)}
            )
            Report.objects.get_or_create(
                project=self.proj_sw_completed, student=self.sw_students[3],
                file_title='تقرير دليل المستخدم',
                defaults={'status': 'accepted', 'uploaded_at': now - timedelta(weeks=2)}
            )

            self.stdout.write('  [OK] 22 reports')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [ERROR] reports: {e}'))

    # ─────────────────────────────────────────────
    # ANNOUNCEMENTS
    # ─────────────────────────────────────────────
    def _create_announcements(self):
        self.stdout.write('Creating announcements...')
        now = timezone.now()

        try:
            # Networks active project
            self.ann_net1, _ = Announcement.objects.get_or_create(
                project=self.proj_net_active,
                title='اجتماع مراجعة أداء الشبكة',
                defaults={
                    'content': 'اجتماع لمناقشة نتائج اختبار الأداء وتحسين البنية التحتية للشبكة',
                    'meeting_time': now - timedelta(days=5),
                }
            )
            self.ann_net2, _ = Announcement.objects.get_or_create(
                project=self.proj_net_active,
                title='موعد تسليم تقرير الأمان',
                defaults={
                    'content': 'تذكير: الموعد النهائي لتسليم تقرير أمن الشبكات وإعدادات جدار الحماية',
                    'meeting_time': now + timedelta(weeks=1),
                }
            )
            self.ann_net3, _ = Announcement.objects.get_or_create(
                project=self.proj_net_active,
                title='ورشة عمل بروتوكولات SDN',
                defaults={
                    'content': 'حضور ورشة عمل حول الشبكات المعرفة بالبرمجيات SDN في مختبر الشبكات',
                    'meeting_time': now + timedelta(days=10),
                }
            )

            # AI active project
            self.ann_ai1, _ = Announcement.objects.get_or_create(
                project=self.proj_ai_active,
                title='مناقشة نتائج التدريب الأولى',
                defaults={
                    'content': 'مناقشة نتائج تدريب النموذج الأولى وتحديد الخطوات التالية لتحسين الدقة',
                    'meeting_time': now - timedelta(days=3),
                }
            )
            self.ann_ai2, _ = Announcement.objects.get_or_create(
                project=self.proj_ai_active,
                title='جلسة عرض النموذج الأولي',
                defaults={
                    'content': 'تجهيز عرض تقديمي للنموذج الأولي لنظام التشخيص الطبي',
                    'meeting_time': now + timedelta(days=14),
                }
            )

            # Completed project announcements (past)
            self.ann_sw1, _ = Announcement.objects.get_or_create(
                project=self.proj_sw_completed,
                title='اجتماع بدء المشروع',
                defaults={
                    'content': 'الاجتماع الافتتاحي لمشروع المكتبة الرقمية ومناقشة خطة العمل',
                    'meeting_time': now - timedelta(weeks=16),
                }
            )
            self.ann_sw2, _ = Announcement.objects.get_or_create(
                project=self.proj_sw_completed,
                title='عرض النسخة النهائية',
                defaults={
                    'content': 'العرض النهائي لمشروع المكتبة الرقمية أمام لجنة التحكيم',
                    'meeting_time': now - timedelta(weeks=2),
                }
            )

            self.stdout.write('  [OK] 7 announcements')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [ERROR] announcements: {e}'))

    # ─────────────────────────────────────────────
    # ATTENDANCE
    # ─────────────────────────────────────────────
    def _create_attendance(self):
        self.stdout.write('Creating attendance records...')

        try:
            # Networks — ann_net1 meeting: s1-s5
            Attendance.objects.get_or_create(
                announcement=self.ann_net1, student=self.net_students[0],
                defaults={'is_present': True}
            )
            Attendance.objects.get_or_create(
                announcement=self.ann_net1, student=self.net_students[1],
                defaults={'is_present': True}
            )
            Attendance.objects.get_or_create(
                announcement=self.ann_net1, student=self.net_students[2],
                defaults={'is_present': False}
            )
            Attendance.objects.get_or_create(
                announcement=self.ann_net1, student=self.net_students[3],
                defaults={'is_present': True}
            )
            Attendance.objects.get_or_create(
                announcement=self.ann_net1, student=self.net_students[4],
                defaults={'is_present': False}
            )

            # AI — ann_ai1 meeting: s21-s25
            Attendance.objects.get_or_create(
                announcement=self.ann_ai1, student=self.ai_students[0],
                defaults={'is_present': True}
            )
            Attendance.objects.get_or_create(
                announcement=self.ann_ai1, student=self.ai_students[1],
                defaults={'is_present': True}
            )
            Attendance.objects.get_or_create(
                announcement=self.ann_ai1, student=self.ai_students[2],
                defaults={'is_present': True}
            )
            Attendance.objects.get_or_create(
                announcement=self.ann_ai1, student=self.ai_students[3],
                defaults={'is_present': False}
            )
            Attendance.objects.get_or_create(
                announcement=self.ann_ai1, student=self.ai_students[4],
                defaults={'is_present': True}
            )

            # Completed project — ann_sw1
            Attendance.objects.get_or_create(
                announcement=self.ann_sw1, student=self.sw_students[0],
                defaults={'is_present': True}
            )
            Attendance.objects.get_or_create(
                announcement=self.ann_sw1, student=self.sw_students[1],
                defaults={'is_present': True}
            )
            Attendance.objects.get_or_create(
                announcement=self.ann_sw1, student=self.sw_students[2],
                defaults={'is_present': True}
            )
            Attendance.objects.get_or_create(
                announcement=self.ann_sw1, student=self.sw_students[3],
                defaults={'is_present': True}
            )
            Attendance.objects.get_or_create(
                announcement=self.ann_sw1, student=self.sw_students[4],
                defaults={'is_present': True}
            )

            self.stdout.write('  [OK] 15 attendance records')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [ERROR] attendance: {e}'))

    # ─────────────────────────────────────────────
    # COMMITTEES
    # ─────────────────────────────────────────────
    def _create_committees(self):
        self.stdout.write('Creating defense committees...')
        now = timezone.now()

        try:
            # Completed project committee (NOT finalized — waiting HOD confirmation)
            self.committee_sw, _ = DefenseCommittee.objects.get_or_create(
                project=self.proj_sw_completed,
                defaults={
                    'date': now - timedelta(weeks=1),
                    'location': 'قاعة المناقشات الرئيسية - مبنى الهندسة',
                    'is_finalized': False,
                }
            )
            self.committee_sw.examiners.add(
                self.supervisors[3], self.supervisors[0], self.supervisors[4]
            )

            # Networks active project — upcoming defense
            self.committee_net, _ = DefenseCommittee.objects.get_or_create(
                project=self.proj_net_active,
                defaults={
                    'date': now + timedelta(weeks=4),
                    'location': 'مختبر الشبكات - مبنى 2',
                    'is_finalized': False,
                }
            )
            self.committee_net.examiners.add(
                self.supervisors[0], self.supervisors[3], self.supervisors[5]
            )

            # AI active project — upcoming defense
            self.committee_ai, _ = DefenseCommittee.objects.get_or_create(
                project=self.proj_ai_active,
                defaults={
                    'date': now + timedelta(weeks=6),
                    'location': 'مختبر الذكاء الاصطناعي - مبنى 3',
                    'is_finalized': False,
                }
            )
            self.committee_ai.examiners.add(
                self.supervisors[4], self.supervisors[1], self.supervisors[2]
            )

            self.stdout.write('  [OK] 3 defense committees')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [ERROR] committees: {e}'))

    # ─────────────────────────────────────────────
    # EVALUATIONS
    # ─────────────────────────────────────────────
    def _create_evaluations(self):
        self.stdout.write('Creating evaluations...')

        try:
            # Completed project — 3 examiners gave grades (waiting HOD confirmation)
            Evaluation.objects.get_or_create(
                committee=self.committee_sw, doctor=self.supervisors[3],
                defaults={
                    'grade': 85,
                    'feedback': 'نظام متكامل وفكرة مبتكرة، تنفيذ احترافي للواجهات',
                }
            )
            Evaluation.objects.get_or_create(
                committee=self.committee_sw, doctor=self.supervisors[0],
                defaults={
                    'grade': 90,
                    'feedback': 'أداء ممتاز في إدارة قواعد البيانات والأمان، عمل رائع',
                }
            )
            Evaluation.objects.get_or_create(
                committee=self.committee_sw, doctor=self.supervisors[4],
                defaults={
                    'grade': 88,
                    'feedback': 'تطبيق متكامل مع بحث ذكي فعّال، يحتاج تحسين طفيف في سرعة الاستجابة',
                }
            )

            self.stdout.write('  [OK] 3 evaluations (avg 87.7)')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [ERROR] evaluations: {e}'))

    # ─────────────────────────────────────────────
    # NOTIFICATIONS
    # ─────────────────────────────────────────────
    def _create_notifications(self):
        self.stdout.write('Creating notifications...')
        now = timezone.now()

        try:
            # For s1 (Networks active project)
            Notification.objects.get_or_create(
                recipient=self.net_students[0], project=self.proj_net_active,
                message='تم قبول تقريرك الثالث (بروتوكولات الأمان) بنجاح ✅',
                defaults={'is_read': True, 'created_at': now - timedelta(weeks=4)}
            )
            Notification.objects.get_or_create(
                recipient=self.net_students[0], project=self.proj_net_active,
                message='تقرير اختبار الأداء يحتاج تعديلات 📝',
                defaults={'is_read': True, 'created_at': now - timedelta(weeks=2)}
            )
            Notification.objects.get_or_create(
                recipient=self.net_students[0], project=self.proj_net_active,
                message='تذكير: اجتماع مراجعة الشبكة غداً ⏰',
                defaults={'is_read': False, 'created_at': now - timedelta(days=1)}
            )

            # For s21 (AI active project)
            Notification.objects.get_or_create(
                recipient=self.ai_students[0], project=self.proj_ai_active,
                message='تم استلام تقرير معالجة البيانات ويحتاج تعديل 📝',
                defaults={'is_read': True, 'created_at': now - timedelta(weeks=3)}
            )
            Notification.objects.get_or_create(
                recipient=self.ai_students[0], project=self.proj_ai_active,
                message='تذكير: جلسة مناقشة نتائج التدريب اليوم 🎯',
                defaults={'is_read': False, 'created_at': now - timedelta(days=2)}
            )

            # For s11 (completed project)
            Notification.objects.get_or_create(
                recipient=self.sw_students[0], project=self.proj_sw_completed,
                message='تم الانتهاء من المشروع بانتظار تأكيد العلامات ✅',
                defaults={'is_read': False, 'created_at': now - timedelta(days=7)}
            )
            Notification.objects.get_or_create(
                recipient=self.sw_students[0], project=self.proj_sw_completed,
                message='نتائج المناقشة متاحة قريباً 📋',
                defaults={'is_read': False, 'created_at': now - timedelta(days=5)}
            )

            # For unassigned students
            Notification.objects.get_or_create(
                recipient=self.net_students[5], project=self.net_proposed[0],
                message='تم استلام طلب انضمامك لمشروع إدارة الشبكات السحابية 📨',
                defaults={'is_read': False, 'created_at': now - timedelta(days=3)}
            )
            Notification.objects.get_or_create(
                recipient=self.sw_students[6], project=self.sw_proposed[2],
                message='تمت الموافقة على طلب انضمامك لمشروع التجارة الإلكترونية ✅',
                defaults={'is_read': False, 'created_at': now - timedelta(days=2)}
            )
            Notification.objects.get_or_create(
                recipient=self.ai_students[7], project=self.ai_proposed[4],
                message='تمت الموافقة على طلب انضمامك لمشروع التنبؤ بالطاقة ✅',
                defaults={'is_read': False, 'created_at': now - timedelta(days=4)}
            )

            # For supervisors
            Notification.objects.get_or_create(
                recipient=self.supervisors[1], project=self.proj_net_active,
                message='طلب جديد لانضمام طالب لمشروع الشبكة الذكية 🔔',
                defaults={'is_read': False, 'created_at': now - timedelta(days=1)}
            )
            Notification.objects.get_or_create(
                recipient=self.supervisors[0], project=self.net_proposed[0],
                message='3 طلاب جدد أرسلوا طلبات انضمام 🔔',
                defaults={'is_read': False, 'created_at': now - timedelta(days=3)}
            )
            Notification.objects.get_or_create(
                recipient=self.supervisors[2], project=self.proj_sw_completed,
                message='تم الانتهاء من المناقشة بانتظار تأكيد النتائج 📋',
                defaults={'is_read': False, 'created_at': now - timedelta(days=7)}
            )
            Notification.objects.get_or_create(
                recipient=self.supervisors[5], project=self.proj_ai_active,
                message='تقرير جديد بانتظار مراجعتك 📋',
                defaults={'is_read': False, 'created_at': now - timedelta(days=2)}
            )

            self.stdout.write('  [OK] 14 notifications')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [ERROR] notifications: {e}'))

    # ─────────────────────────────────────────────
    # PRINT CREDENTIALS
    # ─────────────────────────────────────────────
    def _print_credentials(self):
        msg = []
        msg.append('\n' + '=' * 55)
        msg.append('GPMS Database seeded successfully!')
        msg.append('=' * 55)
        msg.append('\nLOGIN CREDENTIALS:\n')
        msg.append('-' * 55)

        msg.append('\n  Dean')
        msg.append('  Email: dean@gpms.edu')
        msg.append('  Password: Dean@2025')

        msg.append('\n\n  HODs')
        msg.append('  hod.net@gpms.edu / Hod@2025')
        msg.append('  hod.sw@gpms.edu / Hod@2025')
        msg.append('  hod.ai@gpms.edu / Hod@2025')

        msg.append('\n\n  Supervisors / Sup@2025')
        msg.append('  Networks:  sup.net1, sup.net2')
        msg.append('  Software:  sup.sw1, sup.sw2')
        msg.append('  AI:        sup.ai1, sup.ai2')

        msg.append('\n\n  Students / Student@2025')
        msg.append('  Networks:   s1-s5 (in project), s6-s10 (unassigned)')
        msg.append('  Software:   s11-s15 (completed), s16-s20 (unassigned)')
        msg.append('  AI:         s21-s25 (in project), s26-s30 (unassigned)')

        msg.append('\n\n  Quick test accounts:')
        msg.append('  dean@gpms.edu')
        msg.append('  hod.sw@gpms.edu')
        msg.append('  sup.net2@gpms.edu')
        msg.append('  s11@gpms.edu')
        msg.append('  s1@gpms.edu')
        msg.append('  s6@gpms.edu')
        msg.append('  s21@gpms.edu')
        msg.append('  s26@gpms.edu')

        msg.append('\n\n' + '-' * 55)
        msg.append('\nCommands:\n')
        msg.append('  python manage.py reseed_db\n')
        msg.append('  python manage.py reseed_db --no-clear\n')
        msg.append('  python manage.py reseed_db --users-only\n')

        for line in msg:
            self.stdout.write(line)
