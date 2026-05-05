from django.urls import path
from . import views

urlpatterns = [
    path('',              views.dashboard_view,        name='dashboard'),
    path('register/',     views.register_view,         name='register'),
    path('login/',        views.login_view,            name='login'),
    path('logout/',       views.logout_view,           name='logout'),
    path('expense/add/',  views.add_expense_view,      name='add_expense'),
    path('income/add/',   views.add_income_view,       name='add_income'),
    path('history/',      views.history_view,          name='history'),
    path('transaction/<int:transaction_id>/delete/', views.delete_transaction_view, name='delete_transaction'),
    path('budget/set/',   views.set_budget_view,       name='set_budget'),
]
