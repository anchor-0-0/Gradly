from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0017_seed_departments'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='department',
            field=models.ForeignKey(
                blank=True, 
                null=True, 
                on_delete=django.db.models.deletion.SET_NULL, 
                related_name='projects', 
                to='api.department'
            ),
        ),
    ]