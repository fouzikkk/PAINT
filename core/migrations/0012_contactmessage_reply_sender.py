from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0011_adoptionapplication_contact_info'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactmessage',
            name='sender',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contact_messages', to=settings.AUTH_USER_MODEL, verbose_name='Użytkownik'),
        ),
        migrations.AddField(
            model_name='contactmessage',
            name='reply',
            field=models.TextField(blank=True, verbose_name='Odpowiedź administratora'),
        ),
        migrations.AddField(
            model_name='contactmessage',
            name='replied_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contact_message_replies', to=settings.AUTH_USER_MODEL, verbose_name='Odpowiedział'),
        ),
        migrations.AddField(
            model_name='contactmessage',
            name='replied_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Data odpowiedzi'),
        ),
    ]
