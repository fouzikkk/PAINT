from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Shelter(models.Model):
    name = models.CharField(max_length=255, verbose_name='Nazwa schroniska')
    city = models.CharField(max_length=100, db_index=True, verbose_name='Miasto')
    address = models.TextField(verbose_name='Adres')
    phone = models.CharField(max_length=9, blank=True, verbose_name='Telefon')
    email = models.EmailField(blank=True, verbose_name='Adres e-mail')

    class Meta:
        ordering = ['city']
        constraints = [
            models.UniqueConstraint(fields=['name', 'city'], name='unique_shelter_name_city'),
        ]

    def __str__(self):
        return f'{self.name} ({self.city})'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='Użytkownik')
    full_name = models.CharField(max_length=150, blank=True, verbose_name='Imię i nazwisko')
    phone_number = models.CharField(max_length=9, blank=True, verbose_name='Numer telefonu')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return f'Profil: {self.user.username}'


class Animal(models.Model):
    STATUS_CHOICES = [
        ('available', 'Dostępny'),
        ('pending', 'W trakcie adopcji'),
        ('adopted', 'Adoptowany'),
    ]
    SPECIES_CHOICES = [('pies', 'Pies'), ('kot', 'Kot')]
    SIZE_CHOICES = [('maly', 'Mały'), ('sredni', 'Średni'), ('duzy', 'Duży')]
    GENDER_CHOICES = [('unknown', 'Nieznana'), ('female', 'Samica'), ('male', 'Samiec')]

    name = models.CharField(max_length=100, verbose_name='Imię')
    species = models.CharField(max_length=10, choices=SPECIES_CHOICES, verbose_name='Gatunek')
    age = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(40)], verbose_name='Wiek w latach')
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, default='sredni', verbose_name='Wielkość')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unknown', verbose_name='Płeć')
    breed = models.CharField(max_length=120, blank=True, verbose_name='Rasa')
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name='Waga w kg')
    is_sterilized = models.BooleanField(default=False, verbose_name='Sterylizacja')
    is_vaccinated = models.BooleanField(default=False, verbose_name='Szczepienia')
    is_chipped = models.BooleanField(default=False, verbose_name='Chip')
    good_with_children = models.BooleanField(default=False, verbose_name='Dobry kontakt z dziećmi')
    good_with_cats = models.BooleanField(default=False, verbose_name='Dobry kontakt z kotami')
    good_with_dogs = models.BooleanField(default=False, verbose_name='Dobry kontakt z psami')
    description = models.TextField(verbose_name='Opis')
    shelter = models.ForeignKey(Shelter, on_delete=models.CASCADE, related_name='animals', verbose_name='Schronisko')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name='Status')
    image = models.ImageField(upload_to='animals/', blank=True, null=True, verbose_name='Zdjęcie')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['status'], name='animal_status_idx'),
            models.Index(fields=['species'], name='animal_species_idx'),
            models.Index(fields=['size'], name='animal_size_idx'),
            models.Index(fields=['age'], name='animal_age_idx'),
            models.Index(fields=['gender'], name='animal_gender_idx'),
            models.Index(fields=['created_at'], name='animal_created_idx'),
        ]

    def __str__(self):
        return self.name


class AdoptionApplication(models.Model):
    STATUS_CHOICES = [
        ('new', 'Nowe zgłoszenie'),
        ('review', 'W analizie'),
        ('approved', 'Zatwierdzone'),
        ('rejected', 'Odrzucone'),
    ]

    animal = models.ForeignKey(Animal, on_delete=models.PROTECT, related_name='applications', verbose_name='Zwierzę')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications', verbose_name='Aplikujący')
    applicant_name = models.CharField(max_length=150, blank=True, verbose_name='Imię i nazwisko')
    applicant_email = models.EmailField(blank=True, verbose_name='Adres e-mail')
    phone_number = models.CharField(max_length=9, verbose_name='Numer telefonu')
    experience = models.TextField(verbose_name='Doświadczenie ze zwierzętami', blank=True)
    living_conditions = models.TextField(verbose_name='Warunki mieszkaniowe', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='Status wniosku')
    contact_at = models.DateTimeField(blank=True, null=True, verbose_name='Planowany kontakt')
    contact_message = models.TextField(blank=True, verbose_name='Informacja dla adoptującego')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['animal', 'applicant'], name='unique_application_per_user_animal'),
        ]
        indexes = [
            models.Index(fields=['status'], name='application_status_idx'),
            models.Index(fields=['created_at'], name='application_created_idx'),
        ]

    def __str__(self):
        return f'Wniosek - {self.animal.name} od {self.applicant.username}'


class ApplicationStatusHistory(models.Model):
    application = models.ForeignKey(AdoptionApplication, on_delete=models.CASCADE, related_name='status_history', verbose_name='Wniosek')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='application_status_changes', verbose_name='Zmienione przez')
    old_status = models.CharField(max_length=20, choices=AdoptionApplication.STATUS_CHOICES, verbose_name='Poprzedni status')
    new_status = models.CharField(max_length=20, choices=AdoptionApplication.STATUS_CHOICES, verbose_name='Nowy status')
    note = models.TextField(blank=True, verbose_name='Notatka')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at'], name='app_history_created_idx'),
            models.Index(fields=['new_status'], name='app_history_status_idx'),
        ]

    def __str__(self):
        return f'{self.application_id}: {self.old_status} -> {self.new_status}'


class ContactMessage(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Oczekuje'),
        ('resolved', 'Rozwiązane'),
    ]

    name = models.CharField(max_length=150, verbose_name='Imię i nazwisko')
    email = models.EmailField(verbose_name='Adres e-mail')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='contact_messages', verbose_name='Użytkownik')
    subject = models.CharField(max_length=200, verbose_name='Temat')
    message = models.TextField(verbose_name='Treść wiadomości')
    reply = models.TextField(blank=True, verbose_name='Odpowiedź administratora')
    replied_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='contact_message_replies', verbose_name='Odpowiedział')
    replied_at = models.DateTimeField(blank=True, null=True, verbose_name='Data odpowiedzi')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False, verbose_name='Przeczytane')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Status')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_read'], name='contact_is_read_idx'),
            models.Index(fields=['status'], name='contact_status_idx'),
            models.Index(fields=['created_at'], name='contact_created_idx'),
        ]

    def __str__(self):
        return f'Wiadomość od {self.name} - {self.subject}'
