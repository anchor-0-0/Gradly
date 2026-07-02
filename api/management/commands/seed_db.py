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
    help = 'Seeds the database with realistic GPMS demo data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )
        parser.add_argument(
            '--users-only',
            action='store_true',
            help='Seed only users (faster for auth testing)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self._clear_data()

        self.stdout.write(self.style.WARNING('\nStarting GPMS database seed...\n'))

        self._create_groups()
        self._create_departments()
        self._create_users()
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

        self._print_summary()

    # ─────────────────────────────────────────────
    # CLEAR DATA
    # ─────────────────────────────────────────────
    def _clear_data(self):
        self.stdout.write(self.style.WARNING('Clearing existing data...'))
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
        self.stdout.write(self.style.SUCCESS('[OK] Data cleared.'))

    # ─────────────────────────────────────────────
    # GROUPS
    # ─────────────────────────────────────────────
    def _create_groups(self):
        self.stdout.write('Creating groups...')
        Group.objects.get_or_create(name='Dean')
        Group.objects.get_or_create(name='HOD')
        Group.objects.get_or_create(name='Supervisor')
        Group.objects.get_or_create(name='Student')
        self.stdout.write(self.style.SUCCESS('  [OK] 4 groups created.'))

    # ─────────────────────────────────────────────
    # DEPARTMENTS
    # ─────────────────────────────────────────────
    def _create_departments(self):
        self.stdout.write('Creating departments...')
        self.dept_se = Department.objects.get_or_create(
            code='SE',
            defaults={
                'name': 'قسم هندسة البرمجيات',
                'description': 'قسم متخصص في تطوير البرمجيات وهندسة النظم',
            }
        )[0]
        self.dept_is = Department.objects.get_or_create(
            code='IS',
            defaults={
                'name': 'قسم نظم المعلومات',
                'description': 'قسم متخصص في نظم المعلومات وإدارتها',
            }
        )[0]
        self.dept_ai = Department.objects.get_or_create(
            code='AI',
            defaults={
                'name': 'قسم الذكاء الاصطناعي',
                'description': 'قسم متخصص في تطبيقات الذكاء الاصطناعي والتعلم الآلي',
            }
        )[0]
        self.stdout.write(self.style.SUCCESS('  [OK] 3 departments created.'))

    # ─────────────────────────────────────────────
    # USERS
    # ─────────────────────────────────────────────
    def _create_users(self):
        self.stdout.write('Creating users...')

        # ── Dean ──
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
        self.stdout.write('  [OK] Dean: dean@gpms.edu')

        # ── HODs ──
        self.hod1, _ = User.objects.get_or_create(
            username='hod@gpms.edu',
            defaults={
                'email': 'hod@gpms.edu',
                'first_name': 'محمد',
                'last_name': 'الأحمد',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        self.hod1.set_password('Hod@2025')
        self.hod1.save()
        self.hod1.groups.add(Group.objects.get(name='HOD'))
        self.stdout.write('  [OK] HOD: hod@gpms.edu')

        self.hod2, _ = User.objects.get_or_create(
            username='hod2@gpms.edu',
            defaults={
                'email': 'hod2@gpms.edu',
                'first_name': 'سارة',
                'last_name': 'النعيمي',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        self.hod2.set_password('Hod2@2025')
        self.hod2.save()
        self.hod2.groups.add(Group.objects.get(name='HOD'))
        self.stdout.write('  [OK] HOD2: hod2@gpms.edu')

        # ── Supervisors ──
        supervisors_data = [
            ('supervisor1@gpms.edu', 'أحمد', 'الزهراني'),
            ('supervisor2@gpms.edu', 'ليلى', 'المنصور'),
            ('supervisor3@gpms.edu', 'خالد', 'العتيبي'),
            ('supervisor4@gpms.edu', 'نورة', 'الشمري'),
            ('supervisor5@gpms.edu', 'يوسف', 'البلوشي'),
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
            self.stdout.write(f'  [OK] Supervisor: {username}')

        # ── Students ──
        students_data = [
            ('s1@gpms.edu', 'أحمد', 'محمد', 'الغامدي'),
            ('s2@gpms.edu', 'فاطمة', 'علي', 'الشهري'),
            ('s3@gpms.edu', 'عبدالله', 'سعد', 'القحطاني'),
            ('s4@gpms.edu', 'نورا', 'خالد', 'العنزي'),
            ('s5@gpms.edu', 'محمد', 'يوسف', 'الدوسري'),
            ('s6@gpms.edu', 'ريم', 'عبدالرحمن', 'الحربي'),
            ('s7@gpms.edu', 'سلطان', 'ناصر', 'المطيري'),
            ('s8@gpms.edu', 'هند', 'طارق', 'السبيعي'),
            ('s9@gpms.edu', 'عمر', 'فهد', 'الرشيدي'),
            ('s10@gpms.edu', 'لمى', 'جاسم', 'البدر'),
            ('s11@gpms.edu', 'تركي', 'سعود', 'العجمي'),
            ('s12@gpms.edu', 'دانة', 'وليد', 'الفيصل'),
            ('s13@gpms.edu', 'راشد', 'منصور', 'الكندي'),
            ('s14@gpms.edu', 'سمية', 'حمد', 'الزعابي'),
            ('s15@gpms.edu', 'بدر', 'علي', 'الصالح'),
            ('s16@gpms.edu', 'منال', 'عبدالعزيز', 'الراشد'),
            ('s17@gpms.edu', 'فيصل', 'سالم', 'الحربي'),
            ('s18@gpms.edu', 'لينا', 'أحمد', 'الشهابي'),
            ('s19@gpms.edu', 'يوسف', 'umar', 'العمري'),
            ('s20@gpms.edu', 'حور', 'خالد', 'القحطاني'),
        ]
        self.students = []
        stu_group = Group.objects.get(name='Student')
        for username, first, mid, last in students_data:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': username,
                    'first_name': first,
                    'last_name': f'{mid} {last}',
                    'is_staff': False,
                    'is_superuser': False,
                }
            )
            user.set_password('Student@2025')
            user.save()
            user.groups.add(stu_group)
            self.students.append(user)
        self.stdout.write(self.style.SUCCESS(f'  [OK] {len(self.students)} students created.'))

    # ─────────────────────────────────────────────
    # USER PROFILES
    # ─────────────────────────────────────────────
    def _create_user_profiles(self):
        self.stdout.write('Creating user profiles...')
        departments = [self.dept_se, self.dept_is, self.dept_ai]

        UserProfile.objects.get_or_create(
            user=self.dean,
            defaults={
                'phone': '0501234567',
                'address': 'مكتب العميد - المبنى الإداري',
                'birth_date': '1970-01-15',
            }
        )
        UserProfile.objects.get_or_create(
            user=self.hod1,
            defaults={
                'department': self.dept_se,
                'phone': '0502345678',
                'address': 'مكتب رئيس القسم - مبنى الهندسة',
                'birth_date': '1975-05-20',
            }
        )
        UserProfile.objects.get_or_create(
            user=self.hod2,
            defaults={
                'department': self.dept_is,
                'phone': '0503456789',
                'address': 'مكتب رئيس القسم - مبنى العلوم',
                'birth_date': '1978-03-10',
            }
        )

        for i, sup in enumerate(self.supervisors):
            dept = departments[i % len(departments)]
            UserProfile.objects.get_or_create(
                user=sup,
                defaults={
                    'department': dept,
                    'phone': f'050{10000000 + i * 1111111}',
                    'address': f'مكتب المشرف - مبنى {i + 1}',
                    'birth_date': f'198{0 + i}-0{i + 1}-15',
                }
            )

        student_addresses = [
            'سكن الطلاب - المبنى 1',
            'سكن الطلاب - المبنى 2',
            'سكن الطلاب - المبنى 1',
            'سكن الطلاب - المبنى 2',
            'سكن الطلاب - المبنى 3',
            'سكن الطلاب - المبنى 1',
            'سكن الطلاب - المبنى 2',
            'سكن الطلاب - المبنى 3',
            'سكن الطلاب - المبنى 1',
            'سكن الطلاب - المبنى 2',
            'سكن الطلاب - المبنى 3',
            'سكن الطلاب - المبنى 1',
            'سكن الطلاب - المبنى 2',
            'سكن الطلاب - المبنى 3',
            'سكن الطلاب - المبنى 1',
            'سكن الطلاب - المبنى 2',
            'سكن الطلاب - المبنى 3',
            'سكن الطلاب - المبنى 1',
            'سكن الطلاب - المبنى 2',
            'سكن الطلاب - المبنى 3',
        ]
        for i, stu in enumerate(self.students):
            dept = departments[i % len(departments)]
            UserProfile.objects.get_or_create(
                user=stu,
                defaults={
                    'department': dept,
                    'phone': f'050{50000000 + i * 1234567}',
                    'address': student_addresses[i],
                    'birth_date': f'200{1 + i % 4}-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}',
                }
            )
        self.stdout.write(self.style.SUCCESS('  [OK] User profiles created.'))

    # ─────────────────────────────────────────────
    # SYSTEM SETTINGS
    # ─────────────────────────────────────────────
    def _create_system_settings(self):
        self.stdout.write('Creating system settings...')
        SystemSettings.objects.get_or_create(
            id=1,
            defaults={'max_students_per_project': 5}
        )
        self.stdout.write(self.style.SUCCESS('  [OK] SystemSettings: max_students_per_project=5'))

    # ─────────────────────────────────────────────
    # PROJECTS
    # ─────────────────────────────────────────────
    def _create_projects(self):
        self.stdout.write('Creating projects...')
        now = timezone.now()

        # ── مشروع 1: نظام إدارة الصيدليات الذكي ──
        self.proj1, _ = Project.objects.get_or_create(
            title='نظام إدارة الصيدليات الذكي',
            defaults={
                'description': 'نظام متكامل لإدارة المخزون الدوائي وتتبع انتهاء صلاحيات الأدوية',
                'status': 'in_progress',
                'supervisor': self.supervisors[0],
                'required_reports': 8,
                'objectives': 'بناء واجهة إدارة مخزون سهلة الاستخدام\n'
                              'نظام تنبيه تلقائي لانتهاء الصلاحية\n'
                              'تقارير يومية وشهرية للمخزون',
                'technologies': 'Flutter, Django, PostgreSQL',
                'deliverables': 'تطبيق ويب لإدارة الصيدليات\n'
                                'نظام تنبيهات تلقائي\n'
                                'تقارير المخزون',
            }
        )
        self.proj1.students.add(
            self.students[0], self.students[1], self.students[2],
            self.students[3], self.students[4],
        )

        # ── مشروع 2: تطبيق التوجيه الجامعي الذكي ──
        self.proj2, _ = Project.objects.get_or_create(
            title='تطبيق التوجيه الجامعي الذكي',
            defaults={
                'description': 'تطبيق يساعد الطلاب الجدد على اختيار التخصص المناسب',
                'status': 'in_progress',
                'supervisor': self.supervisors[1],
                'required_reports': 8,
                'objectives': 'اختبار ميول وقدرات الطالب\n'
                              'توصيات مبنية على الذكاء الاصطناعي\n'
                              'ربط مع نتائج الثانوية العامة',
                'technologies': 'React Native, Node.js, MongoDB',
                'deliverables': 'تطبيق موبايل للتوجيه الجامعي\n'
                                'نظام توصيات ذكي\n'
                                'تقرير المشروع النهائي',
            }
        )
        self.proj2.students.add(
            self.students[5], self.students[6], self.students[7],
            self.students[8], self.students[9],
        )

        # ── مشروع 3: منصة التعلم التكيفي ──
        self.proj3, _ = Project.objects.get_or_create(
            title='منصة التعلم التكيفي',
            defaults={
                'description': 'منصة تعليمية تتكيف مع مستوى كل طالب تلقائياً',
                'status': 'proposed',
                'supervisor': self.supervisors[2],
                'required_reports': 8,
                'objectives': 'تخصيص المحتوى التعليمي لكل طالب\n'
                              'تتبع التقدم والأداء\n'
                              'تقييم المستمر التلقائي',
                'technologies': 'Python, TensorFlow, Vue.js',
                'deliverables': 'منصة ويب تفاعلية\n'
                                'نموذج تعلم آلي للتخصيص\n'
                                'تقرير المشروع',
            }
        )

        # ── مشروع 4: نظام المراقبة البيئية ──
        self.proj4, _ = Project.objects.get_or_create(
            title='نظام المراقبة البيئية',
            defaults={
                'description': 'شبكة أجهزة استشعار لمراقبة جودة الهواء والتربة',
                'status': 'proposed',
                'supervisor': self.supervisors[3],
                'required_reports': 8,
                'objectives': 'تركيب أجهزة استشعار بيئية\n'
                              'لوحة تحكم لمراقبة البيانات في الوقت الفعلي\n'
                              'نظام تنبيهات عند تجاوز الحدود',
                'technologies': 'IoT, Arduino, Django, React',
                'deliverables': 'شبكة أجهزة الاستشعار\n'
                                'لوحة تحكم ويب\n'
                                'تقرير المشروع',
            }
        )

        # ── مشروع 5: تطبيق تجارة إلكترونية محلية ──
        self.proj5, _ = Project.objects.get_or_create(
            title='تطبيق تجارة إلكترونية محلية',
            defaults={
                'description': 'منصة للتجار المحليين لعرض وبيع منتجاتهم',
                'status': 'proposed',
                'supervisor': self.supervisors[0],
                'required_reports': 8,
                'objectives': 'إنشاء سوق إلكتروني محلي\n'
                              'نظام دفع آمن\n'
                              'تتبع الطلبات والتوصيل',
                'technologies': 'Flutter, Firebase, Stripe',
                'deliverables': 'تطبيق موبايل للتجارة\n'
                                'لوحة تحكم للتجار\n'
                                'تقرير المشروع',
            }
        )

        # ── مشروع 6: نظام السجل الطبي الموحد (مكتمل) ──
        self.proj6, _ = Project.objects.get_or_create(
            title='نظام السجل الطبي الموحد',
            defaults={
                'description': 'نظام مركزي لتخزين وتبادل السجلات الطبية بين المستشفيات',
                'status': 'completed',
                'supervisor': self.supervisors[1],
                'final_grade': 85.0,
                'required_reports': 8,
                'objectives': 'إنشاء قاعدة بيانات موحدة للسجلات الطبية\n'
                              'واجهة برمجة تطبيقات لتبادل البيانات\n'
                              'ضمان الخصوصية والأمان',
                'technologies': 'Java Spring, Oracle, HL7 FHIR',
                'deliverables': 'نظام السجل الطبي المتكامل\n'
                                'API لتبادل البيانات\n'
                                'تقرير المشروع النهائي',
            }
        )
        self.proj6.students.add(
            self.students[10], self.students[11], self.students[12],
            self.students[13], self.students[14],
        )

        # ── مشروع 7: روبوت خدمة العملاء ──
        self.proj7, _ = Project.objects.get_or_create(
            title='روبوت خدمة العملاء',
            defaults={
                'description': 'chatbot ذكي يخدم عملاء الشركات على مدار الساعة',
                'status': 'in_progress',
                'supervisor': self.supervisors[4],
                'required_reports': 8,
                'objectives': 'تطوير chatbot يفهم اللغة الطبيعية\n'
                              'ربط مع قاعدة بيانات الشركات\n'
                              'تحسين تجربة العملاء',
                'technologies': 'Python, GPT API, FastAPI, React',
                'deliverables': 'تطبيق ويب للـ chatbot\n'
                                'نموذج ذكاء اصطناعي مدرّب\n'
                                'تقرير المشروع',
            }
        )
        self.proj7.students.add(
            self.students[15], self.students[16], self.students[17],
            self.students[18], self.students[19],
        )

        # ── مشروع 8: تطبيق إدارة الفعاليات الجامعية ──
        self.proj8, _ = Project.objects.get_or_create(
            title='تطبيق إدارة الفعاليات الجامعية',
            defaults={
                'description': 'منصة لتنظيم وإدارة الفعاليات الطلابية والأكاديمية',
                'status': 'proposed',
                'supervisor': self.supervisors[2],
                'required_reports': 8,
                'objectives': 'إنشاء منصة موحدة لإدارة الفعاليات\n'
                              'نظام حجز المقاعد\n'
                              'تقييم الفعاليات والحضور',
                'technologies': 'Flutter, Django, Firebase',
                'deliverables': 'تطبيق موبايل لإدارة الفعاليات\n'
                                'لوحة تحكم ويب\n'
                                'تقرير المشروع',
            }
        )

        # ── مشروع 9: نظام التعرف على لغة الإشارة ──
        self.proj9, _ = Project.objects.get_or_create(
            title='نظام التعرف على لغة الإشارة',
            defaults={
                'description': 'نظام ذكاء اصطناعي يترجم لغة الإشارة العربية إلى نص صوتي والعكس',
                'status': 'proposed',
                'supervisor': self.supervisors[3],
                'required_reports': 8,
                'objectives': 'تطوير نموذج تعلم عميق للتعرف على حركات اليد\n'
                              'ترجمة الفيديو إلى نص فورية\n'
                              'تطبيق موبايل سهل الاستخدام',
                'technologies': 'Python, MediaPipe, TensorFlow, Flutter',
                'deliverables': 'نموذج الذكاء الاصطناعي المدرب\n'
                                'تطبيق موبايل\n'
                                'تقرير المشروع',
            }
        )

        # ── مشروع 10: منصة إدارة المكتبات الذكية ──
        self.proj10, _ = Project.objects.get_or_create(
            title='منصة إدارة المكتبات الذكية',
            defaults={
                'description': 'نظام ذكي لإدارة المكتبات الجامعية مع توصيات القراءة بالذكاء الاصطناعي',
                'status': 'proposed',
                'supervisor': self.supervisors[4],
                'required_reports': 8,
                'objectives': 'أتمتة إ管理和 استعارة الكتب\n'
                              'نظام توصيات مخصص لكل طالب\n'
                              'بحث ذكي في كتالوج المكتبة',
                'technologies': 'Django, React, Elasticsearch, ML',
                'deliverables': 'نظام إدارة المكتبة\n'
                                'نظام توصيات ذكي\n'
                                'تقرير المشروع',
            }
        )

        # ── مشروع 11: تطبيق مراقبة صحة المسنين ──
        self.proj11, _ = Project.objects.get_or_create(
            title='تطبيق مراقبة صحة المسنين',
            defaults={
                'description': 'تطبيق ذكي لمراقبة صحة كبار السن وإرسال تنبيهات للأهل والأطباء',
                'status': 'proposed',
                'supervisor': self.supervisors[0],
                'required_reports': 8,
                'objectives': 'تتبع العلامات الحيوية للمسنين\n'
                              'نظام تنبيهات طوارئ تلقائي\n'
                              'تواصل مباشر مع الأطباء المعالجين',
                'technologies': 'Flutter, Firebase, IoT Sensors, Python',
                'deliverables': 'تطبيق موبايل للمسنين\n'
                                'لوحة تحكم للأطباء\n'
                                'تقرير المشروع',
            }
        )

        # ── مشروع 12: نظام إدارة الامتحانات الإلكترونية ──
        self.proj12, _ = Project.objects.get_or_create(
            title='نظام إدارة الامتحانات الإلكترونية',
            defaults={
                'description': 'منصة متكاملة لإدارة وتنظيم الامتحانات الإلكترونية مع منع الغش',
                'status': 'proposed',
                'supervisor': self.supervisors[1],
                'required_reports': 8,
                'objectives': 'إنشاء امتحانات إلكترونية آمنة\n'
                              'نظام مراقبة لمنع الغش\n'
                              'تصحيح وتقييم تلقائي',
                'technologies': 'Django, React, WebRTC, AI Proctoring',
                'deliverables': 'منصة الامتحانات\n'
                                'نظام المراقبة\n'
                                'تقرير المشروع',
            }
        )

        self.stdout.write(self.style.SUCCESS('  [OK] 12 projects created (8 proposed, 3 in_progress, 1 completed).'))

    # ─────────────────────────────────────────────
    # JOIN REQUESTS
    # ─────────────────────────────────────────────
    def _create_join_requests(self):
        self.stdout.write('Creating join requests...')
        JoinRequest.objects.get_or_create(
            project=self.proj3, student=self.students[0],
            defaults={'status': 'pending'}
        )
        JoinRequest.objects.get_or_create(
            project=self.proj4, student=self.students[1],
            defaults={'status': 'pending'}
        )
        JoinRequest.objects.get_or_create(
            project=self.proj5, student=self.students[2],
            defaults={'status': 'rejected'}
        )
        JoinRequest.objects.get_or_create(
            project=self.proj8, student=self.students[3],
            defaults={'status': 'pending'}
        )
        JoinRequest.objects.get_or_create(
            project=self.proj9, student=self.students[4],
            defaults={'status': 'pending'}
        )
        self.stdout.write(self.style.SUCCESS('  [OK] 5 join requests created (4 pending, 1 rejected).'))

    # ─────────────────────────────────────────────
    # REPORTS
    # ─────────────────────────────────────────────
    def _create_reports(self):
        self.stdout.write('Creating reports...')
        now = timezone.now()

        # ── مشروع 1 (in_progress) - s1 ──
        Report.objects.get_or_create(
            project=self.proj1, student=self.students[0],
            file_title='تقرير التحليل والتصميم',
            defaults={
                'status': 'accepted',
                'feedback': 'تقرير ممتاز، التحليل والتصميم متكاملاً',
                'uploaded_at': now - timedelta(weeks=6),
            }
        )
        Report.objects.get_or_create(
            project=self.proj1, student=self.students[0],
            file_title='تقرير بناء قاعدة البيانات',
            defaults={
                'status': 'accepted',
                'feedback': 'قاعدة البيانات مصممة بشكل صحيح ومتقن',
                'uploaded_at': now - timedelta(weeks=4),
            }
        )
        Report.objects.get_or_create(
            project=self.proj1, student=self.students[0],
            file_title='تقرير تطوير الواجهة',
            defaults={
                'status': 'accepted',
                'feedback': 'واجهة المستخدم سلسة وسهلة الاستخدام',
                'uploaded_at': now - timedelta(weeks=2),
            }
        )
        Report.objects.get_or_create(
            project=self.proj1, student=self.students[0],
            file_title='تقرير اختبار النظام',
            defaults={
                'status': 'need_work',
                'feedback': 'يرجى إضافة اختبارات الوحدة Unit Tests وتوثيق نتائجها',
                'uploaded_at': now - timedelta(weeks=1),
            }
        )
        Report.objects.get_or_create(
            project=self.proj1, student=self.students[0],
            file_title='تقرير مراجعة الأمان',
            defaults={
                'status': 'pending',
                'uploaded_at': now - timedelta(days=2),
            }
        )

        # ── مشروع 1 (in_progress) - s2 ──
        Report.objects.get_or_create(
            project=self.proj1, student=self.students[1],
            file_title='تقرير تصميم واجهة المستخدم',
            defaults={
                'status': 'accepted',
                'feedback': 'تصميم واجهة احترافي ومتوافق مع المعايير',
                'uploaded_at': now - timedelta(weeks=5),
            }
        )
        Report.objects.get_or_create(
            project=self.proj1, student=self.students[1],
            file_title='تقرير تطوير الواجهة الأمامية',
            defaults={
                'status': 'accepted',
                'feedback': 'الكود نظيف ومنظم، تطبيق أفضل الممارسات',
                'uploaded_at': now - timedelta(weeks=3),
            }
        )

        # ── مشروع 1 (in_progress) - s3 ──
        Report.objects.get_or_create(
            project=self.proj1, student=self.students[2],
            file_title='تقرير تطوير الـ API',
            defaults={
                'status': 'accepted',
                'feedback': 'API موثق بشكل جيد ويعمل بكفاءة',
                'uploaded_at': now - timedelta(weeks=4),
            }
        )
        Report.objects.get_or_create(
            project=self.proj1, student=self.students[2],
            file_title='تقرير اختبارات الأداء',
            defaults={
                'status': 'need_work',
                'feedback': 'يجب إضافة اختبارات الحمل والضغط على النظام',
                'uploaded_at': now - timedelta(weeks=1),
            }
        )

        # ── مشروع 2 (in_progress) - s6 ──
        Report.objects.get_or_create(
            project=self.proj2, student=self.students[5],
            file_title='تقرير دراسة الجدوى',
            defaults={
                'status': 'accepted',
                'feedback': 'دراسة جدوى شاملة ومتقنة',
                'uploaded_at': now - timedelta(weeks=5),
            }
        )
        Report.objects.get_or_create(
            project=self.proj2, student=self.students[5],
            file_title='تقرير النموذج الأولي',
            defaults={
                'status': 'accepted',
                'feedback': 'النموذج الأولي يلبي المتطلبات الأساسية',
                'uploaded_at': now - timedelta(weeks=3),
            }
        )
        Report.objects.get_or_create(
            project=self.proj2, student=self.students[5],
            file_title='تقرير التطوير الأول',
            defaults={
                'status': 'pending',
                'uploaded_at': now - timedelta(days=3),
            }
        )

        # ── مشروع 7 (in_progress) - s16 ──
        Report.objects.get_or_create(
            project=self.proj7, student=self.students[15],
            file_title='تقرير تحليل المتطلبات',
            defaults={
                'status': 'accepted',
                'feedback': 'تحليل متطلبات ممتاز وشامل',
                'uploaded_at': now - timedelta(weeks=4),
            }
        )
        Report.objects.get_or_create(
            project=self.proj7, student=self.students[15],
            file_title='تقرير تطوير الـ API',
            defaults={
                'status': 'need_work',
                'feedback': 'الـ API يحتاج توثيق Swagger وتحسين معالجة الأخطاء',
                'uploaded_at': now - timedelta(weeks=2),
            }
        )

        self.stdout.write(self.style.SUCCESS('  [OK] 10 reports created (various statuses).'))

    # ─────────────────────────────────────────────
    # ANNOUNCEMENTS
    # ─────────────────────────────────────────────
    def _create_announcements(self):
        self.stdout.write('Creating announcements...')
        now = timezone.now()

        self.ann1, _ = Announcement.objects.get_or_create(
            project=self.proj1,
            title='اجتماع مراجعة التقرير الرابع',
            defaults={
                'content': 'نجتمع لمراجعة ملاحظات تقرير اختبار النظام ومناقشة التعديلات المطلوبة',
                'meeting_time': now - timedelta(days=3),
            }
        )

        self.ann2, _ = Announcement.objects.get_or_create(
            project=self.proj1,
            title='موعد تسليم التقرير الخامس',
            defaults={
                'content': 'التذكير بموعد تسليم تقرير مراجعة الأمان. الموعد النهائي خلال أسبوع',
                'meeting_time': now + timedelta(days=7),
            }
        )

        self.ann3, _ = Announcement.objects.get_or_create(
            project=self.proj2,
            title='جلسة عرض النموذج الأولي',
            defaults={
                'content': 'يرجى تجهيز عرض تقديمي للنموذج الأولي مدته 15 دقيقة',
                'meeting_time': now - timedelta(days=7),
            }
        )

        self.stdout.write(self.style.SUCCESS('  [OK] 3 announcements created.'))

    # ─────────────────────────────────────────────
    # ATTENDANCE
    # ─────────────────────────────────────────────
    def _create_attendance(self):
        self.stdout.write('Creating attendance records...')

        # ── مشروع 1: حضور اجتماع مراجعة التقرير الرابع ──
        Attendance.objects.get_or_create(
            announcement=self.ann1, student=self.students[0],
            defaults={'is_present': True}
        )
        Attendance.objects.get_or_create(
            announcement=self.ann1, student=self.students[1],
            defaults={'is_present': True}
        )
        Attendance.objects.get_or_create(
            announcement=self.ann1, student=self.students[2],
            defaults={'is_present': False}
        )
        Attendance.objects.get_or_create(
            announcement=self.ann1, student=self.students[3],
            defaults={'is_present': True}
        )
        Attendance.objects.get_or_create(
            announcement=self.ann1, student=self.students[4],
            defaults={'is_present': True}
        )

        # ── مشروع 2: حضور جلسة عرض النموذج الأولي ──
        Attendance.objects.get_or_create(
            announcement=self.ann3, student=self.students[5],
            defaults={'is_present': True}
        )
        Attendance.objects.get_or_create(
            announcement=self.ann3, student=self.students[6],
            defaults={'is_present': False}
        )
        Attendance.objects.get_or_create(
            announcement=self.ann3, student=self.students[7],
            defaults={'is_present': True}
        )
        Attendance.objects.get_or_create(
            announcement=self.ann3, student=self.students[8],
            defaults={'is_present': True}
        )
        Attendance.objects.get_or_create(
            announcement=self.ann3, student=self.students[9],
            defaults={'is_present': False}
        )

        self.stdout.write(self.style.SUCCESS('  [OK] 10 attendance records created.'))

    # ─────────────────────────────────────────────
    # COMMITTEES
    # ─────────────────────────────────────────────
    def _create_committees(self):
        self.stdout.write('Creating defense committees...')
        now = timezone.now()

        self.committee6, _ = DefenseCommittee.objects.get_or_create(
            project=self.proj6,
            defaults={
                'date': now - timedelta(weeks=2),
                'location': 'قاعة المناقشات A',
                'is_finalized': True,
            }
        )
        self.committee6.examiners.add(
            self.supervisors[0], self.supervisors[3], self.supervisors[4]
        )

        self.committee1, _ = DefenseCommittee.objects.get_or_create(
            project=self.proj1,
            defaults={
                'date': now + timedelta(weeks=2),
                'location': 'قاعة المناقشات B',
                'is_finalized': False,
            }
        )
        self.committee1.examiners.add(
            self.supervisors[0], self.supervisors[1], self.supervisors[2]
        )

        self.stdout.write(self.style.SUCCESS('  [OK] 2 defense committees created.'))

    # ─────────────────────────────────────────────
    # EVALUATIONS
    # ─────────────────────────────────────────────
    def _create_evaluations(self):
        self.stdout.write('Creating evaluations...')

        Evaluation.objects.get_or_create(
            committee=self.committee6, doctor=self.supervisors[0],
            defaults={
                'grade': 88,
                'feedback': 'عمل ممتاز في تصميم قاعدة البيانات والتكامل مع المعايير الطبية',
            }
        )
        Evaluation.objects.get_or_create(
            committee=self.committee6, doctor=self.supervisors[3],
            defaults={
                'grade': 82,
                'feedback': 'واجهة المستخدم سلسة والأداء جيد، يحتاج تحسين في التوثيق',
            }
        )
        Evaluation.objects.get_or_create(
            committee=self.committee6, doctor=self.supervisors[4],
            defaults={
                'grade': 85,
                'feedback': 'الفريق أظهر احترافية عالية في التعامل مع البيانات الحساسة',
            }
        )

        self.stdout.write(self.style.SUCCESS('  [OK] 3 evaluations created (avg=85).'))

    # ─────────────────────────────────────────────
    # NOTIFICATIONS
    # ─────────────────────────────────────────────
    def _create_notifications(self):
        self.stdout.write('Creating notifications...')
        now = timezone.now()

        Notification.objects.get_or_create(
            recipient=self.students[0], project=self.proj1,
            message='تم قبول تقريرك الثالث بنجاح',
            defaults={'is_read': True, 'created_at': now - timedelta(weeks=2)}
        )
        Notification.objects.get_or_create(
            recipient=self.students[0], project=self.proj1,
            message='تقريرك الرابع يحتاج تعديل، راجع ملاحظات المشرف',
            defaults={'is_read': True, 'created_at': now - timedelta(weeks=1)}
        )
        Notification.objects.get_or_create(
            recipient=self.students[0], project=self.proj1,
            message='تذكير: موعد اجتماع المشروع غداً الساعة 10 صباحاً',
            defaults={'is_read': False, 'created_at': now - timedelta(days=2)}
        )

        Notification.objects.get_or_create(
            recipient=self.students[4], project=self.proj9,
            message='تم استلام طلب انضمامك لمشروع التعرف على لغة الإشارة',
            defaults={'is_read': False, 'created_at': now - timedelta(days=3)}
        )

        Notification.objects.get_or_create(
            recipient=self.supervisors[0], project=self.proj5,
            message='طالب جديد أرسل طلب انضمام لمشروع تجارة إلكترونية',
            defaults={'is_read': False, 'created_at': now - timedelta(weeks=1)}
        )
        Notification.objects.get_or_create(
            recipient=self.supervisors[0], project=self.proj1,
            message='تقرير جديد بانتظار مراجعتك في مشروع الصيدليات',
            defaults={'is_read': False, 'created_at': now - timedelta(days=2)}
        )

        self.stdout.write(self.style.SUCCESS('  [OK] 6 notifications created.'))

    # ─────────────────────────────────────────────
    # PRINT SUMMARY
    # ─────────────────────────────────────────────
    def _print_summary(self):
        self.stdout.write('\n' + '=' * 55)
        self.stdout.write(self.style.SUCCESS('  GPMS Database Seeded Successfully!'))
        self.stdout.write('=' * 55)

        self.stdout.write(f'\n  Users:              {User.objects.count()}')
        self.stdout.write(f'  Departments:        {Department.objects.count()}')
        self.stdout.write(f'  Projects:           {Project.objects.count()}')
        self.stdout.write(f'  Join Requests:      {JoinRequest.objects.count()}')
        self.stdout.write(f'  Reports:            {Report.objects.count()}')
        self.stdout.write(f'  Announcements:      {Announcement.objects.count()}')
        self.stdout.write(f'  Attendance:         {Attendance.objects.count()}')
        self.stdout.write(f'  Committees:         {DefenseCommittee.objects.count()}')
        self.stdout.write(f'  Evaluations:        {Evaluation.objects.count()}')
        self.stdout.write(f'  Notifications:      {Notification.objects.count()}')
        self.stdout.write(f'  System Settings:    {SystemSettings.objects.count()}')

        self.stdout.write('\n' + '-' * 55)
        self.stdout.write('  LOGIN CREDENTIALS:')
        self.stdout.write('-' * 55)
        self.stdout.write(f'  {"Role":<14} {"Email":<28} {"Password":<15} {"Status"}')
        self.stdout.write('-' * 55)
        self.stdout.write(f'  {"Dean":<14} {"dean@gpms.edu":<28} {"Dean@2025":<15} Full access')
        self.stdout.write(f'  {"HOD":<14} {"hod@gpms.edu":<28} {"Hod@2025":<15} Full access')
        self.stdout.write(f'  {"HOD":<14} {"hod2@gpms.edu":<28} {"Hod2@2025":<15} Full access')
        self.stdout.write(f'  {"Supervisor":<14} {"supervisor1@gpms.edu":<28} {"Sup@2025":<15} 2 projects')
        self.stdout.write(f'  {"Supervisor":<14} {"supervisor2@gpms.edu":<28} {"Sup@2025":<15} 2 projects')
        self.stdout.write(f'  {"Supervisor":<14} {"supervisor3@gpms.edu":<28} {"Sup@2025":<15} 2 projects')
        self.stdout.write(f'  {"Supervisor":<14} {"supervisor4@gpms.edu":<28} {"Sup@2025":<15} 1 project')
        self.stdout.write(f'  {"Supervisor":<14} {"supervisor5@gpms.edu":<28} {"Sup@2025":<15} 1 project')
        self.stdout.write(f'  {"Student":<14} {"s1@gpms.edu":<28} {"Student@2025":<15} In project + reports')
        self.stdout.write(f'  {"Student":<14} {"s11@gpms.edu":<28} {"Student@2025":<15} Pending join request')
        self.stdout.write(f'  {"Student":<14} {"s13@gpms.edu":<28} {"Student@2025":<15} Rejected request')
        self.stdout.write(f'  {"Student":<14} {"s15@gpms.edu":<28} {"Student@2025":<15} No project')
        self.stdout.write('-' * 55)
        self.stdout.write('')
