from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import AdoptionApplication, Animal, ApplicationStatusHistory, ContactMessage, Shelter, UserProfile


class CoreFlowTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        self.user = User.objects.create_user('user1', 'user1@example.com', 'pass12345')
        self.shelter = Shelter.objects.create(
            name='Schronisko Test',
            city='testowo',
            address='ul. Testowa 1',
        )
        self.animal = Animal.objects.create(
            name='Azor',
            species='pies',
            age=4,
            size='sredni',
            description='Pies testowy',
            shelter=self.shelter,
        )

    def test_public_pages_render(self):
        for path in ['/', '/zwierzeta/', '/adopcja/', '/kontakt/', '/logowanie/']:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)

    def test_animal_list_shows_only_available_animals(self):
        adopted = Animal.objects.create(
            name='Adoptowany',
            species='pies',
            age=5,
            size='sredni',
            status='adopted',
            description='Nie powinien być na liscie adopcyjnej',
            shelter=self.shelter,
        )
        response = self.client.get('/zwierzeta/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.animal.name)
        self.assertNotContains(response, adopted.name)

    def test_animal_detail_page_renders_by_id(self):
        response = self.client.get(f'/zwierzeta/{self.animal.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.animal.name)
        self.assertEqual(self.client.get('/zwierzeta/999999/').status_code, 404)

    def test_animal_detail_places_description_below_photo(self):
        self.animal.description = 'Bardzo długi opis zwierzęcia ' * 20
        self.animal.good_with_children = True
        self.animal.good_with_cats = True
        self.animal.good_with_dogs = True
        self.animal.save(update_fields=['description', 'good_with_children', 'good_with_cats', 'good_with_dogs'])

        response = self.client.get(f'/zwierzeta/{self.animal.id}/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertLess(content.index('details-description'), content.index('details-card'))
        self.assertContains(response, 'Opis zwierzęcia')
        self.assertContains(response, 'Czy jest przyjazny dla dzieci?')
        self.assertContains(response, 'Czy akceptuje koty?')
        self.assertContains(response, 'Czy akceptuje inne psy?')

    def test_animal_detail_keeps_email_in_single_line_row(self):
        self.shelter.email = 'lukasz.grabowski0005@gmail.com'
        self.shelter.save(update_fields=['email'])

        response = self.client.get(f'/zwierzeta/{self.animal.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="info-email-row"')
        self.assertContains(response, 'lukasz.grabowski0005@gmail.com')

    def test_animal_detail_css_breaks_long_description_words(self):
        response = self.client.get(f'/zwierzeta/{self.animal.id}/')
        self.assertEqual(response.status_code, 200)

        css = (Path(__file__).resolve().parents[1] / 'static' / 'css' / 'style.css').read_text()
        self.assertIn('grid-template-columns: minmax(0, 1.2fr) minmax(360px, 0.8fr);', css)
        self.assertIn('overflow-wrap: break-word;', css)
        self.assertIn('word-break: normal;', css)
        self.assertIn('.info-list .info-email-row span', css)
        self.assertIn('white-space: nowrap;', css)

    def test_registration_login_and_application_flow(self):
        response = self.client.post('/logowanie/', {
            'register': 'true',
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'pass12345',
            'password_repeat': 'pass12345',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

        response = self.client.post('/adopcja/', {
            'animal_id': self.animal.id,
            'full_name': 'Nowy User',
            'email': 'newuser@example.com',
            'phone': '123456789',
            'living_conditions': 'Mieszkanie',
            'experience': 'Doświadczenie',
            'truth': 'on',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(AdoptionApplication.objects.count(), 1)
        application = AdoptionApplication.objects.get()
        self.assertEqual(application.applicant_email, 'newuser@example.com')

    def test_registration_requires_email(self):
        response = self.client.post('/logowanie/', {
            'register': 'true',
            'username': 'bezemaila',
            'password': 'pass12345',
            'password_repeat': 'pass12345',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='bezemaila').exists())

    def test_registration_error_keeps_register_panel_active(self):
        response = self.client.post('/logowanie/', {
            'register': 'true',
            'username': 'user1',
            'email': 'new@example.com',
            'password': 'pass12345',
            'password_repeat': 'pass12345',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_panel'], 'register')

    def test_login_redirects_to_safe_next_url(self):
        response = self.client.post('/logowanie/?next=/profil/', {
            'username': 'user1',
            'password': 'pass12345',
            'next': '/profil/',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/profil/')

    def test_duplicate_application_is_blocked(self):
        self.client.force_login(self.user)
        payload = {
            'animal_id': self.animal.id,
            'full_name': 'User Test',
            'email': 'user1@example.com',
            'phone': '123456789',
            'living_conditions': 'Mieszkanie',
            'experience': 'Doświadczenie',
            'truth': 'on',
        }
        self.assertEqual(self.client.post('/adopcja/', payload).status_code, 302)
        self.assertEqual(self.client.post('/adopcja/', payload).status_code, 200)
        self.assertEqual(AdoptionApplication.objects.count(), 1)

    def test_application_for_unavailable_animal_is_blocked(self):
        self.client.force_login(self.user)
        self.animal.status = 'adopted'
        self.animal.save(update_fields=['status'])
        response = self.client.post('/adopcja/', {
            'animal_id': self.animal.id,
            'full_name': 'User Test',
            'email': 'user1@example.com',
            'phone': '123456789',
            'living_conditions': 'Mieszkanie',
            'experience': 'Doświadczenie',
            'truth': 'on',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AdoptionApplication.objects.count(), 0)

    def test_adoption_ignores_posted_email(self):
        self.client.force_login(self.user)
        response = self.client.post('/adopcja/', {
            'animal_id': self.animal.id,
            'full_name': 'User Test',
            'email': 'podszywka@example.com',
            'phone': '123456789',
            'living_conditions': 'Mieszkanie',
            'experience': 'Doświadczenie',
            'truth': 'on',
        })
        self.assertEqual(response.status_code, 302)
        application = AdoptionApplication.objects.get()
        self.assertEqual(application.applicant_email, self.user.email)

    def test_adoption_marks_animal_as_pending(self):
        self.client.force_login(self.user)
        response = self.client.post('/adopcja/', {
            'animal_id': self.animal.id,
            'full_name': 'User Test',
            'phone': '123456789',
            'living_conditions': 'Mieszkanie',
            'experience': 'Doświadczenie',
            'truth': 'on',
        })
        self.assertEqual(response.status_code, 302)
        self.animal.refresh_from_db()
        self.assertEqual(self.animal.status, 'pending')

    def test_contact_message_is_saved(self):
        response = self.client.post('/kontakt/', {
            'name': 'User Test',
            'email': 'user1@example.com',
            'subject': 'Pytanie',
            'message': 'Treść testowa',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_logged_user_contact_message_is_visible_in_my_messages(self):
        self.client.force_login(self.user)
        response = self.client.post('/kontakt/', {
            'name': 'User Test',
            'email': 'user1@example.com',
            'subject': 'Pytanie o adopcję',
            'message': 'Treść widoczna dla użytkownika',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/moje-wiadomosci/')
        msg = ContactMessage.objects.get()
        self.assertEqual(msg.sender, self.user)

        response = self.client.get('/moje-wiadomosci/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pytanie o adopcję')
        self.assertContains(response, 'Treść widoczna dla użytkownika')

    def test_admin_can_change_application_status(self):
        application = AdoptionApplication.objects.create(
            animal=self.animal,
            applicant=self.user,
            applicant_name='User Test',
            applicant_email='user1@example.com',
            phone_number='123456789',
            living_conditions='Mieszkanie',
            experience='Doświadczenie',
        )
        self.client.force_login(self.admin)
        response = self.client.post('/admin-app/wniosek/status/', {
            'application_id': application.id,
            'status': 'review',
        })
        self.assertEqual(response.status_code, 302)
        application.refresh_from_db()
        self.animal.refresh_from_db()
        self.assertEqual(application.status, 'review')
        self.assertEqual(self.animal.status, 'pending')
        self.assertTrue(ApplicationStatusHistory.objects.filter(application=application, new_status='review').exists())

    def test_same_approved_status_repairs_animal_status(self):
        application = AdoptionApplication.objects.create(
            animal=self.animal,
            applicant=self.user,
            applicant_name='User Test',
            applicant_email='user1@example.com',
            phone_number='123456789',
            status='approved',
        )
        self.animal.status = 'available'
        self.animal.save(update_fields=['status'])
        self.client.force_login(self.admin)
        response = self.client.post('/admin-app/wniosek/status/', {
            'application_id': application.id,
            'status': 'approved',
        })
        self.assertEqual(response.status_code, 302)
        self.animal.refresh_from_db()
        self.assertEqual(self.animal.status, 'adopted')

    def test_approved_application_adopts_animal_and_rejects_others(self):
        other_user = User.objects.create_user('user2', 'user2@example.com', 'pass12345')
        application = AdoptionApplication.objects.create(
            animal=self.animal,
            applicant=self.user,
            phone_number='123456789',
        )
        other_application = AdoptionApplication.objects.create(
            animal=self.animal,
            applicant=other_user,
            phone_number='987654321',
        )
        self.client.force_login(self.admin)
        response = self.client.post('/admin-app/wniosek/status/', {
            'application_id': application.id,
            'status': 'approved',
        })
        self.assertEqual(response.status_code, 302)
        application.refresh_from_db()
        other_application.refresh_from_db()
        self.animal.refresh_from_db()
        self.assertEqual(application.status, 'approved')
        self.assertEqual(other_application.status, 'rejected')
        self.assertEqual(self.animal.status, 'adopted')

    def test_approved_application_saves_contact_info_for_user(self):
        application = AdoptionApplication.objects.create(
            animal=self.animal,
            applicant=self.user,
            applicant_name='User Test',
            applicant_email='user1@example.com',
            phone_number='123456789',
        )
        self.client.force_login(self.admin)
        response = self.client.post('/admin-app/wniosek/status/', {
            'application_id': application.id,
            'status': 'approved',
            'contact_at': '2026-06-06T12:30',
            'contact_message': 'Zadzwonimy w sobote po poludniu.',
        })
        self.assertEqual(response.status_code, 302)
        application.refresh_from_db()
        self.assertEqual(application.status, 'approved')
        self.assertEqual(application.contact_message, 'Zadzwonimy w sobote po poludniu.')
        self.assertEqual(timezone.localtime(application.contact_at).strftime('%Y-%m-%d %H:%M'), '2026-06-06 12:30')

        self.client.force_login(self.user)
        response = self.client.get('/moje-wnioski/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Adopcja zatwierdzona.')
        self.assertContains(response, 'Zadzwonimy w sobote po poludniu.')
        self.assertContains(response, 'Planowany kontakt:')
        self.assertContains(response, '06.06.2026 12:30')

    def test_admin_actions_require_post(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/admin-app/zwierze/usun/').status_code, 405)
        self.assertEqual(self.client.get('/admin-app/wniosek/status/').status_code, 405)

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/wyloguj/').status_code, 405)

    def test_animal_with_application_cannot_be_deleted(self):
        AdoptionApplication.objects.create(
            animal=self.animal,
            applicant=self.user,
            phone_number='123456789',
        )
        self.client.force_login(self.admin)
        response = self.client.post('/admin-app/zwierze/usun/', {'animal_id': self.animal.id})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Animal.objects.filter(id=self.animal.id).exists())

    def test_my_applications_requires_login(self):
        self.assertEqual(self.client.get('/moje-wnioski/').status_code, 302)

    def test_my_applications_lists_own(self):
        AdoptionApplication.objects.create(
            animal=self.animal,
            applicant=self.user,
            applicant_name='User Test',
            phone_number='123456789',
        )
        self.client.force_login(self.user)
        response = self.client.get('/moje-wnioski/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.animal.name)

    def test_admin_can_edit_animal(self):
        self.client.force_login(self.admin)
        response = self.client.post(f'/admin-app/zwierze/{self.animal.id}/edytuj/', {
            'name': 'Azor',
            'species': 'pies',
            'age': 6,
            'size': 'sredni',
            'status': 'adopted',
            'shelter': self.shelter.id,
            'description': 'Zmieniony opis',
        })
        self.assertEqual(response.status_code, 302)
        self.animal.refresh_from_db()
        self.assertEqual(self.animal.age, 6)
        self.assertEqual(self.animal.status, 'adopted')

    def test_admin_can_add_animal(self):
        self.client.force_login(self.admin)
        response = self.client.post('/admin-app/ogloszenia/dodaj/', {
            'name': 'Mila',
            'species': 'kot',
            'age': 2,
            'size': 'maly',
            'status': 'available',
            'shelter': self.shelter.id,
            'description': 'Spokojny kot do adopcji',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Animal.objects.filter(name='Mila', status='available').exists())

    def test_admin_can_create_shelter(self):
        self.client.force_login(self.admin)
        response = self.client.post('/admin-app/schroniska/dodaj/', {
            'name': 'Nowe Schronisko',
            'city': 'Kraków',
            'address': 'ul. Testowa 2',
            'phone': '123456789',
            'email': 'kontakt@example.com',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Shelter.objects.filter(name='Nowe Schronisko', city='kraków').exists())

    def test_admin_shelters_show_registered_animals(self):
        self.client.force_login(self.admin)
        response = self.client.get('/admin-app/schroniska/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<dialog class="modal"')
        self.assertContains(response, 'shelter-modal-')
        self.assertContains(response, 'Pokaż ogłoszenia')
        self.assertContains(response, self.animal.name)

    def test_shelter_requires_valid_phone(self):
        self.client.force_login(self.admin)
        response = self.client.post('/admin-app/schroniska/dodaj/', {
            'name': 'Błędny Telefon',
            'city': 'Kraków',
            'address': 'ul. Testowa 3',
            'phone': '123',
            'email': 'kontakt@example.com',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Shelter.objects.filter(name='Błędny Telefon').exists())

    def test_regular_user_cannot_access_admin_panel(self):
        self.client.force_login(self.user)
        response = self.client.get('/admin-app/')
        self.assertEqual(response.status_code, 302)

    def test_admin_can_mark_message_resolved(self):
        msg = ContactMessage.objects.create(
            name='Jan',
            email='jan@example.com',
            subject='Pytanie',
            message='Treść wiadomości',
        )
        self.client.force_login(self.admin)
        response = self.client.post('/admin-app/wiadomosc/status/', {
            'message_id': msg.id,
            'status': 'resolved',
        })
        self.assertEqual(response.status_code, 302)
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)
        self.assertEqual(msg.status, 'resolved')

    def test_admin_messages_show_modal_and_allow_reply(self):
        msg = ContactMessage.objects.create(
            sender=self.user,
            name='Jan',
            email='user1@example.com',
            subject='Pytanie o kota',
            message='Pełna treść wiadomości od użytkownika',
        )
        self.client.force_login(self.admin)
        response = self.client.get('/admin-app/wiadomosci/?status=all')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'message-modal-')
        self.assertContains(response, 'Pełna treść wiadomości od użytkownika')
        self.assertContains(response, 'Odpowiedź dla użytkownika')

        response = self.client.post('/admin-app/wiadomosc/status/', {
            'message_id': msg.id,
            'status': 'resolved',
            'reply': 'Prosze o kontakt telefoniczny jutro.',
        })
        self.assertEqual(response.status_code, 302)
        msg.refresh_from_db()
        self.assertEqual(msg.status, 'resolved')
        self.assertEqual(msg.reply, 'Prosze o kontakt telefoniczny jutro.')
        self.assertEqual(msg.replied_by, self.admin)
        self.assertIsNotNone(msg.replied_at)

        self.client.force_login(self.user)
        response = self.client.get('/moje-wiadomosci/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pytanie o kota')
        self.assertContains(response, 'Prosze o kontakt telefoniczny jutro.')

    def test_my_messages_requires_login(self):
        self.assertEqual(self.client.get('/moje-wiadomosci/').status_code, 302)

    def test_admin_navigation_hides_public_contact_link(self):
        self.client.force_login(self.admin)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'href="/kontakt/"')

    def test_regular_user_navigation_shows_my_messages_and_contact(self):
        self.client.force_login(self.user)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/moje-wiadomosci/"')
        self.assertContains(response, 'href="/kontakt/"')

    def test_applications_csv_export_is_removed(self):
        AdoptionApplication.objects.create(
            animal=self.animal,
            applicant=self.user,
            applicant_name='User Test',
            applicant_email='user1@example.com',
            phone_number='123456789',
        )
        self.client.force_login(self.admin)
        response = self.client.get('/admin-app/wnioski/eksport.csv')
        self.assertEqual(response.status_code, 404)

    def test_profile_page_renders(self):
        self.client.force_login(self.user)
        response = self.client.get('/profil/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Konto')

    def test_user_can_update_profile_details(self):
        self.client.force_login(self.user)
        response = self.client.post('/profil/', {
            'update_details': '1',
            'full_name': 'Jan Kowalski',
            'phone_number': '123456789',
        })
        self.assertEqual(response.status_code, 302)
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.full_name, 'Jan Kowalski')
        self.assertEqual(profile.phone_number, '123456789')

    def test_adoption_form_prefills_profile_details(self):
        UserProfile.objects.update_or_create(
            user=self.user,
            defaults={'full_name': 'Jan Kowalski', 'phone_number': '123456789'},
        )
        self.client.force_login(self.user)
        response = self.client.get('/adopcja/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Jan Kowalski"')
        self.assertContains(response, 'value="123456789"')
        self.assertContains(response, 'value="user1@example.com"')

    def test_contact_form_prefills_profile_and_email(self):
        UserProfile.objects.update_or_create(
            user=self.user,
            defaults={'full_name': 'Jan Kowalski', 'phone_number': '123456789'},
        )
        self.client.force_login(self.user)
        response = self.client.get('/kontakt/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Jan Kowalski"')
        self.assertContains(response, 'value="user1@example.com"')

    def test_admin_applications_show_details_modal(self):
        AdoptionApplication.objects.create(
            animal=self.animal,
            applicant=self.user,
            applicant_name='User Test',
            applicant_email='user1@example.com',
            phone_number='123456789',
            living_conditions='Dom z ogrodem',
            experience='Opieka nad psem',
        )
        self.client.force_login(self.admin)
        response = self.client.get('/admin-app/wnioski/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<dialog class="modal"')
        self.assertContains(response, 'data-modal-open="application-modal-')
        self.assertContains(response, 'Warunki mieszkaniowe')
        self.assertContains(response, 'Dom z ogrodem')
        self.assertContains(response, 'Doświadczenie ze zwierzętami')
        self.assertContains(response, 'Planowany telefon')
        self.assertNotContains(response, '<details')

    def test_admin_users_show_application_details_modal(self):
        AdoptionApplication.objects.create(
            animal=self.animal,
            applicant=self.user,
            applicant_name='User Test',
            applicant_email='user1@example.com',
            phone_number='123456789',
            living_conditions='Dom z ogrodem',
            experience='Opieka nad psem',
            status='approved',
            contact_message='Telefon w poniedzialek.',
        )
        self.client.force_login(self.admin)
        response = self.client.get('/admin-app/uzytkownicy/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<dialog class="modal"')
        self.assertContains(response, 'data-modal-open="user-modal-')
        self.assertContains(response, 'Adoptowane zwierzę:')
        self.assertContains(response, 'Dom z ogrodem')
        self.assertContains(response, 'Opieka nad psem')
        self.assertContains(response, 'Telefon w poniedzialek.')

    def test_admin_animals_filter_uses_clear_statuses(self):
        self.client.force_login(self.admin)
        response = self.client.get('/admin-app/ogloszenia/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dostępne oznacza')
        self.assertContains(response, 'W trakcie adopcji oznacza')
        self.assertContains(response, 'Adoptowane oznacza')
        self.assertNotContains(response, 'Stare/adoptowane')
        self.assertNotContains(response, 'Aktywne to')

    def test_user_can_update_email(self):
        self.client.force_login(self.user)
        response = self.client.post('/profil/', {
            'update_email': '1',
            'new_email': 'nowy@example.com',
            'new_email_repeat': 'nowy@example.com',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'nowy@example.com')

    def test_email_update_uses_generic_placeholders(self):
        self.client.force_login(self.user)
        response = self.client.get('/profil/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'placeholder="nazwa@example.com"', count=2)
        self.assertNotContains(response, 'placeholder="user1@example.com"')
        self.assertNotContains(response, 'placeholder="Powtórz nowy adres e-mail"')

    def test_email_update_requires_repeated_email(self):
        self.client.force_login(self.user)
        response = self.client.post('/profil/', {
            'update_email': '1',
            'new_email': 'nowy@example.com',
            'new_email_repeat': 'inny@example.com',
        })
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'user1@example.com')

    def test_email_update_rejects_duplicate_email(self):
        User.objects.create_user('user2', 'zajety@example.com', 'pass12345')
        self.client.force_login(self.user)
        response = self.client.post('/profil/', {
            'update_email': '1',
            'new_email': 'zajety@example.com',
            'new_email_repeat': 'zajety@example.com',
        })
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'user1@example.com')

    def test_user_can_change_password(self):
        self.client.force_login(self.user)
        response = self.client.post('/profil/', {
            'change_password': '1',
            'old_password': 'pass12345',
            'new_password1': 'nowehasło987',
            'new_password2': 'nowehasło987',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('nowehasło987'))

    def test_user_can_cancel_own_application(self):
        application = AdoptionApplication.objects.create(
            animal=self.animal,
            applicant=self.user,
            phone_number='123456789',
        )
        self.client.force_login(self.user)
        response = self.client.post(f'/moje-wnioski/{application.id}/wycofaj/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(AdoptionApplication.objects.filter(id=application.id).exists())

    def test_cancel_last_active_application_restores_animal_availability(self):
        self.animal.status = 'pending'
        self.animal.save(update_fields=['status'])
        application = AdoptionApplication.objects.create(
            animal=self.animal,
            applicant=self.user,
            phone_number='123456789',
        )
        self.client.force_login(self.user)
        response = self.client.post(f'/moje-wnioski/{application.id}/wycofaj/')
        self.assertEqual(response.status_code, 302)
        self.animal.refresh_from_db()
        self.assertEqual(self.animal.status, 'available')

    def test_cannot_cancel_approved_application(self):
        application = AdoptionApplication.objects.create(
            animal=self.animal,
            applicant=self.user,
            phone_number='123456789',
            status='approved',
        )
        self.client.force_login(self.user)
        self.client.post(f'/moje-wnioski/{application.id}/wycofaj/')
        self.assertTrue(AdoptionApplication.objects.filter(id=application.id).exists())
