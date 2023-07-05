import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler
from config import TOKEN
import matplotlib.pyplot as plt
import numpy as np
from random import randint


CATEGORIES = ['Food', 'Transportation', 'Entertainment', 'Utilities', 'Other']
user_data = dict()
logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)


class Money:
    def __init__(self, money_type: str, categories: str, title: str, value: float, date: None):
        self.money_type = money_type
        self.categories = categories
        self.title = title
        self.value = value
        self.date = date

    def __str__(self):
        if self.money_type == "Income":
            return f"{self.date}  {self.categories}  {self.title}: +{self.value}"
        else:
            return f"{self.date}  {self.categories}  {self.title}: -{self.value}"


async def add_income(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    income_parts = ' '.join(context.args).split(' ')
    income_categories = income_parts[0].strip()
    income_title = income_parts[1].strip()
    income_value = float(income_parts[2].strip())
    date_of_income = None
    print(len(income_parts))
    if len(income_parts) > 3:
        try:
            date_of_income = datetime.strptime(income_parts[3].strip(), "%Y-%m-%d").date()
        except ValueError:
            logging.error("Invalid datetime format")
            await update.message.reply_text("Ur datetime of income is invalid..."
                                            "Use %Y-%m-%d format.")
            return

    if not user_data.get(user_id):
        user_data[user_id] = []
    # income1 = Money("Income", "Other", "Pizza", 300, date_of_income)
    if date_of_income is None:
        current_date = datetime.now().date()
        income = Money("Income", income_categories, income_title, income_value, current_date)
    else:
        income = Money("Income", income_categories, income_title, income_value, date_of_income)
    user_data[user_id].append(income)
    print(user_id)
    print(income, income_categories, income_title, income_value, income_parts)
    await update.message.reply_text(f"Income: {income} was successfully added.")


async def add_expense(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    expense_parts = ' '.join(context.args).split(' ')
    expense_categories = expense_parts[0].strip()
    expense_title = expense_parts[1].strip()
    expense_value = float(expense_parts[2].strip())
    date_of_expense = None
    print(len(expense_parts))
    if len(expense_parts) > 3:
        try:
            date_of_expense = datetime.strptime(expense_parts[3].strip(), "%Y-%m-%d").date()
        except ValueError:
            logging.error("Invalid datetime format")
            await update.message.reply_text("Ur datetime of income is invalid..."
                                            "Use %Y-%m-%d format.")
            return

    if not user_data.get(user_id):
        user_data[user_id] = []
    # income1 = Money("Income", "Other", "Pizza", 300, date_of_income)
    if date_of_expense is None:
        current_date = datetime.now().date()
        expense = Money("Expense", expense_categories, expense_title, expense_value, current_date)
    else:
        expense = Money("Expense", expense_categories, expense_title, expense_value, date_of_expense)
    user_data[user_id].append(expense)
    print(user_id)
    print(expense, expense_categories, expense_title, expense_value, expense_parts)
    await update.message.reply_text(f"Expense: {expense} was successfully added.")


async def money_list(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    result_incomes = "Income:\n"
    result_expense = "\nExpense:\n"
    if not user_data.get(user_id):
        await update.message.reply_text(f"U dont have any incomes/expense...")
        return
    user_data[user_id].sort(key=lambda x: x.date)
    for i, j in enumerate(user_data[user_id]):
        if j.money_type == "Income":
            result_incomes += ''.join(f"{i+1}. {j}") + "\n"
        else:
            result_expense += ''.join(f"{i+1}. {j}") + "\n"

    #result = '\n'.join([f"{i+1}. {t}" for i, t in enumerate(user_data[user_id])])
    print(f"{user_data}\n{user_data[user_id]}\n{list(user_data)}\n{list(user_data[user_id])}")
    await update.message.reply_text(result_incomes+result_expense)


async def remove_money(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    if not user_data.get(user_id):
        await update.message.reply_text("U dont have any incomes/expense to remove...")
        return

    try:
        remove_ind = int(context.args[0]) - 1
        transfer = user_data[user_id].pop(remove_ind)
        await update.message.reply_text(f"Income/expense named: {transfer}, was removed!")
    except (ValueError, IndexError):
        await update.message.reply_text("U enter invalid index")


async def clear(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_data[user_id] = []
    await update.message.reply_text("Successfully clear all ur notes!")


async def all_time_statistics(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if not user_data.get(user_id):
        await update.message.reply_text(f"U dont have any incomes/expense...")
        return
    path_pic = statistics_graph(user_data[user_id])
    user_data[user_id].sort(key=lambda x: x.date)
    result_incomes = "Income:\n"
    result_expense = "\nExpense:\n"
    for i, j in enumerate(user_data[user_id]):
        if j.money_type == "Income":
            result_incomes += ''.join(f"{i + 1}. {j}") + "\n"
        else:
            result_expense += ''.join(f"{i + 1}. {j}") + "\n"
    await update.message.reply_photo(path_pic, caption=(result_incomes+result_expense))


def statistics_graph(data) -> str:
    x = np.arange(0, len(data), 1)
    data_of_value = []
    colors = []
    for i in range(len(data)):
        if data[i].money_type == "Income":
            data_of_value.append(data[i].value)
        else:
            data_of_value.append(-data[i].value)

    for i in range(len(data)):
        if data[i].money_type == "Income":
            colors.append("green")
        else:
            colors.append("red")
    plt.bar(x, data_of_value, color=colors)
    plt.title('Income and Expense of all time')
    plt.xlabel('Timeline')
    plt.ylabel('Value($)')
    plt.xticks([])
    plt.grid()
    name_of_picture = str(randint(0, 100))
    print("figure saved")
    plt.savefig(f"{name_of_picture}.png")
    plt.show()
    return f"{name_of_picture}.png"
    

async def start(update: Update, context: CallbackContext) -> None:
    logging.info("Command start was triggered")
    await update.message.reply_text("hello")


async def helper(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(f"Functionality list: blablabla")


async def categories_list(update: Update, context: CallbackContext) -> None:
    string_of_categories = "\n - ".join(CATEGORIES)
    await update.message.reply_text(f'List of Categories:\n - {string_of_categories}')


def run():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", helper))
    app.add_handler(CommandHandler("categories", categories_list))
    app.add_handler(CommandHandler("addincome", add_income))
    app.add_handler(CommandHandler("addexpense", add_expense))
    app.add_handler(CommandHandler("moneylist", money_list))
    app.add_handler(CommandHandler("allstatistics", all_time_statistics))
    app.run_polling()


if __name__ == "__main__":
    run()

