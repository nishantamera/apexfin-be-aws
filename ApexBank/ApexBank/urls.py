"""ApexBank URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.debug import default_urlconf
from Server import views

urlpatterns = [
    path('api-auth', include('rest_framework.urls')),
    path('', default_urlconf),
    path('admin/', admin.site.urls),

    # authentication path
    path('apex-bank/account/signup', views.signup),
    path('apex-bank/account/login', views.login),
    path('apex-bank/get/banking-account-summary', views.get_dashboard_details),
    path('apex-bank/get/savings-account-summary', views.get_savings_account_details),
    path('apex-bank/get/payee-details', views.get_payee_details),
    path('apex-bank/get/investment-portfolio', views.get_investment_details),
    path('apex-bank/get/credit-card-summary', views.get_credit_card_details),
    path('apex-bank/get/user-details', views.get_user_details),
    path('apex-bank/post/add-payee', views.add_payee),
    path('apex-bank/post/delete-payee', views.delete_payee),
    path('apex-bank/post/process-transaction', views.process_transaction)
]
