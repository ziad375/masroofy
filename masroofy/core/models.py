from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Registered user of Masroofy."""
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class Category(models.Model):
    SYSTEM = 'system'
    USER_DEFINED = 'user'
    SOURCE_CHOICES = [(SYSTEM, 'System'), (USER_DEFINED, 'User-defined')]

    name   = models.CharField(max_length=100)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default=SYSTEM)
    owner  = models.ForeignKey('User', on_delete=models.CASCADE, null=True, blank=True, related_name='categories')

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Transaction(models.Model):
    INCOME  = 'income'
    EXPENSE = 'expense'
    TYPE_CHOICES = [(INCOME, 'Income'), (EXPENSE, 'Expense')]

    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    category    = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='transactions')
    amount      = models.DecimalField(max_digits=12, decimal_places=2)
    type        = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.CharField(max_length=255, blank=True)
    timestamp   = models.DateField()
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type.title()} – {self.amount} EGP ({self.timestamp})"


class Budget(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category     = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date   = models.DateField()
    end_date     = models.DateField()

    class Meta:
        unique_together = ('user', 'category')

    def calculate_remaining(self):
        from django.db.models import Sum
        spent = Transaction.objects.filter(
            user=self.user, category=self.category,
            type=Transaction.EXPENSE,
            timestamp__range=(self.start_date, self.end_date)
        ).aggregate(total=Sum('amount'))['total'] or 0
        return self.total_amount - spent

    def is_exceeded(self):
        return self.calculate_remaining() < 0

    def __str__(self):
        return f"{self.user.email} – {self.category.name}: {self.total_amount} EGP"
