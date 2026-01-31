from django.urls import path
from . import views

urlpatterns = [
    # Extension API
    path('get-credentials/', views.get_credentials, name='get_credentials'),
    
    # Dashboard Actions
    path('dashboard-data/', views.dashboard_data, name='dashboard_data'),
    path('add-account/', views.add_account, name='add_account'),
    path('generate-card/', views.generate_card, name='generate_card'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('delete-card/', views.delete_card, name='delete_card'),
]
