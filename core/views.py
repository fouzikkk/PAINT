from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Prefetch, ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import (
    AdoptionApplicationForm,
    AnimalForm,
    ContactMessageForm,
    EmailUpdateForm,
    ProfileDetailsForm,
    RegistrationForm,
    ShelterForm,
)
from .models import (
    AdoptionApplication,
    Animal,
    ApplicationStatusHistory,
    ContactMessage,
    Shelter,
    UserProfile,
)


def home(request):
    featured_animals = Animal.objects.filter(status='available').select_related('shelter')[:3]
    return render(request, 'index.html', {
        'featured_animals': featured_animals,
        'applications_count': AdoptionApplication.objects.count(),
        'adopted_count': Animal.objects.filter(status='adopted').count(),
        'cities_count': Shelter.objects.values('city').distinct().count(),
        'available_count': Animal.objects.filter(status='available').count(),
    })


def animal_list(request):
    animals = Animal.objects.select_related('shelter').filter(status='available')
    search = request.GET.get('search')
    species = request.GET.get('species')
    age = request.GET.get('age')
    shelter = request.GET.get('shelter')

    if search:
        animals = animals.filter(
            Q(name__icontains=search)
            | Q(breed__icontains=search)
            | Q(description__icontains=search)
        )
    if species and species != 'all':
        animals = animals.filter(species=species)
    if shelter and shelter != 'all':
        animals = animals.filter(shelter__city=shelter)
    if age == 'young':
        animals = animals.filter(age__lte=3)
    elif age == 'adult':
        animals = animals.filter(age__gte=4, age__lte=8)
    elif age == 'senior':
        animals = animals.filter(age__gte=9)

    count = animals.count()
    paginator = Paginator(animals, 9)
    page_obj = paginator.get_page(request.GET.get('page'))
    query_params = request.GET.copy()
    query_params.pop('page', None)

    shelters = Shelter.objects.values_list('city', flat=True).distinct().order_by('city')
    return render(request, 'animals/zwierzeta.html', {
        'animals': page_obj.object_list,
        'page_obj': page_obj,
        'querystring': query_params.urlencode(),
        'shelters': shelters,
        'count': count,
    })


def animal_details(request, animal_id):
    animal = get_object_or_404(Animal.objects.select_related('shelter'), id=animal_id)
    return render(request, 'animals/szczegoly.html', {'animal': animal})


def login_register_view(request):
    active_panel = 'login'
    next_url = _get_safe_next_url(request)
    login_username = ''
    registration_data = {}

    if request.method == 'POST':
        if 'register' in request.POST:
            active_panel = 'register'
            registration_data = request.POST
            form = RegistrationForm(request.POST)
            if form.is_valid():
                user = form.save()
                login(request, user)
                return redirect(next_url or 'home')
            _add_form_errors(request, form)
        else:
            login_username = request.POST.get('username', '')
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                login(request, form.get_user())
                return redirect(next_url or 'home')
            messages.error(request, 'Błędny login lub hasło.')

    return render(request, 'users/logowanie.html', {
        'active_panel': active_panel,
        'login_username': login_username,
        'registration_data': registration_data,
        'next_url': next_url,
    })


@require_POST
def logout_view(request):
    logout(request)
    return redirect('home')


def adoption_form_view(request):
    animal_id = request.GET.get('animal')
    selected_animal = (
        Animal.objects.select_related('shelter').filter(id=animal_id, status='available').first()
        if animal_id else None
    )
    profile = _get_user_profile(request.user) if request.user.is_authenticated else None
    if request.method == 'POST':
        form_data = request.POST
    else:
        form_data = {
            'full_name': profile.full_name if profile else '',
            'phone': profile.phone_number if profile else '',
        }
    if animal_id and not selected_animal and request.method == 'GET':
        messages.error(request, 'Wybrane zwierzę nie jest dostępne do adopcji.')

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Zaloguj się, aby wysłać wniosek.')
            return redirect('login')

        form = AdoptionApplicationForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                form.save(request.user)
                messages.success(request, 'Wniosek został wysłany.')
                return redirect('my_applications')
            except ValidationError as exc:
                for error in exc.messages:
                    messages.error(request, error)

        _add_form_errors(request, form)
        selected_animal = form.cleaned_data.get('animal_id') if 'animal_id' in form.cleaned_data else selected_animal

    return render(request, 'adoptions/adopcja.html', {
        'animal': selected_animal,
        'available_animals': Animal.objects.filter(status='available').order_by('name'),
        'form_data': form_data,
        'profile': profile,
        'selected_animal_id': form_data.get('animal_id') or (selected_animal.id if selected_animal else ''),
    })


