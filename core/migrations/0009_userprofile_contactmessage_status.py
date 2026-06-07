from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def sync_message_status(apps, schema_editor):
    ContactMessage = apps.get_model('core', 'ContactMessage')
    ContactMessage.objects.filter(is_read=True).update(status='resolved')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_remove_favorite_unique_favorite_per_user_animal_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='animal',
            name='animal_urgency_idx',
        ),
        migrations.RemoveField(
            model_name='animal',
            name='urgency',
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(blank=True, max_length=150, verbose_name='Imię i nazwisko')),
                ('phone_number', models.CharField(blank=True, max_length=9, verbose_name='Numer telefonu')),
                ('about', models.TextField(blank=True, verbose_name='Kilka slow o sobie')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL, verbose_name='Użytkownik')),
            ],
            options={
                'ordering': ['user__username'],
            },
        ),
        migrations.AddField(
            model_name='contactmessage',
            name='status',
            field=models.CharField(choices=[('pending', 'Oczekuje'), ('resolved', 'Rozwiązane')], default='pending', max_length=20, verbose_name='Status'),
        ),
        migrations.AddIndex(
            model_name='contactmessage',
            index=models.Index(fields=['status'], name='contact_status_idx'),
        ),
        migrations.RunPython(sync_message_status, migrations.RunPython.noop),
    ]
