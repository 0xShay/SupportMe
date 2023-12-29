import sqlite3

user_id = int(input("Enter the user ID of the account: "))
account_type = int(input("Enter an account type to set (1 = customer, 2 = assistant): "))

with sqlite3.connect("../data.db") as connection:
    
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE User SET accountType = ? WHERE userID = ?;", [ account_type, user_id ])
        if cursor.rowcount == 0:
            print("User with given ID was not found in the database. Terminating.")
        else:
            print(f"User with ID {user_id}'s account type has been successfully updated to {account_type}.")

    except sqlite3.Error as error:
        print(error)