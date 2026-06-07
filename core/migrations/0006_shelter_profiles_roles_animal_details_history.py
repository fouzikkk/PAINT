import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_favorite'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='shelter',
            name='email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='Adres e-mail'),
        ),
        migrations.AddField(
            model_name='shelter',
            name='phone',
            field=models.CharField(blank=True, max_length=30, verbose_name='Telefon'),
        ),
        migrations.AddField(
            model_name='animal',
            name='breed',
            field=models.CharField(blank=True, max_length=120, verbose_name='Rasa'),
        ),
        migrations.AddField(
            model_name='animal',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='animal',
            name='gender',
            field=models.CharField(choices=[('unknown', 'Nieznana'), ('female', 'Samica'), ('male', 'Samiec')], default='unknown', max_length=10, verbose_name='Płeć'),
        ),
        migrations.AddField(
            model_name='animal',
            name='good_with_cats',
            field=models.BooleanField(default=False, verbose_name='Dobry kontakt z kotami'),
        ),
        migrations.AddField(
            model_name='animal',
            name='good_with_children',
            field=models.BooleanField(default=False, verbose_name='Dobry kontakt z dziećmi'),
        ),
        migrations.AddField(
            model_name='animal',
            name='good_with_dogs',
            field=models.BooleanField(default=False, verbose_name='Dobry kontakt z psami'),
        ),
        migrations.AddField(
            model_name='animal',
            name='is_chipped',
            field=models.BooleanField(default=False, verbose_name='Chip'),
        ),
        migrations.AddField(
            model_name='animal',
            name='is_sterilized',
            field=models.BooleanField(default=False, verbose_name='Sterylizacja'),
        ),
        migrations.AddField(
            model_name='animal',
            name='is_vaccinated',
            field=models.BooleanField(default=False, verbose_name='Szczepienia'),
        ),
        migrations.AddField(
            model_name='animal',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='animal',
            name='urgency',
            field=models.CharField(choices=[('standard', 'Standardowa'), ('high', 'Pilna')], default='standard', max_length=20, verbose_name='Pilnosc adopcji'),
        ),
        migrations.AddField(
            model_name='animal',
            name='weight_kg',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='Waga w kg'),
        ),
        migrations.AlterField(
            model_name='shelter',
            name='city',
            field=models.CharField(db_index=True, max_length=100, verbose_name='Miasto'),
        ),
        migrations.CreateModel(
            name='ShelterStaff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('manager', 'Kierownik'), ('staff', 'Pracownik')], default='staff', max_length=20, verbose_name='Rola')),
                ('is_active', models.BooleanField(default=True, verbose_name='Aktywny')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('shelter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff_memberships', to='core.shelter', verbose_name='Schronisko')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shelter_roles', to=settings.AUTH_USER_MODEL, verbose_name='Użytkownik')),
            ],
            options={
                'ordering': ['shelter__city', 'user__username'],
            },
        ),
        migrations.CreateModel(
            name='ApplicationStatusHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_status', models.CharField(choices=[('new', 'Nowe zgłoszenie'), ('review', 'W analizie'), ('approved', 'Zatwierdzone'), ('rejected', 'Odrzucone')], max_length=20, verbose_name='Poprzedni status')),
                ('new_status', models.CharField(choices=[('new', 'Nowe zgłoszenie'), ('review', 'W analizie'), ('approved', 'Zatwierdzone'), ('rejected', 'Odrzucone')], max_length=20, verbose_name='Nowy status')),
                ('note', models.TextField(blank=True, verbose_name='Notatka')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_history', to='core.adoptionapplication', verbose_name='Wniosek')),
                ('changed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='application_status_changes', to=settings.AUTH_USER_MODEL, verbose_name='Zmienione przez')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='animal',
            index=models.Index(fields=['gender'], name='animal_gender_idx'),
        ),
        migrations.AddIndex(
            model_name='animal',
            index=models.Index(fields=['urgency'], name='animal_urgency_idx'),
        ),
        migrations.AddIndex(
            model_name='animal',
            index=models.Index(fields=['created_at'], name='animal_created_idx'),
        ),
        migrations.AddIndex(
            model_name='shelterstaff',
            index=models.Index(fields=['is_active'], name='shelter_staff_active_idx'),
        ),
        migrations.AddIndex(
            model_name='applicationstatushistory',
            index=models.Index(fields=['created_at'], name='app_history_created_idx'),
        ),
        migrations.AddIndex(
            model_name='applicationstatushistory',
            index=models.Index(fields=['new_status'], name='app_history_status_idx'),
        ),
        migrations.AddConstraint(
            model_name='shelter',
            constraint=models.UniqueConstraint(fields=('name', 'city'), name='unique_shelter_name_city'),
        ),
        migrations.AddConstraint(
            model_name='shelterstaff',
            constraint=models.UniqueConstraint(fields=('user', 'shelter'), name='unique_user_shelter_role'),
        ),
    ]