def contact_view(request):
    animal_id = request.GET.get('animal')
    animal = Animal.objects.filter(id=animal_id).first() if animal_id else None
    subject = f'Zapytanie o zwierzę: {animal.name}' if animal else ''
    profile = _get_user_profile(request.user) if request.user.is_authenticated else None
    form_data = {
        'name': profile.full_name if profile else '',
        'email': request.user.email if request.user.is_authenticated else '',
        'subject': subject,
        'message': '',
    }

    if request.method == 'POST':
        form_data = request.POST
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            contact_message = form.save(commit=False)
            if request.user.is_authenticated:
                contact_message.sender = request.user
            contact_message.save()
            messages.success(request, 'Wiadomość została wysłana.')
            if request.user.is_authenticated and not request.user.is_staff:
                return redirect('my_messages')
            return redirect('contact_form')
        _add_form_errors(request, form)

    return render(request, 'contact/kontakt.html', {
        'subject': subject,
        'form_data': form_data,
        'profile': profile,
    })


admin_required = user_passes_test(lambda u: u.is_staff)


@admin_required
def admin_panel_view(request):
    return render(request, 'users/admin_dashboard.html', {
        'available_count': Animal.objects.filter(status='available').count(),
        'pending_count': Animal.objects.filter(status='pending').count(),
        'adopted_count': Animal.objects.filter(status='adopted').count(),
        'applications_count': AdoptionApplication.objects.count(),
        'messages_pending_count': ContactMessage.objects.filter(status='pending').count(),
        'shelters_count': Shelter.objects.count(),
        'users_count': User.objects.count(),
    })


@admin_required
def admin_animal_add(request):
    if request.method == 'POST':
        form = AnimalForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dodano ogłoszenie.')
            return redirect('admin_animals')
        _add_form_errors(request, form)
    else:
        form = AnimalForm(user=request.user)

    return render(request, 'users/admin_animal_form.html', {
        'form': form,
        'title': 'Dodaj ogłoszenie',
        'submit_label': 'Zapisz ogłoszenie',
    })


@admin_required
def admin_animals_view(request):
    status_filter = request.GET.get('status', 'all')
    animals = (
        Animal.objects
        .select_related('shelter')
        .prefetch_related(Prefetch(
            'applications',
            queryset=AdoptionApplication.objects.filter(status='approved').select_related('applicant'),
            to_attr='approved_applications',
        ))
        .order_by('-updated_at', 'name')
    )

    if status_filter in dict(Animal.STATUS_CHOICES):
        animals = animals.filter(status=status_filter)
    else:
        status_filter = 'all'

    paginator = Paginator(animals, 40)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'users/admin_animals.html', {
        'animals': page_obj.object_list,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_choices': Animal.STATUS_CHOICES,
    })


@admin_required
@require_POST
def admin_animal_delete(request):
    animal = get_object_or_404(Animal, id=request.POST.get('animal_id'))
    try:
        animal.delete()
        messages.success(request, 'Ogłoszenie zostało usunięte.')
    except ProtectedError:
        messages.error(request, 'Nie można usunąć zwierzęcia, które ma powiązane wnioski adopcyjne.')
    return redirect('admin_animals')


@admin_required
@require_POST
def admin_application_update(request):
    application = get_object_or_404(AdoptionApplication.objects.select_related('animal'), id=request.POST.get('application_id'))
    new_status = request.POST.get('status')
    if new_status in dict(AdoptionApplication.STATUS_CHOICES):
        contact_at = _parse_contact_at(request.POST.get('contact_at', ''))
        contact_message = request.POST.get('contact_message', '').strip()
        error = _update_application_status(
            application,
            new_status,
            request.user,
            contact_at=contact_at,
            contact_message=contact_message,
        )
        if error:
            messages.error(request, error)
        else:
            messages.success(request, 'Status wniosku został zaktualizowany.')
    else:
        messages.error(request, 'Nieprawidłowy status wniosku.')
    return redirect('admin_applications')


