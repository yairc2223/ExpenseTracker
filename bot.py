import telebot
from telebot import types
import matplotlib.pyplot as plt
import io
import json
from datetime import datetime

BOT_KEY = "6977507006:AAFrtCHEYkIiHllph9nUiFARsPUSlzAOtds"


class Transaction:
    def __init__(self, amount, category, transaction_type, date=None):
        self.amount = amount
        self.category = category
        self.transaction_type = transaction_type  # 'income' or 'expense'
        self.date = date if date else datetime.now()

    def __repr__(self):
        return f"{self.transaction_type.title()} - {self.category.title()}: ${self.amount} on {self.date.strftime('%Y-%m-%d')}"


class Storage:
    def __init__(self, filename='data.json'):
        self.filename = filename
        self.data = self.load_data()

    def load_data(self):
        try:
            with open(self.filename, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"transactions": []}

    def save_data(self):
        with open(self.filename, 'w') as file:
            json.dump(self.data, file, default=str, indent=4)

    def add_transaction(self, transaction):
        self.data['transactions'].append(transaction.__dict__)
        self.save_data()

    def get_transactions_for_month(self, year, month):
        transactions = [Transaction(**t) for t in self.data['transactions']]
        for transaction in transactions:
            # Assuming transaction.date is a string with format 'YYYY-MM-DD HH:MM:SS.SSSSSS'
            date_part = transaction.date.split(" ")[0]  # Keep only the date part
            transaction.date = datetime.strptime(date_part, '%Y-%m-%d')
        return [t for t in transactions if t.date.month == month and t.date.year == year]

    # storage.py - Add these methods to the Storage class

    def get_transactions_by_category(self, transaction_type):
        transactions = self.get_transactions_for_month(datetime.now().year, datetime.now().month)
        by_category = {}
        for t in transactions:
            if t.transaction_type == transaction_type:
                if t.category not in by_category:
                    by_category[t.category] = 0
                by_category[t.category] += t.amount
        return by_category

    # Modify the Storage class in storage.py to include budget management

    def save_budget(self, budget):
        if 'budgets' not in self.data:
            self.data['budgets'] = {}
        self.data['budgets'][budget.category] = budget.limit
        self.save_data()

    def get_budgets(self):
        budgets = {}
        if 'budgets' in self.data:
            for category, limit in self.data['budgets'].items():
                budgets[category] = Budget(category, limit)
        return budgets


class Budget:
    def __init__(self, category, limit):
        self.category = category
        self.limit = limit
        self.spent = 0

    def add_expense(self, amount):
        self.spent += amount

    def get_remaining_budget(self):
        return self.limit - self.spent

    def __str__(self):
        return f"Budget for {self.category}: Limit ${self.limit}, Spent ${self.spent}, Remaining ${self.get_remaining_budget()}"


TOKEN = BOT_KEY  # Use your actual token here
bot = telebot.TeleBot(TOKEN)
storage = Storage()
temp_storage = {}


def send_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Add Transaction")
    btn2 = types.KeyboardButton("View Summary")
    btn3 = types.KeyboardButton("Set Budget")
    btn4 = types.KeyboardButton("View Budgets")
    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "View Summary")
def view_summary(message):
    year, month = datetime.now().year, datetime.now().month
    try:
        transactions = storage.get_transactions_for_month(year, month)
        income = sum(t.amount for t in transactions if t.transaction_type == 'income')
        expenses = sum(t.amount for t in transactions if t.transaction_type == 'expense')
        summary_text = f"📅 Current Month Summary:\n\n💰 Total Income: ${income}\n💸 Total Expenses: ${expenses}\n🔍 Balance: ${income - expenses}"
        bot.send_message(message.chat.id, summary_text, parse_mode='Markdown')
    except Exception as e:
        print(f"Error in view_summary: {e}")
        bot.send_message(message.chat.id, "An error occurred while generating the summary.")


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    send_main_menu(message)


