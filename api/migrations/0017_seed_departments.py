from django.db import migrations

def seed_departments(apps, schema_editor):
    Department = apps.get_model('api', 'Department')
    departments = [
        {'name': 'الذكاء الاصطناعي', 'code': 'AI', 'description': 'قسم الذكاء الاصطناعي وتعلم الآلة'},
        {'name': 'هندسة البرمجيات ونظم المعلومات', 'code': 'SE', 'description': 'قسم هندسة البرمجيات وأنظمة المعلومات'},
        {'name': 'هندسة الشبكات والنظم الحاسوبية', 'code': 'NE', 'description': 'قسم هندسة الشبكات والنظم الحاسوبية'},
    ]
    for dept in departments:
        Department.objects.get_or_create(
            code=dept['code'],
            defaults=dept,
        )

def reverse_seed(apps, schema_editor):
    Department = apps.get_model('api', 'Department')
    Department.objects.filter(code__in=['AI', 'SE', 'NE']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_passwordresetcode_announcement_title_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_departments, reverse_seed),
    ]
