import os
import shutil
import urllib.request

import django
from django.apps import apps

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'przyjazna_lapa.settings')
if not apps.ready:
    django.setup()

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.utils import timezone

from core.models import (
    AdoptionApplication,
    Animal,
    ContactMessage,
    Shelter,
    UserProfile,
)

# Zdjęcia z Unsplash (darmowa licencja).
# Każdy URL wskazuje na konkretne zdjęcie zmniejszone do 600px szerokości.
ANIMAL_PHOTOS = {
    'Burek': 'https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=600',
    'Luna': 'https://images.unsplash.com/photo-1526336024174-e58f5cdd8e13?w=600',
    'Rex': 'https://images.unsplash.com/photo-1589941013453-ec89f33b5e95?w=600',
    'Mruczka': 'https://images.unsplash.com/photo-1513245543132-31f507417b26?w=600',
    'Fafik': 'https://images.unsplash.com/photo-1598133894008-61f7fdb8cc3a?w=600',
    'Puszek': 'https://images.unsplash.com/photo-1615497001839-b0a0eac3274c?w=600',
    'Bella': 'https://images.unsplash.com/photo-1579110727408-3e1550e795c0?w=600',
    'Filemon': 'https://images.unsplash.com/photo-1573865526739-10659fec78a5?w=600',
}


def _download_photo(name):
    """Pobiera zdjęcie z Unsplash i zwraca ścieżkę do pliku tymczasowego."""
    url = ANIMAL_PHOTOS.get(name)
    if not url:
        return None

    tmp_dir = os.path.join(settings.BASE_DIR, 'media', 'animals')
    os.makedirs(tmp_dir, exist_ok=True)
    filename = f'{name.lower()}.jpg'
    filepath = os.path.join(tmp_dir, filename)

    if os.path.exists(filepath):
        return filepath

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            with open(filepath, 'wb') as f:
                shutil.copyfileobj(response, f)
        print(f'  Pobrano zdjęcie: {name} -> {filename}')
        return filepath
    except Exception as e:
        print(f'  Nie udało się pobrać zdjęcia dla {name}: {e}')
        return None


def _assign_photo(animal):
    """Przypisuje pobrane zdjęcie do zwierzęcia (jeśli jeszcze nie ma)."""
    if animal.image:
        return

    filepath = _download_photo(animal.name)
    if not filepath:
        return

    relative = f'animals/{animal.name.lower()}.jpg'
    animal.image = relative
    animal.save(update_fields=['image'])


