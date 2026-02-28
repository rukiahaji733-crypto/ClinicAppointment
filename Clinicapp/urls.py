from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.api_login),
    path('appointments/', views.api_appointments),
    path('book-appointment/', views.api_book_appointment),
    path('create-doctor/', views.create_doctor),
    path('cancel-appointment/<int:id>/', views.api_cancel_appointment),
    path('doctors/', views.api_doctors),
    path('delete-doctor/<int:id>/', views.delete_doctor),
    
    path('dashboard/', views.api_dashboard),
    path('register/', views.api_register),
    path('register-patient/', views.api_register_patient),
]
