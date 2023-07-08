import json
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler
from config import TOKEN
import matplotlib.pyplot as plt
import numpy as np
from random import randint

DATA_FILE = 'data.json'
CATEGORIES = ['food', 'transportation', 'entertainment', 'utilities', 'other']
user_data = dict()
logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)


class Money:
    def __init__(self, money_type: str, categories: str, title: str, value: float, date: datetime.date):
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


def load_data():
    global user_data
    try:
        with open(DATA_FILE, 'r') as file:
            data = json.load(file)
            user_data = {int(user_id): [deserialize_money(money) for money in money_list] for user_id, money_list in data.items()}
            logging.info('Use data from .JSON File successfully')
    except FileNotFoundError:
        logging.info('FileNotFoundError - use empty dict')
        user_data = {}


def deserialize_money(data):
    if isinstance(data, dict):
        return Money(**data)

    raise ValueError("Invalid data format for deserialization.")


def save_data():
    with open(DATA_FILE, 'w') as file:
        json.dump(user_data, file, indent=4, default=serialize_money)
    logging.info("Saved user_data .JSON format")


def serialize_money(obj):
    if isinstance(obj, Money):
        return {
            'money_type': obj.money_type,
            'categories': obj.categories,
            'title': obj.title,
            'value': obj.value,
            'date': obj.date.strftime('%Y-%m-%d')
        }
    raise TypeError(f"Object of type '{obj.__class__.__name__}' is not JSON serializable.")


async def add_income(update: Update, context: CallbackContext) -> None:
    logging.info("Command add_income was triggered")
    global CATEGORIES
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

    if income_categories.lower() not in CATEGORIES:
        CATEGORIES.append(income_categories.lower())

    if not user_data.get(user_id):
        user_data[user_id] = []

    if date_of_income is None:
        current_date = datetime.now().date()
        income = Money("Income", income_categories, income_title, income_value, current_date)
    else:
        income = Money("Income", income_categories, income_title, income_value, date_of_income)
    user_data[user_id].append(income)
    save_data()
    await update.message.reply_text(f"Income: {income} was successfully added.")


async def add_expense(update: Update, context: CallbackContext) -> None:
    logging.info("Command add_expense was triggered")
    global CATEGORIES
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

    if expense_categories.lower() not in CATEGORIES:
        CATEGORIES.append(expense_categories.lower())

    if not user_data.get(user_id):
        user_data[user_id] = []

    if date_of_expense is None:
        current_date = datetime.now().date()
        expense = Money("Expense", expense_categories, expense_title, expense_value, current_date)
    else:
        expense = Money("Expense", expense_categories, expense_title, expense_value, date_of_expense)
    user_data[user_id].append(expense)
    save_data()
    await update.message.reply_text(f"Expense: {expense} was successfully added.")


async def money_list(update: Update, context: CallbackContext) -> None:
    logging.info("Command money_list was triggered")
    user_id = update.message.from_user.id
    result_incomes = "⬆️Income:\n"
    result_expense = "\n⬇️Expense:\n"
    if not user_data.get(user_id):
        await update.message.reply_text(f"U dont have any incomes/expense...")
        return
    user_data[user_id].sort(key=lambda x: x.date)
    for i, j in enumerate(user_data[user_id]):
        if j.money_type == "Income":
            result_incomes += ''.join(f"{i+1}. {j}") + "\n"
        else:
            result_expense += ''.join(f"{i+1}. {j}") + "\n"

    await update.message.reply_text(result_incomes+result_expense)


async def remove_money(update: Update, context: CallbackContext) -> None:
    logging.info("Command remove_money was triggered")
    user_id = update.message.from_user.id

    if not user_data.get(user_id):
        await update.message.reply_text("U dont have any incomes/expense to remove...")
        return

    try:
        remove_ind = int(context.args[0]) - 1
        transfer = user_data[user_id].pop(remove_ind)
        save_data()
        await update.message.reply_text(f"Income/expense named: {transfer}, was removed!")
    except (ValueError, IndexError):
        await update.message.reply_text("U enter invalid index")