@bot.message_handler(func=lambda message: message.text == "Add Transaction")
def add_transaction_step1(message):
    markup = types.InlineKeyboardMarkup()
    btn_income = types.InlineKeyboardButton("Income", callback_data="add_income")
    btn_expense = types.InlineKeyboardButton("Expense", callback_data="add_expense")
    markup.add(btn_income, btn_expense)
    bot.send_message(message.chat.id, "Select transaction type:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ["add_income", "add_expense"])
def handle_transaction_type(call):
    bot.answer_callback_query(call.id)
    transaction_type = "income" if call.data == "add_income" else "expense"

    categories = {
        "income": ["Salary", "Gifts", "Other"],
        "expense": ["Rent", "Food", "Health", "Car", "Other"]
    }

    markup = types.InlineKeyboardMarkup()
    for category in categories[transaction_type]:
        callback_data = f"category_{transaction_type}_{category}"
        markup.add(types.InlineKeyboardButton(category, callback_data=callback_data))

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Select category:",
                          reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("category_"))
def handle_category_selection(call):
    bot.answer_callback_query(call.id)
    _, transaction_type, category = call.data.split('_')
    temp_storage[call.from_user.id] = {'type': transaction_type, 'category': category}
    msg = bot.send_message(call.message.chat.id, "Enter the amount:")
    bot.register_next_step_handler(msg, process_amount, call.from_user.id)


def process_amount(message, user_id):
    try:
        amount = float(message.text)
        transaction_info = temp_storage[user_id]
        transaction = Transaction(amount, transaction_info['category'], transaction_info['type'])
        storage.add_transaction(transaction)
        bot.reply_to(message, "Transaction added successfully!")
        del temp_storage[user_id]  # Clean up after adding
        send_main_menu(message)  # Send the main menu again
        check_budget_alerts(transaction)
    except ValueError:
        bot.reply_to(message, "Invalid amount. Please enter a numeric value.")
        del temp_storage[user_id]  # Ensure to clean up even on failure
    except Exception as e:
        bot.reply_to(message, "Error processing transaction. Try again.")
        del temp_storage[user_id]  # Ensure to clean up even on failure


def check_budget_alerts(transaction):
    if transaction.transaction_type != "expense":
        return
    budget = storage.get_budgets().get(transaction.category)
    if not budget:
        return
    spending = storage.get_transactions_by_category('expense').get(transaction.category, 0)
    if spending + transaction.amount > budget.limit * 0.9:  # Alert if spending exceeds 90% of the budget
        message = f"⚠️ Alert: Your spending for {transaction.category} is close to the budget limit."
        bot.send_message(chat_id=transaction.user_id, text=message)  # Assumes transaction includes user_id


@bot.message_handler(func=lambda message: message.text == "View Budgets")
def view_budgets(message):
    try:
        budgets = storage.get_budgets()
        spending = storage.get_transactions_by_category('expense')
        response = "📅 Current Month Budgets vs. Spending:\n"
        for category, budget in budgets.items():
            spent = spending.get(category, 0)
            response += f"\n{category}: Budgeted ${budget.limit}, Spent ${spent}, Remaining ${budget.limit - spent}"
        bot.send_message(message.chat.id, response, parse_mode='Markdown')
    except Exception as e:
        print(f"Error in view_budgets: {e}")
        bot.send_message(message.chat.id, "An error occurred while retrieving budget information.")

@bot.message_handler(func=lambda message: message.text == "Set Budget")
def set_budget_step1(message):
    markup = types.InlineKeyboardMarkup()
    categories = ["Salary", "Gifts", "Other", "Rent", "Food", "Health", "Car"]  # Example categories
    for category in categories:
        markup.add(types.InlineKeyboardButton(category, callback_data=f"setbudget_{category}"))
    bot.send_message(message.chat.id, "Select a category for the budget:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("setbudget_"))
def handle_budget_category_selection(call):
    category = call.data[len("setbudget_"):]
    temp_storage[call.from_user.id] = {'category': category}
    msg = bot.send_message(call.message.chat.id, "Enter the budget limit:")
    bot.register_next_step_handler(msg, process_budget_limit, call.from_user.id, category)


def process_budget_limit(message, user_id, category):
    try:
        limit = float(message.text)
        budget = Budget(category, limit)
        storage.save_budget(budget)
        bot.reply_to(message, f"Budget for {category} set to ${limit}")
        del temp_storage[user_id]
    except ValueError:
        bot.reply_to(message, "Invalid amount. Please enter a numeric value.")


if __name__ == '__main__':
    bot.polling(none_stop=True)
