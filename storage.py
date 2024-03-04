# storage.py

import json
from datetime import datetime



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

    def get_transactions_for_current_month(self):
        current_month = datetime.now().month
        current_year = datetime.now().year
        transactions = [Transaction(**t) for t in self.data['transactions']]
        return [t for t in transactions if t.date.month == current_month and t.date.year == current_year]

# storage.py - Add these methods to the Storage class

    def get_transactions_by_category(self, transaction_type):
        transactions = self.get_transactions_for_current_month()
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