@admin_required
def admin_animal_edit(request, animal_id):
    animal = get_object_or_404(Animal.objects.select_related('shelter'), id=animal_id)
    if request.method == 'POST':
        form = AnimalForm(request.POST, request.FILES, instance=animal, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ogłoszenie zostało zaktualizowane.')
            return redirect('admin_animals')
        _add_form_errors(request, form)
    else:
        form = AnimalForm(instance=animal, user=request.user)

    return render(request, 'users/admin_animal_form.html', {
        'form': form,
        'animal': animal,
        'title': f'Edytuj ogłoszenie: {animal.name}',
        'submit_label': 'Zapisz zmiany',
    })


@admin_required
@require_POST
def admin_message_update(request):
    message = get_object_or_404(ContactMessage, id=request.POST.get('message_id'))
    new_status = request.POST.get('status')
    if new_status in dict(ContactMessage.STATUS_CHOICES):
        message.status = new_status
        message.is_read = new_status == 'resolved'
        reply = request.POST.get('reply')
        update_fields = ['status', 'is_read']
        if reply is not None:
            message.reply = reply.strip()
            if message.reply:
                message.replied_by = request.user
                message.replied_at = timezone.now()
                update_fields.extend(['reply', 'replied_by', 'replied_at'])
            else:
                message.replied_by = None
                message.replied_at = None
                update_fields.extend(['reply', 'replied_by', 'replied_at'])
        message.save(update_fields=update_fields)
        messages.success(request, 'Status wiadomości został zaktualizowany.')
    else:
        messages.error(request, 'Nieprawidłowy status wiadomości.')
    return redirect('admin_messages')


@admin_required
def admin_applications_view(request):
    applications = (
        AdoptionApplication.objects
        .select_related('animal', 'animal__shelter', 'applicant')
        .order_by('-created_at')
    )
    status_filter = request.GET.get('status', 'all')
    if status_filter in dict(AdoptionApplication.STATUS_CHOICES):
        applications = applications.filter(status=status_filter)
    else:
        status_filter = 'all'

    paginator = Paginator(applications, 40)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'users/admin_applications.html', {
        'applications': page_obj.object_list,
        'application_statuses': AdoptionApplication.STATUS_CHOICES,
        'page_obj': page_obj,
        'status_filter': status_filter,
    })


@admin_required
def admin_shelters_view(request):
    shelters = (
        Shelter.objects
        .annotate(animals_count=Count('animals'))
        .prefetch_related(Prefetch(
            'animals',
            queryset=Animal.objects.select_related('shelter').order_by('name'),
        ))
        .order_by('city', 'name')
    )
    return render(request, 'users/admin_shelters.html', {
        'shelters': shelters,
    })


@admin_required
def admin_shelter_create(request):
    if request.method == 'POST':
        form = ShelterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Schronisko zostało zarejestrowane.')
            return redirect('admin_shelters')
        _add_form_errors(request, form)
    else:
        form = ShelterForm()

    return render(request, 'users/admin_shelter_form.html', {'form': form})


@admin_required
def admin_users_view(request):
    existing_profile_user_ids = UserProfile.objects.values_list('user_id', flat=True)
    missing_profiles = [
        UserProfile(user=user)
        for user in User.objects.exclude(id__in=existing_profile_user_ids)
    ]
    if missing_profiles:
        UserProfile.objects.bulk_create(missing_profiles)

    users = (
        User.objects
        .select_related('profile')
        .prefetch_related(Prefetch(
            'applications',
            queryset=AdoptionApplication.objects.select_related('animal', 'animal__shelter').order_by('-created_at'),
        ))
        .order_by('username')
    )
    paginator = Paginator(users, 40)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'users/admin_users.html', {
        'registered_users': page_obj.object_list,
        'page_obj': page_obj,
    })


@admin_required
def admin_messages_view(request):
    status_filter = request.GET.get('status', 'pending')
    messages_queryset = ContactMessage.objects.select_related('sender', 'replied_by')
    if status_filter in dict(ContactMessage.STATUS_CHOICES):
        messages_queryset = messages_queryset.filter(status=status_filter)
    else:
        status_filter = 'all'

    paginator = Paginator(messages_queryset, 40)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'users/admin_messages.html', {
        'contact_messages': page_obj.object_list,
        'message_statuses': ContactMessage.STATUS_CHOICES,
        'page_obj': page_obj,
        'status_filter': status_filter,
    })


@login_required
def my_applications(request):
    applications = (
        AdoptionApplication.objects
        .filter(applicant=request.user)
        .select_related('animal', 'animal__shelter')
    )
    return render(request, 'adoptions/moje_wnioski.html', {'applications': applications})


@login_required
def my_messages(request):
    query = Q(sender=request.user)
    if request.user.email:
        query |= Q(email__iexact=request.user.email)

    contact_messages = ContactMessage.objects.filter(query).select_related('replied_by').order_by('-created_at')
    paginator = Paginator(contact_messages, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'contact/moje_wiadomosci.html', {
        'contact_messages': page_obj.object_list,
        'page_obj': page_obj,
    })


