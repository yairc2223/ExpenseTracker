# user_interface.py

from storage import Storage
from transaction import Transaction
from budget_manager import Budget


def input_transaction():
    transaction_type = input("Enter transaction type (income/expense): ").lower().strip()
    amount = float(input("Enter amount: "))
    category = input("Enter category: ").lower().strip()
    return Transaction(amount, category, transaction_type)


# user_interface.py - Modify the display_current_status function

def display_current_status(storage):
    transactions = storage.get_transactions_for_current_month()
    income_by_category = storage.get_transactions_by_category('income')
    expense_by_category = storage.get_transactions_by_category('expense')

    total_income = sum(income_by_category.values())
    total_expense = sum(expense_by_category.values())
    balance = total_income - total_expense

    print("\nCurrent Month Summary:")
    print(f"Total Income: ${total_income}")
    for category, amount in income_by_category.items():
        print(f"   {category.title()}: ${amount}")

    print(f"Total Expense: ${total_expense}")
    for category, amount in expense_by_category.items():
        print(f"   {category.title()}: ${amount}")

    print(f"Balance: ${balance}")

# user_interface.py


def set_budget(storage):
    category = input("Enter budget category: ")
    limit = float(input("Enter budget limit: "))
    budget = Budget(category, limit)
    storage.save_budget(budget)
    print("Budget set successfully.")

def display_budgets(storage):
    budgets = storage.get_budgets()
    if not budgets:
        print("No budgets set.")
    for budget in budgets.values():
        print(budget)


def main_loop():
    storage = Storage()
    while True:
        print("\nFinance Tracker")
        print("1. Enter a new transaction")
        print("2. Display current status")
        print("3. Exit")
        choice = input("Choose an option: ")

        if choice == '1':
            transaction = input_transaction()
            storage.add_transaction(transaction)
            print("Transaction added successfully.")
        elif choice == '2':
            display_current_status(storage)
        elif choice == '3':
            break
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    main_loop()
