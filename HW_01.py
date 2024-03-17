from datetime import datetime
from datetime import timedelta
from collections import UserDict
import pickle
from abc import ABC, abstractmethod
from tabulate import tabulate

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено

class Field: # Базовий клас для полів запису.
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field): #Клас для зберігання імені контакту. Обов'язкове поле.
    def __init__(self, name):
        if not name:
            raise ValueError("Please enter your name")
        super().__init__(name)

class Phone(Field): #Клас для зберігання номера телефону. Має валідацію формату (10 цифр).
    def __init__(self, phone):
      if len(phone) !=10 or not phone.isdigit():
        raise ValueError ("Number must have 10 digits.")
      super().__init__(phone)

class Birthday(Field):
    def __init__(self, value):
        try:
            datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(datetime.strptime(value, '%d.%m.%Y'))

class Record: # Клас для зберігання інформації про контакт, включаючи ім'я та список телефонів.
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        for ph in self.phones:
            if ph.value == phone:
                self.phones.remove(ph)

    def edit_phone(self, old_phone, new_phone):
        for phone in self.phones:
            if phone.value == old_phone:
                phone.value = new_phone
                break

    def find_phone(self, phone):
      for ph in self.phones:
          if ph.value == phone:
            return ph
      return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        birthday_str = self.birthday.value.strftime("%d.%m.%Y") if self.birthday else 'Not specified'
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}, birthday: {birthday_str}"

def input_error(func):   # input_error декоратор для помилок
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            return "Give me name and phone please."
        except KeyError:
            return "No such name found"
        except IndexError:
            return "Not found"
        except Exception as e:
            return f"Error:{e}"

    return inner

class AddressBook(UserDict):  # Клас для зберігання та управління записами.

    @input_error
    def add_record(self, record):
        self.data[record.name.value] = record

    @input_error
    def find(self, name):
        return self.data.get(name)

    @input_error
    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        birthdays = []

        for record in self.data.values():
            if isinstance(record.birthday, Birthday):
                bday = record.birthday.value.date()
                bday_this_year = datetime(today.year, bday.month, bday.day).date()

                if 0 <= (bday_this_year - today).days < 7:
                    if datetime.weekday(bday_this_year) < 5:
                        birthdays.append({'name': record.name.value, 'birthday': datetime.strftime(bday_this_year, "%Y.%m.%d")})
                    else:
                        if datetime.weekday(bday_this_year) == 5:  # Saturday bday
                            bday_this_year = datetime(bday_this_year.year, bday_this_year.month, bday_this_year.day + 2).date()
                            birthdays.append({'name': record.name.value, 'birthday': datetime.strftime(bday_this_year, "%Y.%m.%d")})
                        elif datetime.weekday(bday_this_year) == 6:  # Sunday bday
                            bday_this_year = datetime(bday_this_year.year, bday_this_year.month, bday_this_year.day + 1).date()
                            birthdays.append({'name': record.name.value, 'birthday': datetime.strftime(bday_this_year, "%Y.%m.%d")})

        return birthdays

@input_error
def add_birthday(args, book):
    name, birthday = args
    try:
        record = book.find(name)
        if record:
            record.add_birthday(birthday)
            print(f"Birthday added for {name}.")
        else:
            print(f"Contact {name} not found.")
    except ValueError as e:
        print(e)

@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        print(f"{name}'s birthday: {record.birthday.value}")
    elif record and not record.birthday:
        print(f"{name} does not have a birthday specified.")
    else:
        print(f"Contact {name} not found.")

@input_error
def birthdays(args, book):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if upcoming_birthdays:
        print("Upcoming birthdays:")
        for record in upcoming_birthdays:
            name = record['name']
            birthday = record['birthday']
            print(f"The congratulation date for {name} is {birthday}")
    else:
        print("No upcoming birthdays.")

