from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .services import (
    RegistrationController, AuthController,
    TransactionController, BudgetController, DashboardController,
    TransactionController_Repo
)
from .forms import RegisterForm, LoginForm, TransactionForm, BudgetForm
from .models import Transaction


# ── 1. User Registration ──────────────────────────────────────────────────────
def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        if not RegistrationController.validate_input(d['name'], d['email'], d['password']):
            messages.error(request, 'Invalid input. Please check all fields.')
        elif RegistrationController.register(d['name'], d['email'], d['password']):
            messages.success(request, 'Registration Successful! Please log in.')
            return redirect('login')
        else:
            messages.error(request, 'Email already used. Please try another.')
    return render(request, 'core/register.html', {'form': form})


# ── 2. User Login ─────────────────────────────────────────────────────────────
def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        if AuthController.login(request, d['email'], d['password']):
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    AuthController.logout_user(request)
    return redirect('login')


# ── 6. View Dashboard & Calculate Remaining Budget ────────────────────────────
@login_required
def dashboard_view(request):
    data = DashboardController.load_dashboard(request.user)
    return render(request, 'core/dashboard.html', data)


# ── 3. Add Expense ────────────────────────────────────────────────────────────
@login_required
def add_expense_view(request):
    form = TransactionForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        result = TransactionController.add_expense(
            request.user, d['amount'], d['category'].id, d['date'], d.get('description', '')
        )
        if result['success']:
            if result['budget_exceeded']:
                messages.warning(request, result['message'])
            else:
                messages.success(request, result['message'])
            return redirect('dashboard')
        else:
            messages.error(request, result['message'])
    return render(request, 'core/add_transaction.html', {'form': form, 'transaction_type': 'Expense'})


# ── 4. Add Income ─────────────────────────────────────────────────────────────
@login_required
def add_income_view(request):
    form = TransactionForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        result = TransactionController.add_income(
            request.user, d['amount'], d['category'].id, d['date'], d.get('description', '')
        )
        if result['success']:
            messages.success(request, result['message'])
            return redirect('dashboard')
        else:
            messages.error(request, result['message'])
    return render(request, 'core/add_transaction.html', {'form': form, 'transaction_type': 'Income'})


# ── 5. Delete Transaction ─────────────────────────────────────────────────────
@login_required
def delete_transaction_view(request, transaction_id):
    result = TransactionController.delete_transaction(transaction_id, request.user)
    if result['success']:
        messages.success(request, result['message'])
    else:
        messages.error(request, result['message'])
    return redirect('history')


# ── Transaction History ───────────────────────────────────────────────────────
@login_required
def history_view(request):
    transactions = TransactionController_Repo.get_transactions(request.user)
    return render(request, 'core/history.html', {'transactions': transactions})


# ── 7. Set Category Budget ────────────────────────────────────────────────────
@login_required
def set_budget_view(request):
    form = BudgetForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        success = BudgetController.set_budget_limit(
            request.user, d['category'].id, d['amount'], d['start_date'], d['end_date']
        )
        if success:
            messages.success(request, 'Budget Set Successfully')
            return redirect('dashboard')
        else:
            messages.error(request, 'Amount must be greater than 0')
    return render(request, 'core/set_budget.html', {'form': form})