@login_required
@require_POST
def cancel_application(request, application_id):
    with transaction.atomic():
        application = get_object_or_404(
            AdoptionApplication.objects.select_for_update(),
            id=application_id,
            applicant=request.user,
        )
        if application.status == 'approved':
            messages.error(request, 'Nie można wycofać zatwierdzonego wniosku.')
        else:
            animal_id = application.animal_id
            application.delete()
            _refresh_animal_status(animal_id)
            messages.success(request, 'Wniosek został wycofany.')
    return redirect('my_applications')


@login_required
def profile(request):
    user_profile = _get_user_profile(request.user)
    details_form = ProfileDetailsForm(instance=user_profile)
    email_form = EmailUpdateForm(user=request.user)
    password_form = PasswordChangeForm(request.user)

    if request.method == 'POST':
        if 'update_details' in request.POST:
            details_form = ProfileDetailsForm(request.POST, instance=user_profile)
            if details_form.is_valid():
                details_form.save(request.user)
                messages.success(request, 'Dane konta zostały zaktualizowane.')
                return redirect('profile')
            _add_form_errors(request, details_form)
        elif 'update_email' in request.POST:
            email_form = EmailUpdateForm(request.POST, user=request.user)
            if email_form.is_valid():
                email_form.save(request.user)
                messages.success(request, 'Adres e-mail został zaktualizowany.')
                return redirect('profile')
            _add_form_errors(request, email_form)
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Hasło zostało zmienione.')
                return redirect('profile')
            _add_form_errors(request, password_form)

    return render(request, 'users/profil.html', {
        'details_form': details_form,
        'email_form': email_form,
        'password_form': password_form,
        'user_profile': user_profile,
    })


def _add_form_errors(request, form):
    for errors in form.errors.values():
        for error in errors:
            messages.error(request, error)


def _get_user_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _get_safe_next_url(request):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return ''


def _parse_contact_at(raw_value):
    raw_value = (raw_value or '').strip()
    if not raw_value:
        return None

    parsed = parse_datetime(raw_value)
    if parsed is None:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _refresh_animal_status(animal_id):
    animal = Animal.objects.select_for_update().get(id=animal_id)
    has_approved_application = AdoptionApplication.objects.filter(
        animal=animal,
        status='approved',
    ).exists()
    has_active_applications = AdoptionApplication.objects.filter(
        animal=animal,
        status__in=['new', 'review'],
    ).exists()

    if has_approved_application:
        new_status = 'adopted'
    elif has_active_applications:
        new_status = 'pending'
    else:
        new_status = 'available'

    if animal.status != new_status:
        animal.status = new_status
        animal.save(update_fields=['status', 'updated_at'])


def _update_application_status(application, new_status, user, contact_at=None, contact_message=''):
    with transaction.atomic():
        application = (
            AdoptionApplication.objects
            .select_for_update()
            .select_related('animal')
            .get(id=application.id)
        )
        animal = Animal.objects.select_for_update().get(id=application.animal_id)
        old_status = application.status

        if old_status == new_status:
            if new_status == 'approved':
                _apply_approval_contact(application, contact_at, contact_message)
                application.save(update_fields=['contact_at', 'contact_message'])
            _refresh_animal_status(animal.id)
            return None

        approved_exists = (
            AdoptionApplication.objects
            .filter(animal=animal, status='approved')
            .exclude(id=application.id)
            .exists()
        )
        if new_status == 'approved' and approved_exists:
            return 'To zwierzę ma już zatwierdzony wniosek adopcyjny.'

        application.status = new_status
        update_fields = ['status']
        if new_status == 'approved':
            _apply_approval_contact(application, contact_at, contact_message)
            update_fields.extend(['contact_at', 'contact_message'])
        application.save(update_fields=update_fields)

        ApplicationStatusHistory.objects.create(
            application=application,
            changed_by=user,
            old_status=old_status,
            new_status=new_status,
        )

        if new_status == 'approved':
            animal.status = 'adopted'
            animal.save(update_fields=['status', 'updated_at'])
            AdoptionApplication.objects.filter(animal=animal).exclude(id=application.id).exclude(status='rejected').update(status='rejected')
        else:
            _refresh_animal_status(animal.id)

    return None


def _apply_approval_contact(application, contact_at=None, contact_message=''):
    application.contact_at = contact_at
    application.contact_message = (
        contact_message
        or 'Adopcja została zatwierdzona. Schronisko skontaktuje się z Tobą telefonicznie w sprawie dalszych kroków.'
    )