@input_error
def add_contact(args, book: AddressBook):
    name, phone = args

    record = book.find(name)
    if not record:
        record = Record(name)
        book.add_record(record)

    record.add_phone(phone)
    print("Контакт додано.")

def parse_input(user_input):
    return user_input.strip().lower().split()

class AbstractView(ABC):
    @abstractmethod
    def display_contacts(self, contacts):
        pass

    @abstractmethod
    def display_commands(self):
        pass

class ConsoleView(AbstractView):
    def display_contacts(self, contacts):
        print("Contacts:")
        for contact in contacts:
            print(contact)

    def display_commands(self):
        print("Available commands:")
        print("add - Add a new contact with name and phone number.")
        print("change - Change a contact's phone number.")
        print("phone - Show the phone number for a specified contact.")
        print("all - Show all contacts in the address book.")
        print("add-birthday - Add a birthday date for a specified contact.")
        print("show-birthday - Show the birthday date for a specified contact.")
        print("birthdays - Show upcoming birthdays.")
        print("exit - Close the application.")

class TableView(AbstractView):
    def display_contacts(self, contacts):
        data = []
        for contact in contacts:
            phones = '; '.join(str(phone) for phone in contact.phones)
            birthday_str = contact.birthday.value.strftime("%d.%m.%Y") if contact.birthday else 'Not specified'
            data.append([contact.name.value, phones, birthday_str])
        headers = ["Name", "Phones", "Birthday"]
        print(tabulate(data, headers=headers))
        
    def display_commands(self):
        menu = [
            ["add [name] [phone]", "Add new contact"],
            ["change [name] [new phone]", "Change contact phone"],
            ["phone [name]", "Show contact's phone"],
            ["all", "Show all contacts"],
            ["add-birthday [name] [birthday date]", "Add contact's birthday date"],
            ["show-birthday [name]", "Show contact's birthday date"],
            ["birthdays", "Show birthday dates on upcoming 7 days"],
            ["hello", "Show greeting"],
            ["close or exit", "Shut the bot"]
        ]
        print(tabulate(menu, headers=["Command", "Description"]))
        
def main(): # чат бот
    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Goodbye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add": # Додати новий контакт з іменем та телефонним номером.
            add_contact(args, book)
            
        elif command == "change":
            if len(args) != 3:
                print("Invalid number of arguments.")
                continue
            name, old_phone, new_phone = args
            record = book.find(name)
            if record:
                record.edit_phone(old_phone, new_phone)
                print("Контакт змінено")
            else:
                print("Контакт не знайдено")

        elif command == "phone":  #Показати телефонний номер для вказаного контакту.
            if len(args) != 1:
                print("Invalid number of arguments.")
                continue
            name = args[0]
            record = book.find(name)
            if record:
                if record.phones:
                    print(f"{name}: {'; '.join(str(phone) for phone in record.phones)}")
                else:
                    print(f"{name} has no phone numbers.")
            else:
                print(f"Контакт не знайдено.")

        elif command == "all":  #Показати всі контакти в адресній книзі.
            for record in book.data.values():
                print(record)

        elif command == "add-birthday":  # Додати дату народження для вказаного контакту.
            if len(args) != 2:
                print("Invalid number of arguments.")
                continue
            add_birthday(args, book)

        elif command == "show-birthday": # Показати дату народження для вказаного контакту.
            if len(args) != 1:
                print("Invalid number of arguments.")
                continue
            show_birthday(args, book)

        elif command == "birthdays":
            birthdays(args, book)

        else:
            print("Invalid command.")
    
    save_data(book)

    # Створення об'єкта класу ConsoleView
    console_view = ConsoleView()
    # Виклик методу display_commands
    console_view.display_commands()
    # Виклик методу display_contacts 
    console_view.display_contacts(contacts)

    # Створення об'єкта класу TableView
    table_view = TableView()
    # Виклик методу display_commands
    table_view.display_commands()
    # Виклик методу display_contacts 
    table_view.display_contacts(contacts)

if __name__ == "__main__":
    main()