def seed():
    # ------------------------------------------------------------------ admin
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print('Utwórzono administratora: admin / admin123')

    admin_user = User.objects.get(username='admin')

    # --------------------------------------------------- zwykli użytkownicy
    users = {}
    users_data = [
        {
            'username': 'jan_kowalski',
            'email': 'jan.kowalski@example.com',
            'password': 'user1234',
            'full_name': 'Jan Kowalski',
            'phone_number': '501234567',
        },
        {
            'username': 'anna_nowak',
            'email': 'anna.nowak@example.com',
            'password': 'user1234',
            'full_name': 'Anna Nowak',
            'phone_number': '602345678',
        },
        {
            'username': 'tomek_zielinski',
            'email': 'tomek.z@example.com',
            'password': 'user1234',
            'full_name': 'Tomasz Zieliński',
            'phone_number': '703456789',
        },
    ]

    for data in users_data:
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={'email': data['email']},
        )
        if created:
            user.set_password(data['password'])
            user.save()
            print(f'Utwórzono użytkownika: {data["username"]} / {data["password"]}')

        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'full_name': data['full_name'],
                'phone_number': data['phone_number'],
            },
        )
        users[data['username']] = user

    # ------------------------------------------------------------ schroniska
    shelter_krakow, _ = Shelter.objects.get_or_create(
        name='Schronisko Kraków',
        city='kraków',
        defaults={
            'address': 'ul. Psia 1, 30-001 Kraków',
            'phone': '123456789',
            'email': 'kontakt@schronisko-krakow.pl',
        },
    )
    shelter_warszawa, _ = Shelter.objects.get_or_create(
        name='Schronisko Warszawa',
        city='warszawa',
        defaults={
            'address': 'ul. Kocia 2, 00-001 Warszawa',
            'phone': '987654321',
            'email': 'kontakt@schronisko-warszawa.pl',
        },
    )
    shelter_gdansk, _ = Shelter.objects.get_or_create(
        name='Schronisko Gdańsk',
        city='gdańsk',
        defaults={
            'address': 'ul. Zwierzęca 10, 80-001 Gdańsk',
            'phone': '555666777',
            'email': 'kontakt@schronisko-gdansk.pl',
        },
    )

    # -------------------------------------------------------------- zwierzęta
    animals_data = [
        {
            'name': 'Burek',
            'species': 'pies',
            'breed': 'Mieszaniec',
            'age': 4,
            'size': 'sredni',
            'gender': 'male',
            'weight_kg': 18.5,
            'is_sterilized': True,
            'is_vaccinated': True,
            'is_chipped': True,
            'good_with_children': True,
            'good_with_dogs': True,
            'good_with_cats': False,
            'status': 'available',
            'shelter': shelter_krakow,
            'description': (
                'Burek to energiczny, 4-letni mieszaniec o złotej sierci. '
                'Uwielbia długie spacery i zabawę z piłką. Świetnie dogaduje się '
                'z dziećmi i innymi psami. Jest w pełni zaszczepiony, '
                'wysterylizowany i zaczipowany.'
            ),
        },
        {
            'name': 'Luna',
            'species': 'kot',
            'breed': 'Europejski krótkowłosy',
            'age': 2,
            'size': 'maly',
            'gender': 'female',
            'weight_kg': 3.8,
            'is_sterilized': True,
            'is_vaccinated': True,
            'is_chipped': False,
            'good_with_children': True,
            'good_with_dogs': False,
            'good_with_cats': True,
            'status': 'available',
            'shelter': shelter_krakow,
            'description': (
                'Luna to spokojna, dwuletnia kotka o czarnej sierci z białym '
                'plamkami na piersi. Lubi ciche miejsca i głaskanie. Idealnie '
                'sprawdzi się w mieszkaniu bez psów. Jest wysterylizowana '
                'i zaszczepiona.'
            ),
        },
        {
            'name': 'Rex',
            'species': 'pies',
            'breed': 'Owczarek niemiecki',
            'age': 7,
            'size': 'duzy',
            'gender': 'male',
            'weight_kg': 35.0,
            'is_sterilized': True,
            'is_vaccinated': True,
            'is_chipped': True,
            'good_with_children': False,
            'good_with_dogs': False,
            'good_with_cats': False,
            'status': 'available',
            'shelter': shelter_warszawa,
            'description': (
                'Rex to wierny i opanowany owczarek niemiecki. Wymaga '
                'doświadczonego opiekuna, który zapewni mu spokój i regularny ruch. '
                'Najlepiej czuje się jako jedyne zwierzę w domu.'
            ),
        },
        {
            'name': 'Mruczka',
            'species': 'kot',
            'breed': 'Perski',
            'age': 5,
            'size': 'sredni',
            'gender': 'female',
            'weight_kg': 4.5,
            'is_sterilized': True,
            'is_vaccinated': True,
            'is_chipped': True,
            'good_with_children': True,
            'good_with_dogs': False,
            'good_with_cats': True,
            'status': 'available',
            'shelter': shelter_warszawa,
            'description': (
                'Mruczka to piękna kotka perska o długiej, białej sierci. '
                'Jest bardzo towarzyska i lubi spać na kolanach. Wymaga '
                'regularnego szczotkowania. Świetnie dogaduje się z innymi kotami.'
            ),
        },
        {
            'name': 'Fafik',
            'species': 'pies',
            'breed': 'Jack Russell Terrier',
            'age': 1,
            'size': 'maly',
            'gender': 'male',
            'weight_kg': 6.2,
            'is_sterilized': False,
            'is_vaccinated': True,
            'is_chipped': True,
            'good_with_children': True,
            'good_with_dogs': True,
            'good_with_cats': False,
            'status': 'available',
            'shelter': shelter_gdansk,
            'description': (
                'Fafik to roczny Jack Russell Terrier pełny energii. Potrzebuje '
                'aktywnego opiekuna, który zabierze go na długie spacery i zabawy. '
                'Bardzo przyjazny wobec ludzi i innych psów.'
            ),
        },
        {
            'name': 'Puszek',
            'species': 'kot',
            'breed': 'Maine Coon',
            'age': 3,
            'size': 'duzy',
            'gender': 'male',
            'weight_kg': 7.8,
            'is_sterilized': True,
            'is_vaccinated': True,
            'is_chipped': True,
            'good_with_children': True,
            'good_with_dogs': True,
            'good_with_cats': True,
            'status': 'available',
            'shelter': shelter_gdansk,
            'description': (
                'Puszek to imponujący Maine Coon o rudej sierci. Mimo '
                'dużych rozmiarów jest bardzo łagodny i towarzyski. Dogaduje '
                'się ze wszystkimi - dziećmi, psami i kotami. Idealny kompan '
                'do rodzinnego domu.'
            ),
        },
        {
            'name': 'Bella',
            'species': 'pies',
            'breed': 'Labrador Retriever',
            'age': 3,
            'size': 'duzy',
            'gender': 'female',
            'weight_kg': 28.0,
            'is_sterilized': True,
            'is_vaccinated': True,
            'is_chipped': True,
            'good_with_children': True,
            'good_with_dogs': True,
            'good_with_cats': True,
            'status': 'pending',
            'shelter': shelter_krakow,
            'description': (
                'Bella to 3-letnia labradorka o czekoladowej sierci. Jest '
                'niezwykle łagodna i cierpliwa, świetna z dziećmi. Uwielbia '
                'wodę i aportowanie. Aktualnie w trakcie procesu adopcyjnego.'
            ),
        },
        {
            'name': 'Filemon',
            'species': 'kot',
            'breed': 'Dachowiec',
            'age': 10,
            'size': 'sredni',
            'gender': 'male',
            'weight_kg': 5.2,
            'is_sterilized': True,
            'is_vaccinated': True,
            'is_chipped': False,
            'good_with_children': False,
            'good_with_dogs': False,
            'good_with_cats': False,
            'status': 'adopted',
            'shelter': shelter_warszawa,
            'description': (
                'Filemon to starszy, 10-letni dachowiec. Lubi spokój i ciche '
                'towarzystwo. Najlepiej czuje się jako jedyny pupil w domu. '
                'Znalazł już swój dom!'
            ),
        },
    ]

    created_animals = {}
    for data in animals_data:
        animal, _ = Animal.objects.get_or_create(name=data['name'], defaults=data)
        created_animals[data['name']] = animal

    # Pobierz i przypisz zdjęcia
    print('Pobieranie zdjęć z Unsplash...')
    for animal in created_animals.values():
        _assign_photo(animal)

    # ------------------------------------------------- wnioski adopcyjne
    applications_data = [
        {
            'animal': created_animals['Bella'],
            'applicant': users['jan_kowalski'],
            'applicant_name': 'Jan Kowalski',
            'applicant_email': 'jan.kowalski@example.com',
            'phone_number': '501234567',
            'experience': 'Miałem psa przez 8 lat. Dorastałem z labradorami.',
            'living_conditions': 'Dom z ogrodem, 120m2. Ogrodzone podwórko.',
            'status': 'review',
        },
        {
            'animal': created_animals['Burek'],
            'applicant': users['anna_nowak'],
            'applicant_name': 'Anna Nowak',
            'applicant_email': 'anna.nowak@example.com',
            'phone_number': '602345678',
            'experience': 'Obecnie mam jednego psa. Regularnie chodzę na spacery.',
            'living_conditions': 'Mieszkanie 65m2 z balkonem. Park w pobliżu.',
            'status': 'new',
        },
        {
            'animal': created_animals['Filemon'],
            'applicant': users['tomek_zielinski'],
            'applicant_name': 'Tomasz Zieliński',
            'applicant_email': 'tomek.z@example.com',
            'phone_number': '703456789',
            'experience': 'Miałem koty przez całe życie. Obecnie szukam spokojnego towarzysza.',
            'living_conditions': 'Mieszkanie 50m2, ciche osiedle. Bez innych zwierząt.',
            'status': 'approved',
            'contact_at': timezone.now(),
            'contact_message': 'Prosimy o kontakt w celu umówienia odbioru Filemona.',
        },
    ]

    for data in applications_data:
        AdoptionApplication.objects.get_or_create(
            animal=data['animal'],
            applicant=data['applicant'],
            defaults=data,
        )

    # -------------------------------------------- wiadomości kontaktowe
    messages_data = [
        {
            'name': 'Jan Kowalski',
            'email': 'jan.kowalski@example.com',
            'sender': users['jan_kowalski'],
            'subject': 'Pytanie o godziny otwarcia schroniska w Krakowie',
            'message': (
                'Dzień dobry, chciałbym odwiedzić schronisko w Krakowie '
                'w najbliższy weekend. Jakie są godziny otwarcia? '
                'Czy mogę przyjść z dziećmi?'
            ),
            'is_read': True,
            'status': 'resolved',
            'reply': 'Schronisko w Krakowie jest otwarte od 9:00 do 17:00 w weekendy. Zapraszamy z dziećmi!',
            'replied_by': admin_user,
            'replied_at': timezone.now(),
        },
        {
            'name': 'Anna Nowak',
            'email': 'anna.nowak@example.com',
            'sender': users['anna_nowak'],
            'subject': 'Wolontariat w schronisku',
            'message': (
                'Dzień dobry, czy jest możliwość wolontariatu w Waszym schronisku? '
                'Chętnie pomogę przy spacerach z psami w weekendy.'
            ),
            'is_read': True,
            'status': 'pending',
        },
        {
            'name': 'Tomasz Zieliński',
            'email': 'tomek.z@example.com',
            'sender': users['tomek_zielinski'],
            'subject': 'Dieta dla starszego kota',
            'message': (
                'Właśnie adoptowałem Filemona i chciałbym wiedzieć, '
                'jaka karma jest dla niego najlepsza? Ma 10 lat, '
                'więc pewnie wymaga specjalnej diety.'
            ),
            'is_read': False,
            'status': 'pending',
        },
    ]

    for data in messages_data:
        ContactMessage.objects.get_or_create(
            sender=data['sender'],
            subject=data['subject'],
            defaults=data,
        )

    print('Dane startowe są gotowe.')


if __name__ == '__main__':
    seed()
