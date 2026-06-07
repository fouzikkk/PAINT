from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import IntegrityError, transaction

from .models import AdoptionApplication, Animal, ContactMessage, Shelter, UserProfile


phone_validator = RegexValidator(
    regex=r'^\d{9}$',
    message='Numer telefonu musi składać się dokładnie z 9 cyfr.',
)


class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=150, label='Nazwa użytkownika')
    email = forms.EmailField(required=True, label='Adres e-mail', widget=forms.EmailInput(attrs={'placeholder': 'nazwa@example.com'}))
    password = forms.CharField(widget=forms.PasswordInput, label='Hasło')
    password_repeat = forms.CharField(widget=forms.PasswordInput, label='Powtórz hasło')

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('Nazwa użytkownika jest już zajęta.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Ten adres e-mail jest już przypisany do konta.')
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        password_repeat = cleaned.get('password_repeat')

        if password and password_repeat and password != password_repeat:
            self.add_error('password_repeat', 'Hasła muszą być takie same.')
        elif password:
            try:
                validate_password(password)
            except ValidationError as exc:
                self.add_error('password', exc)

        return cleaned

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data.get('email', ''),
            password=self.cleaned_data['password'],
        )
        UserProfile.objects.get_or_create(user=user)
        return user


class AnimalForm(forms.ModelForm):
    class Meta:
        model = Animal
        fields = [
            'name',
            'species',
            'age',
            'size',
            'gender',
            'breed',
            'weight_kg',
            'is_sterilized',
            'is_vaccinated',
            'is_chipped',
            'good_with_children',
            'good_with_cats',
            'good_with_dogs',
            'shelter',
            'status',
            'description',
            'image',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['gender'].required = False
        self.fields['shelter'].queryset = Shelter.objects.order_by('city', 'name')
        self.fields['shelter'].empty_label = 'Wybierz schronisko'

    def clean_gender(self):
        return self.cleaned_data.get('gender') or 'unknown'

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image:
            return image

        content_type = getattr(image, 'content_type', None)
        if content_type is not None:
            max_size = 5 * 1024 * 1024
            if image.size > max_size:
                raise ValidationError('Zdjęcie nie może być większe niż 5 MB.')

            allowed = ('image/jpeg', 'image/png', 'image/webp', 'image/gif')
            if content_type not in allowed:
                raise ValidationError('Dozwolone formaty zdjęcia: JPEG, PNG, WEBP, GIF.')

        return image

    def save(self, commit=True):
        animal = super().save(commit=commit)
        if commit:
            approved_exists = AdoptionApplication.objects.filter(animal=animal, status='approved').exists()
            active_exists = AdoptionApplication.objects.filter(animal=animal, status__in=['new', 'review']).exists()
            if approved_exists and animal.status != 'adopted':
                animal.status = 'adopted'
                animal.save(update_fields=['status', 'updated_at'])
            elif active_exists and animal.status == 'available':
                animal.status = 'pending'
                animal.save(update_fields=['status', 'updated_at'])
        return animal


class ShelterForm(forms.ModelForm):
    class Meta:
        model = Shelter
        fields = ['name', 'city', 'address', 'phone', 'email']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 4}),
            'phone': forms.TextInput(attrs={
                'inputmode': 'numeric',
                'maxlength': '9',
                'pattern': '[0-9]{9}',
                'placeholder': 'Numer telefonu',
            }),
        }

    def clean_city(self):
        return self.cleaned_data.get('city', '').strip().lower()

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone:
            phone_validator(phone)
        return phone


class AdoptionApplicationForm(forms.Form):
    full_name = forms.CharField(max_length=150, label='Imię i nazwisko')
    phone = forms.CharField(max_length=9, validators=[phone_validator], label='Numer telefonu')
    animal_id = forms.ModelChoiceField(
        queryset=Animal.objects.none(),
        label='Wybrane zwierzę',
        error_messages={
            'invalid_choice': 'Wybrane zwierzę nie jest już dostępne do adopcji.',
        },
    )
    living_conditions = forms.CharField(label='Warunki mieszkaniowe')
    experience = forms.CharField(widget=forms.Textarea, label='Doświadczenie')
    truth = forms.BooleanField(label='Oświadczam, że podane informacje są prawdziwe.')

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['animal_id'].queryset = Animal.objects.filter(status='available').select_related('shelter')

    def clean_animal_id(self):
        animal = self.cleaned_data['animal_id']
        if animal.status != 'available':
            raise ValidationError('To zwierzę nie jest już dostępne do adopcji.')
        return animal

    def save(self, user):
        animal = self.cleaned_data['animal_id']
        try:
            with transaction.atomic():
                animal = Animal.objects.select_for_update().get(id=animal.id)
                if animal.status != 'available':
                    raise ValidationError('To zwierzę nie jest już dostępne do adopcji.')

                application = AdoptionApplication.objects.create(
                    animal=animal,
                    applicant=user,
                    applicant_name=self.cleaned_data['full_name'],
                    applicant_email=user.email,
                    phone_number=self.cleaned_data['phone'],
                    living_conditions=self.cleaned_data['living_conditions'],
                    experience=self.cleaned_data['experience'],
                )
                animal.status = 'pending'
                animal.save(update_fields=['status', 'updated_at'])
                return application
        except IntegrityError as exc:
            raise ValidationError('Masz już złożony wniosek na to zwierzę.') from exc


class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'nazwa@example.com'}),
            'message': forms.Textarea(attrs={'rows': 6}),
        }


class EmailUpdateForm(forms.Form):
    new_email = forms.EmailField(required=True, label='Nowy adres e-mail')
    new_email_repeat = forms.EmailField(required=True, label='Potwierdź adres e-mail')

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['new_email'].widget.attrs['placeholder'] = 'nazwa@example.com'
        self.fields['new_email_repeat'].widget.attrs['placeholder'] = 'nazwa@example.com'

    def clean(self):
        cleaned = super().clean()
        new_email = cleaned.get('new_email')
        new_email_repeat = cleaned.get('new_email_repeat')
        if new_email and new_email_repeat and new_email != new_email_repeat:
            self.add_error('new_email_repeat', 'Adresy e-mail muszą być takie same.')
        if new_email:
            queryset = User.objects.filter(email__iexact=new_email)
            if self.user is not None:
                queryset = queryset.exclude(id=self.user.id)
            if queryset.exists():
                self.add_error('new_email', 'Ten adres e-mail jest już przypisany do innego konta.')
        return cleaned

    def save(self, user):
        user.email = self.cleaned_data['new_email']
        user.save(update_fields=['email'])
        return user


class ProfileDetailsForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['full_name', 'phone_number']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Imię i nazwisko'}),
            'phone_number': forms.TextInput(attrs={
                'inputmode': 'numeric',
                'maxlength': '9',
                'pattern': '[0-9]{9}',
                'placeholder': 'Numer telefonu',
            }),
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        if phone:
            phone_validator(phone)
        return phone

    def save(self, user, commit=True):
        profile = super().save(commit=False)
        profile.user = user
        if commit:
            profile.save()
            names = profile.full_name.split(' ', 1)
            user.first_name = names[0] if profile.full_name else ''
            user.last_name = names[1] if len(names) > 1 else ''
            user.save(update_fields=['first_name', 'last_name'])
        return profile