async def clear(update: Update, context: CallbackContext) -> None:
    logging.info("Command clear was triggered")
    user_id = update.message.from_user.id
    user_data[user_id] = []
    await update.message.reply_text("Successfully clear all ur notes!")


async def all_time_statistics(update: Update, context: CallbackContext) -> None:
    logging.info("Command all_time_statistics was triggered")
    user_id = update.message.from_user.id
    if not user_data.get(user_id):
        await update.message.reply_text(f"U dont have any incomes/expense...")
        return
    path_pic = statistics_graph(user_data[user_id])
    user_data[user_id].sort(key=lambda x: x.date)
    result_incomes = "⬆️Income:\n"
    result_expense = "\n⬇️Expense:\n"
    for i, j in enumerate(user_data[user_id]):
        if j.money_type == "Income":
            result_incomes += ''.join(f"{i + 1}. {j}") + "\n"
        else:
            result_expense += ''.join(f"{i + 1}. {j}") + "\n"
    await update.message.reply_photo(path_pic, caption=(result_incomes+result_expense))


def statistics_graph(data) -> str:
    logging.info("Command statistics_graph was triggered")
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
    return f"{name_of_picture}.png"
    

async def expense_per_month(update: Update, context: CallbackContext) -> None:
    logging.info("Command expense_per_month was triggered")
    user_id = update.message.from_user.id
    today = datetime.now().date()
    start_date = today.replace(day=1)
    end_date = today
    datalist = user_data[user_id]
    month_expenses = []
    result_expense = ""

    if not user_data.get(user_id):
        await update.message.reply_text(f"U dont have any expense...")
        return

    for i in range(len(datalist)):
        if datalist[i].money_type == "Expense":
            if start_date <= datalist[i].date <= end_date:
                month_expenses.append(datalist[i])

    if len(month_expenses) == 0:
        await update.message.reply_text(f"You dont have any expense for a month...")
        return

    for i, j in enumerate(month_expenses):
        result_expense += ''.join(f"{i + 1}. {j}") + "\n"

    await update.message.reply_text(f"Expenses for the month:\n{result_expense}")


async def expense_per_week(update: Update, context: CallbackContext) -> None:
    logging.info("Command expense_per_week was triggered")
    user_id = update.message.from_user.id
    today = datetime.now().date()
    start_date = today - timedelta(days=today.weekday())
    end_date = today
    datalist = user_data[user_id]
    week_expenses = []
    result_expense = ""

    if not user_data.get(user_id):
        await update.message.reply_text(f"U dont have any expense...")
        return

    for i in range(len(datalist)):
        if datalist[i].money_type == "Expense":
            if start_date <= datalist[i].date <= end_date:
                week_expenses.append(datalist[i])

    if len(week_expenses) == 0:
        await update.message.reply_text(f"You dont have any expense for a week...")
        return

    for i, j in enumerate(week_expenses):
        result_expense += ''.join(f"{i + 1}. {j}") + "\n"

    await update.message.reply_text(f"Expenses for the month:\n{result_expense}")


