from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_remove_userprofile_about_repair_animal_statuses'),
    ]

    operations = [
        migrations.AddField(
            model_name='adoptionapplication',
            name='contact_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Planowany kontakt'),
        ),
        migrations.AddField(
            model_name='adoptionapplication',
            name='contact_message',
            field=models.TextField(blank=True, verbose_name='Informacja dla adoptującego'),
        ),
    ]
