from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm  

from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect, get_object_or_404
from .models import Transaction, Budget
from .forms import TransactionForm
from django.db.models import Sum
from datetime import datetime


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the new user to the database
            login(request, user)  # Log in the new user
            messages.success(request, 'Registration successful!')
            return redirect('login')  # Redirect to home or dashboard
        else:
            messages.error(request, 'Registration failed. Please try again.')
    else:
        form = UserCreationForm()

    return render(request, 'finance/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('home')  # Redirect to home or another page
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'finance/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have successfully logged out.')
    return redirect('login')  # Redirect to login page after logout

def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'finance/home.html')








def transaction_list(request):
    if not request.user.is_authenticated:
        return redirect('login')
    transactions = Transaction.objects.filter(user=request.user)
    return render(request, 'finance/transaction_list.html', {'transactions': transactions})


def add_transaction(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('track_expenses')
    else:
        form = TransactionForm()
    return render(request, 'finance/add_transaction.html', {'form': form})


def update_transaction(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            return redirect('track_expenses')
    else:
        form = TransactionForm(instance=transaction)
    return render(request, 'finance/update_transaction.html', {'form': form})


def delete_transaction(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        return redirect('track_expenses')
    return render(request, 'finance/delete_transaction.html', {'transaction': transaction})





from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from datetime import datetime


def financial_report(request):
    if not request.user.is_authenticated:
        return redirect('login')
    # Get the current date
    today = datetime.now()

    # Monthly Report
    month_start = today.replace(day=1)
    monthly_income = Transaction.objects.filter(
        user=request.user, transaction_type='income', date__gte=month_start
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    monthly_expenses = Transaction.objects.filter(
        user=request.user, transaction_type='expense', date__gte=month_start
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    monthly_savings = monthly_income - monthly_expenses

    # Yearly Report
    year_start = today.replace(month=1, day=1)
    yearly_income = Transaction.objects.filter(
        user=request.user, transaction_type='income', date__gte=year_start
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    yearly_expenses = Transaction.objects.filter(
        user=request.user, transaction_type='expense', date__gte=year_start
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    yearly_savings = yearly_income - yearly_expenses

    context = {
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_savings': monthly_savings,
        'yearly_income': yearly_income,
        'yearly_expenses': yearly_expenses,
        'yearly_savings': yearly_savings,
    }
    return render(request, 'finance/financial_report.html', context)







def set_budget(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        category = request.POST.get('category')
        monthly_budget = request.POST.get('monthly_budget')

        # Update or create the budget for the user
        budget, created = Budget.objects.update_or_create(
            user=request.user,
            category=category,
            defaults={'monthly_budget': monthly_budget}
        )
        return redirect('view_budget')

    return render(request, 'finance/set_budget.html', {
        'categories': [choice[0] for choice in Transaction.CATEGORY_CHOICES]
    })


def view_budget(request):
    if not request.user.is_authenticated:
        return redirect('login')
    budgets = Budget.objects.filter(user=request.user)
    today = datetime.now()
    month_start = today.replace(day=1)

    # Calculate expenses for each category
    category_expenses = (
        Transaction.objects.filter(
            user=request.user,
            transaction_type='expense',
            date__gte=month_start
        )
        .values('category')
        .annotate(total=Sum('amount'))
    )

    # Merge budget and expense data
    budget_data = []
    for budget in budgets:
        total_spent = next(
            (expense['total'] for expense in category_expenses if expense['category'] == budget.category), 0
        )
        exceeded = total_spent > budget.monthly_budget
        budget_data.append({
            'category': budget.category,
            'monthly_budget': budget.monthly_budget,
            'total_spent': total_spent,
            'exceeded': exceeded,
        })

    return render(request, 'finance/view_budget.html', {'budget_data': budget_data})

def track_expenses(request):
    if not request.user.is_authenticated:
        return redirect('login')
    transactions = Transaction.objects.filter(user=request.user)
    return render(request, 'finance/track_expenses.html', {'transactions': transactions})

