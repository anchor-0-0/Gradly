from django.db import migrations
from django.contrib.auth.models import Group
from django.contrib.auth.hashers import make_password


def setup_departments_and_data(apps, schema_editor):
    Department = apps.get_model('api', 'Department')
    UserProfile = apps.get_model('api', 'UserProfile')
    Project = apps.get_model('api', 'Project')
    User = apps.get_model('auth', 'User')
    Group = apps.get_model('auth', 'Group')
    
    # ============= 1. Clean up departments =============
    # Delete the separate SE and IS departments
    Department.objects.filter(code__in=['SE', 'IS']).delete()
    
    # Create/Update the 3 target departments
    dept_ai, _ = Department.objects.update_or_create(
        code='AI',
        defaults={'name': 'الذكاء الاصطناعي', 'description': 'قسم الذكاء الاصطناعي وتعلم الآلة'}
    )
    dept_se_is, _ = Department.objects.update_or_create(
        code='SEIS',
        defaults={'name': 'هندسة البرمجيات ونظم المعلومات', 'description': 'قسم هندسة البرمجيات وأنظمة المعلومات'}
    )
    dept_ne, _ = Department.objects.update_or_create(
        code='NE',
        defaults={'name': 'هندسة الشبكات والنظم الحاسوبية', 'description': 'قسم هندسة الشبكات والنظم الحاسوبية'}
    )
    
    departments = [dept_ai, dept_se_is, dept_ne]
    
    # ============= 2. Create/Update HODs (one per department) =============
    hod_group, _ = Group.objects.get_or_create(name='HOD')
    supervisor_group, _ = Group.objects.get_or_create(name='Supervisor')
    student_group, _ = Group.objects.get_or_create(name='Student')
    
    hod_data = [
        {'username': 'hod_ai@gpms.edu', 'email': 'hod_ai@gpms.edu', 'dept': dept_ai},
        {'username': 'hod_seis@gpms.edu', 'email': 'hod_seis@gpms.edu', 'dept': dept_se_is},
        {'username': 'hod_ne@gpms.edu', 'email': 'hod_ne@gpms.edu', 'dept': dept_ne},
    ]
    
    for hod in hod_data:
        user, created = User.objects.get_or_create(
            username=hod['username'],
            defaults={'email': hod['email'], 'is_staff': True, 'password': make_password('Hod@2025')}
        )
        if created:
            user.password = make_password('Hod@2025')
            user.save()
        user.groups.add(hod_group)
        user.is_staff = True
        user.save()
        
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.department = hod['dept']
        profile.save()
        
        # Set as department head
        hod['dept'].head = user
        hod['dept'].save()
    
    # ============= 3. Assign supervisors to departments =============
    supervisor_emails = [
        ('supervisor1@gpms.edu', dept_ai),
        ('supervisor2@gpms.edu', dept_ai),
        ('supervisor3@gpms.edu', dept_se_is),
        ('supervisor4@gpms.edu', dept_se_is),
        ('supervisor5@gpms.edu', dept_ne),
    ]
    
    for email, dept in supervisor_emails:
        try:
            user = User.objects.get(username=email)
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.department = dept
            profile.save()
        except User.DoesNotExist:
            pass
    
    # ============= 4. Assign projects to departments =============
    projects = list(Project.objects.all().order_by('id'))
    projects_per_dept = len(projects) // 3
    
    for i, project in enumerate(projects):
        if i < projects_per_dept:
            project.department = dept_ai
        elif i < projects_per_dept * 2:
            project.department = dept_se_is
        else:
            project.department = dept_ne
        project.save()
    
    # ============= 5. Assign students to departments based on their project =============
    students = User.objects.filter(groups__name='Student')
    
    for student in students:
        profile, _ = UserProfile.objects.get_or_create(user=student)
        
        # Find student's project through project membership
        student_projects = Project.objects.filter(students=student)
        if student_projects.exists():
            profile.department = student_projects.first().department
        else:
            # Distribute evenly if no project
            student_index = student.id % 3
            if student_index == 0:
                profile.department = dept_ai
            elif student_index == 1:
                profile.department = dept_se_is
            else:
                profile.department = dept_ne
        profile.save()


def reverse_setup(apps, schema_editor):
    Department = apps.get_model('api', 'Department')
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('api', 'UserProfile')
    Project = apps.get_model('api', 'Project')
    
    # Remove created HODs
    User.objects.filter(username__in=['hod_ai@gpms.edu', 'hod_seis@gpms.edu', 'hod_ne@gpms.edu']).delete()
    
    # Reset departments
    Department.objects.filter(code__in=['AI', 'SEIS', 'NE']).delete()
    
    # Restore original SE and IS
    Department.objects.get_or_create(code='SE', defaults={'name': 'قسم هندسة البرمجيات'})
    Department.objects.get_or_create(code='IS', defaults={'name': 'قسم نظم المعلومات'})
    
    # Remove department from projects
    Project.objects.all().update(department=None)
    
    # Remove department from user profiles
    UserProfile.objects.all().update(department=None)


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_add_department_to_project'),
    ]

    operations = [
        migrations.RunPython(setup_departments_and_data, reverse_setup),
    ]