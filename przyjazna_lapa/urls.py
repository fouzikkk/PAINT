from django.contrib import admin
from django.urls import path
from core import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin-panel-django/', admin.site.urls),
    path('', views.home, name='home'),
    path('zwierzeta/', views.animal_list, name='animals_list'),
    path('zwierzeta/<int:animal_id>/', views.animal_details, name='animal_details'),
    path('adopcja/', views.adoption_form_view, name='adoption_form'),
    path('moje-wnioski/', views.my_applications, name='my_applications'),
    path('moje-wnioski/<int:application_id>/wycofaj/', views.cancel_application, name='cancel_application'),
    path('moje-wiadomosci/', views.my_messages, name='my_messages'),
    path('profil/', views.profile, name='profile'),
    path('kontakt/', views.contact_view, name='contact_form'),
    path('logowanie/', views.login_register_view, name='login'),
    path('wyloguj/', views.logout_view, name='logout'),
    path('admin-app/', views.admin_panel_view, name='admin_panel'),
    path('admin-app/ogloszenia/', views.admin_animals_view, name='admin_animals'),
    path('admin-app/ogloszenia/dodaj/', views.admin_animal_add, name='admin_animal_add'),
    path('admin-app/zwierze/usun/', views.admin_animal_delete, name='admin_animal_delete'),
    path('admin-app/zwierze/<int:animal_id>/edytuj/', views.admin_animal_edit, name='admin_animal_edit'),
    path('admin-app/schroniska/', views.admin_shelters_view, name='admin_shelters'),
    path('admin-app/schroniska/dodaj/', views.admin_shelter_create, name='admin_shelter_create'),
    path('admin-app/uzytkownicy/', views.admin_users_view, name='admin_users'),
    path('admin-app/wnioski/', views.admin_applications_view, name='admin_applications'),
    path('admin-app/wniosek/status/', views.admin_application_update, name='admin_application_update'),
    path('admin-app/wiadomosci/', views.admin_messages_view, name='admin_messages'),
    path('admin-app/wiadomosc/status/', views.admin_message_update, name='admin_message_update'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
