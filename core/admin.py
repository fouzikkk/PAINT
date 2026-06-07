from django.contrib import admin
from .models import (
    AdoptionApplication,
    Animal,
    ApplicationStatusHistory,
    ContactMessage,
    Shelter,
    UserProfile,
)

@admin.register(Shelter)
class ShelterAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'phone', 'email')
    search_fields = ('name', 'city', 'email')

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ('name', 'species', 'size', 'gender', 'status', 'shelter')
    list_filter = ('species', 'size', 'gender', 'status', 'shelter')
    search_fields = ('name', 'breed', 'description', 'shelter__name', 'shelter__city')

@admin.register(AdoptionApplication)
class AdoptionApplicationAdmin(admin.ModelAdmin):
    list_display = ('animal', 'applicant_name', 'applicant', 'phone_number', 'status', 'created_at')
    list_filter = ('status', 'created_at')

@admin.register(ApplicationStatusHistory)
class ApplicationStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('application', 'old_status', 'new_status', 'changed_by', 'created_at')
    list_filter = ('new_status', 'created_at')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'status', 'replied_at', 'created_at')
    list_filter = ('status', 'created_at')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'phone_number', 'updated_at')
    search_fields = ('user__username', 'user__email', 'full_name', 'phone_number')

