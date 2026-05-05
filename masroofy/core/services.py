"""
Service / Controller Layer
Maps directly to the Class-Sequence Usage Table in the SDS.
Every method here corresponds to a message in a sequence diagram.
"""
from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum
from .models import User, Transaction, Budget, Category
import datetime


# ── 1. User Registration ──────────────────────────────────────────────────────

class RegistrationController:
    @staticmethod
    def validate_input(name: str, email: str, password: str) -> bool:
        return bool(name and email and password and len(password) >= 6)

    @staticmethod
    def register(name: str, email: str, password: str) -> bool:
        """Returns True on success, False if email already exists."""
        if User.objects.filter(email=email).exists():
            return False
        user = User.objects.create_user(username=email, email=email, password=password)
        user.first_name = name
        user.save()
        RegistrationController.send_confirmation(email)
        return True

    @staticmethod
    def send_confirmation(email: str):
        # Placeholder – would send a real email in production
        print(f"[INFO] Confirmation sent to {email}")


# ── 2. User Login ─────────────────────────────────────────────────────────────

class AuthController:
    @staticmethod
    def login(request, email: str, password: str) -> bool:
        """Authenticate and create session. Returns True on success."""
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return True
        return False

    @staticmethod
    def logout_user(request):
        logout(request)


# ── 3 & 4. Transaction Controller (Expense + Income) ─────────────────────────

class TransactionController:
    @staticmethod
    def validate_amount(amount) -> bool:
        try:
            return float(amount) > 0
        except (TypeError, ValueError):
            return False

    @staticmethod
    def add_expense(user, amount, category_id, date, desc='') -> dict:
        """
        Add expense transaction and check budget.
        Returns {'success': bool, 'budget_exceeded': bool, 'message': str}
        """
        if not TransactionController.validate_amount(amount):
            return {'success': False, 'budget_exceeded': False, 'message': 'Invalid amount'}

        category = Category.objects.get(id=category_id)
        transaction = Transaction.objects.create(
            user=user, category=category, amount=amount,
            type=Transaction.EXPENSE, description=desc, timestamp=date
        )

        # Check budget limit
        budget_exceeded = BudgetController.check_limit(user, category, amount)
        if budget_exceeded:
            return {'success': True, 'budget_exceeded': True,
                    'message': 'Warning: Budget Limit Exceeded!', 'transaction': transaction}

        return {'success': True, 'budget_exceeded': False,
                'message': 'Expense Added Successfully', 'transaction': transaction}

    @staticmethod
    def add_income(user, amount, category_id, date, desc='') -> dict:
        """Add income transaction."""
        if not TransactionController.validate_amount(amount):
            return {'success': False, 'message': 'Invalid amount'}

        category = Category.objects.get(id=category_id)
        transaction = Transaction.objects.create(
            user=user, category=category, amount=amount,
            type=Transaction.INCOME, description=desc, timestamp=date
        )
        DashboardController.refresh_dashboard(user)
        return {'success': True, 'message': 'Income Added Successfully', 'transaction': transaction}

    @staticmethod
    def delete_transaction(transaction_id: int, user) -> dict:
        """Delete transaction and recalculate budget."""
        try:
            transaction = Transaction.objects.get(id=transaction_id, user=user)
            category = transaction.category
            transaction.delete()
            BudgetController.recalculate_budget(user, category)
            DashboardController.refresh_dashboard(user)
            return {'success': True, 'message': 'Transaction Deleted & Balance Restored'}
        except Transaction.DoesNotExist:
            return {'success': False, 'message': 'Transaction not found'}


# ── Budget Controller ─────────────────────────────────────────────────────────

class BudgetController:
    @staticmethod
    def check_limit(user, category, new_amount) -> bool:
        """Returns True if budget is exceeded after adding new_amount."""
        today = datetime.date.today()
        budget = Budget.objects.filter(
            user=user, category=category,
            start_date__lte=today, end_date__gte=today
        ).first()
        if not budget:
            return False
        return budget.is_exceeded()

    @staticmethod
    def recalculate_budget(user, category):
        """Recalculate after a transaction is deleted."""
        # Budget.calculate_remaining() is always live – nothing to do here
        pass

    @staticmethod
    def set_budget_limit(user, category_id: int, limit_amount, start_date, end_date) -> bool:
        """Create or update budget limit. Returns True on success."""
        try:
            limit = float(limit_amount)
            if limit <= 0:
                return False
        except (TypeError, ValueError):
            return False

        category = Category.objects.get(id=category_id)
        Budget.objects.update_or_create(
            user=user, category=category,
            defaults={'total_amount': limit, 'start_date': start_date, 'end_date': end_date}
        )
        return True

    @staticmethod
    def get_budget(user, category_id):
        today = datetime.date.today()
        return Budget.objects.filter(
            user=user, category_id=category_id,
            start_date__lte=today, end_date__gte=today
        ).first()


# ── Dashboard Controller ──────────────────────────────────────────────────────

class DashboardController:
    @staticmethod
    def load_dashboard(user) -> dict:
        """Aggregate all financial data for the dashboard."""
        transactions = TransactionController_Repo.get_transactions(user)
        total_income    = DashboardController.get_total_income(user)
        total_expenses  = DashboardController.get_total_expenses(user)
        remaining       = DashboardController.get_remaining_budget(user)
        budgets         = Budget.objects.filter(user=user).select_related('category')

        budget_status = []
        for b in budgets:
            budget_status.append({
                'category': b.category.name,
                'limit': b.total_amount,
                'remaining': b.calculate_remaining(),
                'exceeded': b.is_exceeded(),
            })

        return {
            'transactions': transactions,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'remaining_budget': remaining,
            'budget_status': budget_status,
        }

    @staticmethod
    def get_total_income(user) -> float:
        result = Transaction.objects.filter(user=user, type=Transaction.INCOME)\
            .aggregate(total=Sum('amount'))['total']
        return float(result or 0)

    @staticmethod
    def get_total_expenses(user) -> float:
        result = Transaction.objects.filter(user=user, type=Transaction.EXPENSE)\
            .aggregate(total=Sum('amount'))['total']
        return float(result or 0)

    @staticmethod
    def get_remaining_budget(user) -> float:
        return DashboardController.get_total_income(user) - DashboardController.get_total_expenses(user)

    @staticmethod
    def refresh_dashboard(user):
        pass  # In a real app, would push update via WebSocket / signal


class TransactionController_Repo:
    @staticmethod
    def get_transactions(user):
        return Transaction.objects.filter(user=user).select_related('category').order_by('-timestamp')
