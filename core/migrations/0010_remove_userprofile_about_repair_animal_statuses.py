from django.db import migrations


def repair_animal_statuses(apps, schema_editor):
    Animal = apps.get_model('core', 'Animal')
    AdoptionApplication = apps.get_model('core', 'AdoptionApplication')

    for animal in Animal.objects.all():
        approved_exists = AdoptionApplication.objects.filter(animal=animal, status='approved').exists()
        active_exists = AdoptionApplication.objects.filter(animal=animal, status__in=['new', 'review']).exists()

        if approved_exists:
            new_status = 'adopted'
        elif active_exists and animal.status != 'adopted':
            new_status = 'pending'
        elif animal.status == 'pending':
            new_status = 'available'
        else:
            new_status = animal.status

        if animal.status != new_status:
            animal.status = new_status
            animal.save(update_fields=['status'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_userprofile_contactmessage_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='about',
        ),
        migrations.RunPython(repair_animal_statuses, migrations.RunPython.noop),
    ]
