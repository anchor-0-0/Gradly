from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Project, Report, SystemSettings, JoinRequest, Notification, Announcement, Attendance, DefenseCommittee, Evaluation


class AuthTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/register/'
        self.login_url = '/api/login/'
        self.user_data = {
            'username': 'test@example.com',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }

    def test_register_success(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_register_duplicate_email(self):
        self.client.post(self.register_url, self.user_data, format='json')
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        self.client.post(self.register_url, self.user_data, format='json')
        response = self.client.post(self.login_url, {
            'username': 'test@example.com',
            'password': 'testpass123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('is_staff', response.data)

    def test_login_wrong_password(self):
        self.client.post(self.register_url, self.user_data, format='json')
        response = self.client.post(self.login_url, {
            'username': 'test@example.com',
            'password': 'wrongpass'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProjectTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        SystemSettings.objects.create(max_students_per_project=5)

        self.supervisor = User.objects.create_user(
            username='supervisor@test.com', email='supervisor@test.com',
            password='pass1234', is_staff=True
        )
        self.student = User.objects.create_user(
            username='student@test.com', email='student@test.com',
            password='pass1234'
        )

    def test_list_projects_unauthenticated(self):
        response = self.client.get('/api/projects/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_supervisor_create_project(self):
        self.client.force_authenticate(user=self.supervisor)
        response = self.client.post('/supervisor/create-project/', {
            'title': 'مشروع الذكاء الاصطناعي',
            'description': 'وصف المشروع'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)
        project = Project.objects.first()
        self.assertEqual(project.status, 'proposed')
        self.assertEqual(project.supervisor, self.supervisor)

    def test_supervisor_create_project_unauthenticated(self):
        response = self.client.post('/supervisor/create-project/', {
            'title': 'مشروع',
            'description': 'وصف'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_proposed_projects(self):
        self.client.force_authenticate(user=self.student)
        Project.objects.create(title='مشروع 1', description='وصف', supervisor=self.supervisor, status='proposed')
        Project.objects.create(title='مشروع 2', description='وصف', supervisor=self.supervisor, status='in_progress')
        response = self.client.get('/api/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_supervisor_manage_project_own(self):
        self.client.force_authenticate(user=self.supervisor)
        project = Project.objects.create(title='مشروع', description='وصف', supervisor=self.supervisor, status='proposed')
        response = self.client.patch(f'/supervisor/manage-project/{project.id}/', {
            'title': 'مشروع معدل'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertEqual(project.title, 'مشروع معدل')

    def test_supervisor_manage_project_not_own(self):
        other_supervisor = User.objects.create_user(
            username='other@test.com', email='other@test.com', password='pass1234', is_staff=True
        )
        self.client.force_authenticate(user=self.supervisor)
        project = Project.objects.create(title='مشروع', description='وصف', supervisor=other_supervisor, status='proposed')
        response = self.client.patch(f'/supervisor/manage-project/{project.id}/', {
            'title': 'مشروع معدل'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class JoinRequestTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        SystemSettings.objects.create(max_students_per_project=5)

        self.supervisor = User.objects.create_user(
            username='sup@test.com', email='sup@test.com', password='pass1234', is_staff=True
        )
        self.student1 = User.objects.create_user(
            username='st1@test.com', email='st1@test.com', password='pass1234'
        )
        self.student2 = User.objects.create_user(
            username='st2@test.com', email='st2@test.com', password='pass1234'
        )
        self.project = Project.objects.create(
            title='مشروع', description='وصف', supervisor=self.supervisor, status='proposed'
        )

    def test_join_project_success(self):
        self.client.force_authenticate(user=self.student1)
        response = self.client.post(f'/api/projects/{self.project.id}/join/', {
            'emails': ['st1@test.com']
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(JoinRequest.objects.count(), 1)

    def test_reject_join_request(self):
        self.client.force_authenticate(user=self.student1)
        self.client.post(f'/api/projects/{self.project.id}/join/', {
            'emails': ['st1@test.com']
        }, format='json')

        self.client.force_authenticate(user=self.supervisor)
        join_request = JoinRequest.objects.first()
        response = self.client.post(f'/api/join_request/{join_request.id}/reject/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        join_request.refresh_from_db()
        self.assertEqual(join_request.status, 'rejected')
        self.assertNotIn(self.student1, self.project.students.all())

    def test_join_project_invalid_email(self):
        self.client.force_authenticate(user=self.student1)
        response = self.client.post(f'/api/projects/{self.project.id}/join/', {
            'emails': ['notfound@test.com']
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_approve_join_request(self):
        self.client.force_authenticate(user=self.student1)
        self.client.post(f'/api/projects/{self.project.id}/join/', {
            'emails': ['st1@test.com']
        }, format='json')

        self.client.force_authenticate(user=self.supervisor)
        join_request = JoinRequest.objects.first()
        response = self.client.post(f'/api/join_request/{join_request.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertIn(self.student1, self.project.students.all())

    def test_approve_join_request_wrong_supervisor(self):
        other_sup = User.objects.create_user(
            username='othersup@test.com', email='othersup@test.com', password='pass1234', is_staff=True
        )
        self.client.force_authenticate(user=self.student1)
        self.client.post(f'/api/projects/{self.project.id}/join/', {
            'emails': ['st1@test.com']
        }, format='json')

        self.client.force_authenticate(user=other_sup)
        join_request = JoinRequest.objects.first()
        response = self.client.post(f'/api/join_request/{join_request.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ReportTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        SystemSettings.objects.create(max_students_per_project=5)

        self.supervisor = User.objects.create_user(
            username='sup@test.com', email='sup@test.com', password='pass1234', is_staff=True
        )
        self.student = User.objects.create_user(
            username='st@test.com', email='st@test.com', password='pass1234'
        )
        self.project = Project.objects.create(
            title='مشروع', description='وصف', supervisor=self.supervisor, status='in_progress'
        )
        self.project.students.add(self.student)

    def test_upload_report(self):
        self.client.force_authenticate(user=self.student)
        file = SimpleUploadedFile("report.pdf", b"file_content", content_type="application/pdf")
        response = self.client.post('/api/reports/upload/', {
            'file_title': 'التقرير الأول',
            'file': file,
            'project': self.project.id
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Report.objects.count(), 1)

    def test_upload_report_not_in_project(self):
        other_student = User.objects.create_user(
            username='other@test.com', email='other@test.com', password='pass1234'
        )
        self.client.force_authenticate(user=other_student)
        file = SimpleUploadedFile("report.pdf", b"content", content_type="application/pdf")
        response = self.client.post('/api/reports/upload/', {
            'file_title': 'تقرير',
            'file': file,
            'project': self.project.id
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervisor_evaluate_report(self):
        self.client.force_authenticate(user=self.student)
        file = SimpleUploadedFile("report.pdf", b"content", content_type="application/pdf")
        self.client.post('/api/reports/upload/', {
            'file_title': 'تقرير', 'file': file, 'project': self.project.id
        }, format='multipart')

        self.client.force_authenticate(user=self.supervisor)
        report = Report.objects.first()
        response = self.client.patch(f'/supervisor/evaluate-report/{report.id}/', {
            'status': 'accepted',
            'feedback': 'ممتاز'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report.refresh_from_db()
        self.assertEqual(report.status, 'accepted')
        self.assertEqual(report.feedback, 'ممتاز')

    def test_student_my_reports(self):
        self.client.force_authenticate(user=self.student)
        file = SimpleUploadedFile("report.pdf", b"content", content_type="application/pdf")
        self.client.post('/api/reports/upload/', {
            'file_title': 'تقرير', 'file': file, 'project': self.project.id
        }, format='multipart')

        response = self.client.get('/my-reports/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class NotificationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='user@test.com', email='user@test.com', password='pass1234'
        )
        Notification.objects.create(recipient=self.user, message='إشعار 1')
        Notification.objects.create(recipient=self.user, message='إشعار 2')

    def test_get_notifications(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/my-notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_notifications_unauthenticated(self):
        response = self.client.get('/my-notifications/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AnnouncementAndAttendanceTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        SystemSettings.objects.create(max_students_per_project=3)

        self.supervisor = User.objects.create_user(
            username='sup@test.com', email='sup@test.com', password='pass1234', is_staff=True
        )
        self.student = User.objects.create_user(
            username='st@test.com', email='st@test.com', password='pass1234'
        )
        self.project = Project.objects.create(
            title='مشروع', description='وصف', supervisor=self.supervisor, status='in_progress'
        )
        self.project.students.add(self.student)

    def test_create_announcement(self):
        self.client.force_authenticate(user=self.supervisor)
        response = self.client.post('/announcements/create/', {
            'project': self.project.id,
            'content': 'اجتماع غداً',
            'meeting_time': '2026-12-31T10:00:00Z'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Announcement.objects.count(), 1)
        self.assertEqual(Attendance.objects.count(), 1)

    def test_mark_attendance(self):
        self.client.force_authenticate(user=self.supervisor)
        self.client.post('/announcements/create/', {
            'project': self.project.id,
            'content': 'اجتماع',
            'meeting_time': '2026-12-31T10:00:00Z'
        }, format='json')

        announcement = Announcement.objects.first()
        response = self.client.post(f'/announcements/{announcement.id}/mark-attendance/', {
            'attendance_list': [{'username': self.student.username, 'is_present': True}]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        attendance = Attendance.objects.first()
        self.assertTrue(attendance.is_present)


class StudentDashboardTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        SystemSettings.objects.create(max_students_per_project=5)

        self.supervisor = User.objects.create_user(
            username='sup@test.com', email='sup@test.com', password='pass1234', is_staff=True
        )
        self.student = User.objects.create_user(
            username='st@test.com', email='st@test.com', password='pass1234'
        )
        self.project = Project.objects.create(
            title='مشروع', description='وصف', supervisor=self.supervisor, status='in_progress',
            required_reports=8
        )
        self.project.students.add(self.student)

    def test_student_dashboard(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get('/student/project_dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['project_title'], 'مشروع')
        self.assertEqual(response.data['progress'], 0)

    def test_student_dashboard_no_project(self):
        other_student = User.objects.create_user(
            username='other@test.com', email='other@test.com', password='pass1234'
        )
        self.client.force_authenticate(user=other_student)
        response = self.client.get('/student/project_dashboard/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_dashboard_with_progress(self):
        file = SimpleUploadedFile("report.pdf", b"content", content_type="application/pdf")
        for i in range(4):
            Report.objects.create(
                project=self.project, student=self.student,
                file_title=f'تقرير {i+1}', file=file, status='accepted'
            )
        self.client.force_authenticate(user=self.student)
        response = self.client.get('/student/project_dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['accepted_reports'], 4)
        self.assertEqual(response.data['progress'], 50.0)


class SupervisorDashboardTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.supervisor = User.objects.create_user(
            username='sup@test.com', email='sup@test.com', password='pass1234', is_staff=True
        )
        Project.objects.create(title='مشروع 1', description='وصف', supervisor=self.supervisor)

    def test_supervisor_dashboard(self):
        self.client.force_authenticate(user=self.supervisor)
        response = self.client.get('/supervisor/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('stats', response.data)

    def test_my_projects(self):
        self.client.force_authenticate(user=self.supervisor)
        response = self.client.get('/my_projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class HeadDepartmentTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.head = User.objects.create_user(
            username='head@test.com', email='head@test.com', password='pass1234', is_superuser=True
        )
        self.supervisor = User.objects.create_user(
            username='sup@test.com', email='sup@test.com', password='pass1234', is_staff=True
        )
        self.project = Project.objects.create(
            title='مشروع', description='وصف', supervisor=self.supervisor, status='completed'
        )

    def test_head_list_projects(self):
        self.client.force_authenticate(user=self.head)
        response = self.client.get('/head/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_head_project_details(self):
        self.client.force_authenticate(user=self.head)
        response = self.client.get(f'/head/projects/{self.project.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'مشروع')

    def test_non_head_cannot_access_projects(self):
        self.client.force_authenticate(user=self.supervisor)
        response = self.client.get('/head/projects/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminDashboardTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.dean_group = Group.objects.create(name='Dean')
        self.dean = User.objects.create_user(
            username='dean@test.com', email='dean@test.com', password='pass1234'
        )
        self.dean.groups.add(self.dean_group)

    def test_admin_dashboard_dean_allowed(self):
        self.client.force_authenticate(user=self.dean)
        response = self.client.get('/api/admin/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('stats', response.data)

    def test_admin_dashboard_head_of_department_blocked(self):
        head = User.objects.create_user(
            username='head@test.com', email='head@test.com', password='pass1234', is_superuser=True
        )
        self.client.force_authenticate(user=head)
        response = self.client.get('/api/admin/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_dashboard_supervisor_blocked(self):
        sup = User.objects.create_user(
            username='sup@test.com', email='sup@test.com', password='pass1234', is_staff=True
        )
        self.client.force_authenticate(user=sup)
        response = self.client.get('/api/admin/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_dashboard_student_blocked(self):
        student = User.objects.create_user(
            username='st@test.com', email='st@test.com', password='pass1234'
        )
        self.client.force_authenticate(user=student)
        response = self.client.get('/api/admin/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DefenseCommitteeTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.head = User.objects.create_user(
            username='head@test.com', email='head@test.com', password='pass1234', is_superuser=True
        )
        self.supervisor = User.objects.create_user(
            username='sup@test.com', email='sup@test.com', password='pass1234', is_staff=True
        )
        self.student = User.objects.create_user(
            username='st@test.com', email='st@test.com', password='pass1234'
        )
        self.project = Project.objects.create(
            title='مشروع', description='وصف', supervisor=self.supervisor, status='completed'
        )
        self.project.students.add(self.student)

    def test_create_committee(self):
        self.client.force_authenticate(user=self.head)
        response = self.client.post('/committees/', {
            'project': self.project.id,
            'examiners': [self.head.id, self.supervisor.id],
            'date': '2026-12-31T10:00:00Z',
            'location': 'مدرج A'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DefenseCommittee.objects.count(), 1)

    def test_finalize_result(self):
        self.client.force_authenticate(user=self.head)
        response = self.client.post('/committees/', {
            'project': self.project.id,
            'examiners': [self.head.id, self.supervisor.id],
            'date': '2026-12-31T10:00:00Z',
            'location': 'مدرج A'
        }, format='json')
        committee = DefenseCommittee.objects.first()

        Evaluation.objects.create(committee=committee, doctor=self.head, grade=85)

        response = self.client.post(f'/committees/{committee.id}/finalize/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('final_grade', response.data)
        self.project.refresh_from_db()
        self.assertEqual(self.project.final_grade, 85)
