from django.db import migrations, models


def map_student_status_to_registration_type(apps, schema_editor):
    RegistrationInfo = apps.get_model('web', 'RegistrationInfo')
    for registration in RegistrationInfo.objects.all():
        if hasattr(registration, 'student_status'):
            registration.registration_type = 'attendee' if registration.student_status == 0 else 'src'
            registration.save(update_fields=['registration_type'])


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0003_remove_registrationinfo_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrationinfo',
            name='affiliation',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='registrationinfo',
            name='registration_type',
            field=models.CharField(
                choices=[
                    ('regular', 'Regular Registration'),
                    ('src', 'SRC Registration'),
                    ('attendee', 'Attendee / Non-Author Registration'),
                    ('phd', 'PhD Research Track'),
                    ('secondary', 'Supplementary Registration'),
                ],
                default='regular',
                max_length=20,
            ),
        ),
        migrations.RunPython(map_student_status_to_registration_type, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='registrationinfo',
            name='student_status',
        ),
    ]