async def statistics_categ_per_something(update: Update, context: CallbackContext) -> None:
    logging.info("Command statistics_categ_per_something was triggered")
    user_id = update.message.from_user.id
    period = update.message.text.split()[1]
    today = datetime.now().date()
    end_date = today
    datalist = user_data[user_id] #list []
    category_transactions = []
    result_string = ''

    if not user_data.get(user_id):
        await update.message.reply_text(f"U dont have any income/expense...")
        return

    if period != "week" and period != "day" and period != "month" and period != "year":
        await update.message.reply_text(f"U enter invalid value.\n"
                                        f"Use 'week', 'day', 'month', 'year'.")
        return

    match period:
        case "day":
            start_date = today
        case "week":
            start_date = today - timedelta(days=today.weekday())
        case "month":
            start_date = today.replace(day=1)
        case "year":
            start_date = today.replace(month=1, day=1)
        case _:
            print("Something goes wrong...")
            return

    for i in range(len(datalist)):
        if start_date <= datalist[i].date <= end_date:
            category_transactions.append(datalist[i])
    if len(category_transactions) == 0:
        await update.message.reply_text(f"You have no expense on {period}")
        return

    for i in range(len(CATEGORIES)):
        category = CATEGORIES[i]
        time_string = ''
        for j in range(len(category_transactions)):
            if category_transactions[j].categories.lower() == category:
                if category_transactions[j].money_type == "Income":
                    time_string += f"\t⬆️{category_transactions[j].date}" \
                                   f" {category_transactions[j].title} {category_transactions[j].value}\n"
                else:
                    time_string += f"\t⬇️{category_transactions[j].date}" \
                                   f" {category_transactions[j].title} {category_transactions[j].value}\n"
        if time_string != '':
            result_string += f"{category[0].upper()+category[1:]}:\n{time_string}"

    await update.message.reply_text(result_string)


async def start(update: Update, context: CallbackContext) -> None:
    logging.info("Command start was triggered")
    sticker = open("sticker.webp", "rb")
    await update.message.reply_text(f"<b>Hi, {update.message.from_user.first_name}👋.</b>\nI`m FinancialStatisticBot,"
                                    f"with me you can keep all income and expenditure statistics.\n"
                                    f"Use <code>/help</code> for command list.", parse_mode='HTML')
    await update.message.reply_sticker(sticker)


async def helper(update: Update, context: CallbackContext) -> None:
    logging.info("Command helper was triggered")
    await update.message.reply_text(f"<b>Functionality list:</b>\n"
                                    f"<code>/start</code> - Greetings\n"
                                    f"<code>/help</code> - List of commands\n"
                                    f"<code>/clear</code> - Clear all your data\n"
                                    f"<code>/remove [index]</code> - Remove one income/expense by "
                                    f"index(like <code>/remove 1</code>)\n"
                                    f"<code>/categories</code> - List of categories\n"
                                    f"<code>/addincome [Categories] [Title] [Value] [Date]</code> - Add your income, "
                                    f"[date] is optional\n"
                                    f"<code>/addexpense [Categories] [Title] [Value] [Date]</code> - Add your expense, "
                                    f"[date] is optional\n"
                                    f"<code>/moneylist</code> - List of all your incomes/expenses sorted by date\n"
                                    f"<code>/allstatistics</code> - Graph and List of all your "
                                    f"incomes/expenses sorted by date\n"
                                    f"<code>/statcatper [day/week/month/year]</code> - List of your "
                                    f"incomes/expenses per some period\n"
                                    f"<code>/expweek</code> - Your expense for week\n"
                                    f"<code>/expmonth</code> - Your expense for month\n", parse_mode='HTML')


async def categories_list(update: Update, context: CallbackContext) -> None:
    string_of_categories = "\n - ".join(CATEGORIES)
    await update.message.reply_text(f'List of Categories:\n - {string_of_categories}')


def run():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", helper))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("remove", remove_money))
    app.add_handler(CommandHandler("categories", categories_list))
    app.add_handler(CommandHandler("addincome", add_income))
    app.add_handler(CommandHandler("addexpense", add_expense))
    app.add_handler(CommandHandler("moneylist", money_list))
    app.add_handler(CommandHandler("allstatistics", all_time_statistics))
    app.add_handler(CommandHandler("statcatper", statistics_categ_per_something))
    app.add_handler(CommandHandler("expweek", expense_per_week))
    app.add_handler(CommandHandler("expmonth", expense_per_month))

    app.run_polling()


if __name__ == "__main__":
    load_data()
    print(user_data)
    run()

