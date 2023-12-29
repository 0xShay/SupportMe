import json, sqlite3, time, jwt, random, re
from flask import Flask, redirect, url_for, request, send_from_directory, render_template

JWT_SECRET_KEY = "".join([random.choice(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F"]) for i in range(64)])


### start of global constants ###

ACCOUNT_TYPE_CUSTOMER = 1
ACCOUNT_TYPE_ASSISTANT = 2

TICKET_STATUS_OPEN = 1
TICKET_STATUS_CLOSED = 2

SYSTEM_USER_ID = 0

### end of global constants ###


App = Flask(
    __name__,
    static_url_path='', 
    static_folder='static',
    template_folder='templates'
)


### start of server-side methods ###

def create_user(username, email, password):

    with sqlite3.connect("data.db") as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM User WHERE username = ?", [ username ])
        if len(cursor.fetchall()) != 0:
            return (False, "That username is already taken.")

        cursor.execute("SELECT * FROM User WHERE email = ?", [ email ])
        if len(cursor.fetchall()) != 0:
            return (False, "A user is already registered with that email address.")

        cursor.execute(
            "INSERT INTO User (username, password, createdAt, accountType, profileIcon, email) VALUES (?, ?, ?, ?, ?, ?)",
            [ username, password, int(time.time()), ACCOUNT_TYPE_CUSTOMER, f"/profile-icons/{random.choice(['blue', 'green', 'purple', 'red'])}.png", email ]
        )

        user_id = cursor.lastrowid
        return (True, user_id)

def login_user(username, password):

    with sqlite3.connect("data.db") as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT userID, password, accountType FROM User WHERE username = ?", [ username ])
        user_list = cursor.fetchall()
        if len(user_list) == 0:
            return (False, "A user with the supplied username and password was not found.")
        
        _user_id, _password, _account_type = user_list[0]

        if password == _password:
            access_token = generate_access_token(_user_id, _account_type)
            return (True, access_token)
        else:
            return (False, "A user with the supplied username and password was not found.")

def get_profile(user_id):
    
    with sqlite3.connect("data.db") as connection:

        cursor = connection.cursor()

        cursor.execute("SELECT username, createdAt, accountType, profileIcon FROM User WHERE userID = ?", [ user_id ])
        user_list = cursor.fetchall()
        if len(user_list) == 0:
            return None

        _username, _created_at, _account_type, _profile_icon = user_list[0]

        return {
            "user_id": user_id,
            "username": _username,
            "created_at": _created_at,
            "account_type": _account_type,
            "profile_icon": _profile_icon
        }

def generate_access_token(user_id, account_type):
    access_token = jwt.encode({
        "user_id": user_id,
        "account_type": account_type,
        "exp": int(time.time()) + 86400
    }, JWT_SECRET_KEY, algorithm="HS256")
    return access_token

def verify_access_token(access_token):
    try:
        d_at = jwt.decode(access_token.split(" ")[1], JWT_SECRET_KEY, algorithms=["HS256"])
        if d_at["exp"] < time.time():
            return None
        else:
            return d_at
    except:
        return None

def is_valid_username(username):
    if not username.isalnum():
        return False, "Username can only contain alphanumeric characters."
    elif len(username) > 16:
        return False, "Username cannot be more than 16 characters."
    return True, True

def is_valid_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    elif len(password) > 32:
        return False, "Password cannot be more than 32 characters."
    return True, True

def is_valid_email(email):
    if re.search('^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,63}$', email):
        return True, True
    else:
        return False, "The provided email was invalid."

def is_valid_profile_icon(profile_icon):
    if profile_icon not in [ f"/profile-icons/{c}.png" for c in ["blue", "green", "purple", "red"] ]:
        return False, "Profile icon is invalid."
    return True, True

def is_valid_ticket_title(ticket_title):
    if not all(x.isalnum() or x.isspace() for x in ticket_title):
        return False, "Ticket title can only contain spaces and alphanumeric characters."
    elif len(ticket_title) < 8:
        return False, "Ticket title must be at least 8 characters - be descriptive."
    elif len(ticket_title) > 64:
        return False, "Ticket title cannot be more than 64 characters - keep it concise."
    return True, True

def is_valid_message(message):
    if len(message) < 8 and not message.startswith("!"):
        return False, "Message length must be at least 8 characters - be descriptive."
    elif len(message) > 512:
        return False, "Message length cannot be more than 512 characters."
    return True, True

### end of server-side methods ###


### start of flask endpoints ###

@App.route('/', methods=['GET'])
@App.route('/home', methods=['GET'])
def home_req():
    if request.method == 'GET':        
        return (render_template('home.html'), 200)

@App.route('/register', methods=['GET', 'POST'])
def register_req():
    
    if request.method == 'GET':
        
        return (render_template('register.html'), 200)
    
    elif request.method == 'POST':

        try:
    
            registration_data = json.loads(request.get_data())
            
            if list(registration_data.keys()) != ["username", "email", "password"]:
                return ({ "error": "The request failed." }, 400)
            
            if "" in list(registration_data.values()):
                return ({ "error": "Please don't leave any blank fields." }, 400)
            
            _valid_username = is_valid_username(registration_data["username"])
            if not _valid_username[0]:
                return ({ "error": _valid_username[1] }, 400)

            _valid_password = is_valid_password(registration_data["password"])
            if not _valid_password[0]:
                return ({ "error": _valid_password[1] }, 400)
            
            _valid_email = is_valid_email(registration_data["email"])
            if not _valid_email[0]:
                return ({ "error": _valid_email[1] }, 400)

            cu_success, cu_res = create_user(registration_data["username"], registration_data["email"], registration_data["password"])
            if cu_success:
                return ({ "access_token": generate_access_token(cu_res, ACCOUNT_TYPE_CUSTOMER) }, 200)
            else:
                return ({ "error": cu_res }, 400)

        except:
            return ({ "error": "Server failed to parse the request." }, 400)

@App.route('/login', methods=['GET', 'POST'])
def login_req():
    
    if request.method == 'GET':
        return (render_template('login.html'), 200)
    
    elif request.method == 'POST':
    
        try:

            login_data = json.loads(request.get_data())
            
            if list(login_data.keys()) != ["username", "password"]:
                return ({ "error": "The request failed." }, 400)
            
            if "" in list(login_data.values()):
                return ({ "error": "Please don't leave any blank fields." }, 400)
            
            lu_success, lu_res = login_user(login_data["username"], login_data["password"])
            if lu_success:
                return ({ "access_token": lu_res }, 200)
            else:
                return ({ "error": lu_res }, 400)
        
        except:
            return ({ "error": "Server failed to parse the request." }, 400)

@App.route('/get-profile/<int:user_id>', methods=['GET'])
def get_profile_by_user_id_req(user_id):
    if request.method == 'GET':
        
        auth_user = verify_access_token(request.headers.get("Authorization"))
        if auth_user == None:
            return ({ "error": "User is not authenticated to make this request." }, 403)
        
        with sqlite3.connect("data.db") as connection:

            cursor = connection.cursor()

            cursor.execute("SELECT username, createdAt, accountType, profileIcon FROM User WHERE userID = ?", [ user_id ])
            user_list = cursor.fetchall()
            if len(user_list) == 0:
                return ({ "error": "User not found." }, 400)

            _username, _created_at, _account_type, _profile_icon = user_list[0]

            return ({ "user": {
                "user_id": user_id,
                "username": _username,
                "created_at": _created_at,
                "account_type": _account_type,
                "profile_icon": _profile_icon
            } }, 200)

@App.route('/ticket/new', methods=['GET', 'POST'])
def create_ticket_req():
    if request.method == 'GET':        
        return (render_template('ticket/new.html'), 200)
    
    elif request.method == 'POST':

        try:

            auth_user = verify_access_token(request.headers.get("Authorization"))
            if auth_user == None or auth_user["account_type"] != ACCOUNT_TYPE_CUSTOMER:
                return ({ "error": "User is not authenticated to make this request." }, 403)

            ticket_data = json.loads(request.get_data())
            
            if list(ticket_data.keys()) != ["ticket_title", "message"]:
                return ({ "error": "The request failed." }, 400)
            
            if "" in list(ticket_data.values()):
                return ({ "error": "Please don't leave any blank fields." }, 400)
            
            _valid_ticket_title = is_valid_ticket_title(ticket_data["ticket_title"])
            if not _valid_ticket_title[0]:
                return ({ "error": _valid_ticket_title[1] }, 400)

            _valid_message = is_valid_message(ticket_data["message"])
            if not _valid_message[0]:
                return ({ "error": _valid_message[1] }, 400)
            
            with sqlite3.connect("data.db") as connection:
                
                cursor = connection.cursor()
                
                cursor.execute("INSERT INTO Ticket (customerID, assistantID, openedAt, closedAt, title) VALUES (?, ?, ?, ?, ?);", [ auth_user["user_id"], -1, int(time.time()), -1, ticket_data["ticket_title"] ])
                ticket_id = cursor.lastrowid

                cursor.execute("INSERT INTO Message (ticketID, authorID, body, sentAt) VALUES (?, ?, ?, ?);", [ ticket_id, auth_user["user_id"], ticket_data["message"], int(time.time()) ])
                message_id = cursor.lastrowid

                return ({
                    "ticket_id": ticket_id,
                    "message_id": message_id
                }, 200)
        
        except:
            return ({ "error": "Server failed to parse the request." }, 400)

@App.route('/get-ticket/<int:ticket_id>', methods=['GET'])
def ticket_json_by_id_req(ticket_id):
    if request.method == 'GET':

        auth_user = verify_access_token(request.headers.get("Authorization"))
        if auth_user == None:
            return ({ "error": "User is not authenticated to make this request." }, 403)

        with sqlite3.connect("data.db") as connection:
        
            cursor = connection.cursor()
            
            cursor.execute("SELECT customerID, assistantID, openedAt, closedAt, title FROM Ticket WHERE ticketID = ?;", [ ticket_id ])

            ticket_list = cursor.fetchall()
            if len(ticket_list) == 0:
                return ({ "error": "Ticket with given ID was not found in the database." }, 404)

            _customer_id, _assistant_id, _opened_at, _closed_at, _title = ticket_list[0]
            
            if auth_user["user_id"] not in [_customer_id] and auth_user["account_type"] != ACCOUNT_TYPE_ASSISTANT:
                return ({ "error": "User is not authenticated to make this request." }, 403)

            return ({
                "ticket_data": {
                    "ticket_id": ticket_id,
                    "customer_id": _customer_id,
                    "assistant_id": _assistant_id,
                    "opened_at": _opened_at,
                    "closed_at": _closed_at,
                    "title": _title
                }
            }, 200)

@App.route('/ticket/<int:ticket_id>', methods=['GET', 'POST'])
def ticket_by_id_req(ticket_id):
    if request.method == 'GET':
        return (render_template('ticket/ticket.html', ticket_id=ticket_id), 200)
    
    elif request.method == 'POST':

        try:

            auth_user = verify_access_token(request.headers.get("Authorization"))
            if auth_user == None:
                return ({ "error": "User is not authenticated to make this request." }, 403)

            message_data = json.loads(request.get_data())
            
            if list(message_data.keys()) != ["message"]:
                return ({ "error": "The request failed." }, 400)
            
            if "" in list(message_data.values()):
                return ({ "error": "Please don't leave any blank fields." }, 400)

            _valid_message = is_valid_message(message_data["message"])
            if not _valid_message[0]:
                return ({ "error": _valid_message[1] }, 400)
            
            with sqlite3.connect("data.db") as connection:
                
                cursor = connection.cursor()
                
                cursor.execute("SELECT customerID, assistantID, closedAt FROM Ticket WHERE ticketID = ?;", [ ticket_id ])

                ticket_list = cursor.fetchall()
                if len(ticket_list) == 0:
                    return ({ "error": "Ticket with given ID was not found in the database." }, 404)

                _customer_id, _assistant_id, _closed_at = ticket_list[0]
                
                if auth_user["user_id"] not in [_customer_id] and auth_user["account_type"] != ACCOUNT_TYPE_ASSISTANT:
                    return ({ "error": "User is not authenticated to make this request." }, 403)
                
                user_profile = get_profile(auth_user["user_id"])
                if message_data["message"] == "!close":
                    cursor.execute("UPDATE Ticket SET closedAt = ? WHERE (ticketID = ?);", [ int(time.time()), ticket_id ])
                    cursor.execute("INSERT INTO Message (ticketID, authorID, body, sentAt) VALUES (?, ?, ?, ?);", [ ticket_id, SYSTEM_USER_ID, f"This ticket has been closed by {user_profile['username']} (ID: {auth_user['user_id']}).", int(time.time()) ])
                elif message_data["message"] == "!open":
                    cursor.execute("UPDATE Ticket SET closedAt = -1 WHERE (ticketID = ?);", [ ticket_id ])
                    cursor.execute("INSERT INTO Message (ticketID, authorID, body, sentAt) VALUES (?, ?, ?, ?);", [ ticket_id, SYSTEM_USER_ID, f"This ticket has been reopened by {user_profile['username']} (ID: {auth_user['user_id']}).", int(time.time()) ])
                elif message_data["message"] == "!claim" and auth_user["account_type"] == ACCOUNT_TYPE_ASSISTANT:
                    cursor.execute("UPDATE Ticket SET assistantID = ?, closedAt = ? WHERE (ticketID = ?);", [ auth_user["user_id"], -1, ticket_id ])
                    if _closed_at != -1:
                        cursor.execute("INSERT INTO Message (ticketID, authorID, body, sentAt) VALUES (?, ?, ?, ?);", [ ticket_id, SYSTEM_USER_ID, f"This ticket has been claimed and reopened by {user_profile['username']} (ID: {auth_user['user_id']}).", int(time.time()) ])
                    else:
                        cursor.execute("INSERT INTO Message (ticketID, authorID, body, sentAt) VALUES (?, ?, ?, ?);", [ ticket_id, SYSTEM_USER_ID, f"This ticket has been claimed by {user_profile['username']} (ID: {auth_user['user_id']}).", int(time.time()) ])
                else:
                    if _closed_at != -1:
                        cursor.execute("INSERT INTO Message (ticketID, authorID, body, sentAt) VALUES (?, ?, ?, ?);", [ ticket_id, SYSTEM_USER_ID, f"This ticket has been reopened by {user_profile['username']} (ID: {auth_user['user_id']}).", int(time.time())-1 ])
                        cursor.execute("UPDATE Ticket SET closedAt = ? WHERE (ticketID = ?);", [ -1, ticket_id ])
                    cursor.execute("INSERT INTO Message (ticketID, authorID, body, sentAt) VALUES (?, ?, ?, ?);", [ ticket_id, auth_user["user_id"], message_data["message"], int(time.time())+1 ])
                
                message_id = cursor.lastrowid

                return ({
                    "ticket_id": ticket_id,
                    "message_id": message_id
                }, 200)

        except:
            return ({ "error": "Server failed to parse the request." }, 400)

@App.route('/get-open-tickets/<int:user_id>', methods=['GET'])
def get_open_tickets_by_user_id_req(user_id):
    if request.method == 'GET':

        auth_user = verify_access_token(request.headers.get("Authorization"))
        if auth_user == None or auth_user["user_id"] != user_id:
            return ({ "error": "User is not authenticated to make this request." }, 403)

        with sqlite3.connect("data.db") as connection:

            cursor = connection.cursor()

            cursor.execute("SELECT * FROM User WHERE userID = ?;", [ user_id ])

            if len(cursor.fetchall()) == 0:
                return ({ "error": "User with given ID was not found in the database." }, 404)

            cursor.execute("SELECT ticketID, customerID, assistantID, openedAt, closedAt, title FROM Ticket WHERE (customerID = ? OR assistantID = ?) AND closedAt = -1 ORDER BY openedAt ASC;", [ user_id, user_id ])
            ticket_list = cursor.fetchall()

            response = []

            for t in ticket_list:
                _ticket_id, _customer_id, _assistant_id, _opened_at, _closed_at, _title = t
                response.append({
                    "ticket_id": _ticket_id,
                    "customer_id": _customer_id,
                    "assistant_id": _assistant_id,
                    "opened_at": _opened_at,
                    "closed_at": _closed_at,
                    "title": _title
                })

            return ({
                "tickets": response
            }, 200)

@App.route('/get-closed-tickets/<int:user_id>', methods=['GET'])
def get_closed_tickets_by_user_id_req(user_id):
    if request.method == 'GET':

        auth_user = verify_access_token(request.headers.get("Authorization"))
        if auth_user == None or auth_user["user_id"] != user_id:
            return ({ "error": "User is not authenticated to make this request." }, 403)

        with sqlite3.connect("data.db") as connection:

            cursor = connection.cursor()

            cursor.execute("SELECT * FROM User WHERE userID = ?;", [ user_id ])

            if len(cursor.fetchall()) == 0:
                return ({ "error": "User with given ID was not found in the database." }, 404)

            cursor.execute("SELECT ticketID, customerID, assistantID, openedAt, closedAt, title FROM Ticket WHERE (customerID = ? OR assistantID = ?) AND closedAt != -1 ORDER BY closedAt DESC;", [ user_id, user_id ])
            ticket_list = cursor.fetchall()

            response = []

            for t in ticket_list:
                _ticket_id, _customer_id, _assistant_id, _opened_at, _closed_at, _title = t
                response.append({
                    "ticket_id": _ticket_id,
                    "customer_id": _customer_id,
                    "assistant_id": _assistant_id,
                    "opened_at": _opened_at,
                    "closed_at": _closed_at,
                    "title": _title
                })

            return ({
                "tickets": response
            }, 200)

@App.route('/get-unclaimed-tickets', methods=['GET'])
def get_unclaimed_tickets_req():
    if request.method == 'GET':

        auth_user = verify_access_token(request.headers.get("Authorization"))
        if auth_user == None or auth_user["account_type"] != ACCOUNT_TYPE_ASSISTANT:
            return ({ "error": "User is not authenticated to make this request." }, 403)

        with sqlite3.connect("data.db") as connection:

            cursor = connection.cursor()

            cursor.execute("SELECT ticketID, customerID, assistantID, openedAt, closedAt, title FROM Ticket WHERE assistantID = -1 ORDER BY openedAt ASC;")
            ticket_list = cursor.fetchall()

            response = []

            for t in ticket_list:
                _ticket_id, _customer_id, _assistant_id, _opened_at, _closed_at, _title = t
                response.append({
                    "ticket_id": _ticket_id,
                    "customer_id": _customer_id,
                    "assistant_id": _assistant_id,
                    "opened_at": _opened_at,
                    "closed_at": _closed_at,
                    "title": _title
                })

            return ({
                "tickets": response
            }, 200)

@App.route('/get-messages/<int:ticket_id>', methods=['GET'])
def get_messages_by_ticket_id_req(ticket_id):
    if request.method == 'GET':

        auth_user = verify_access_token(request.headers.get("Authorization"))
        if auth_user == None:
            return ({ "error": "User is not authenticated to make this request." }, 403)

        with sqlite3.connect("data.db") as connection:
            
            cursor = connection.cursor()
            
            cursor.execute("SELECT customerID, assistantID FROM Ticket WHERE ticketID = ?;", [ ticket_id ])

            ticket_list = cursor.fetchall()
            if len(ticket_list) == 0:
                return ({ "error": "Ticket with given ID was not found in the database." }, 404)

            _customer_id, _assistant_id = ticket_list[0]

            if auth_user["user_id"] not in [_customer_id] and auth_user["account_type"] != ACCOUNT_TYPE_ASSISTANT:
                return ({ "error": "User is not authenticated to make this request." }, 403)
            
            cursor.execute("SELECT messageID, authorID, body, sentAt FROM Message WHERE ticketID = ? ORDER BY sentAt DESC;", [ ticket_id ])
            message_list = cursor.fetchall()

            response = []

            for m in message_list:
                _message_id, _author_id, _body, _sent_at = m
                response.append({
                    "message_id": _message_id,
                    "author_id": _author_id,
                    "body": _body,
                    "sent_at": _sent_at
                })

            return ({
                "ticket_id": ticket_id,
                "message_list": response
            }, 200)

@App.route('/profile', methods=['GET', 'POST'])
def profile_req():
    if request.method == 'GET':
        return (render_template('profile.html'), 200)
    
    elif request.method == 'POST':

        try:

            auth_user = verify_access_token(request.headers.get("Authorization"))
            if auth_user == None:
                return ({ "error": "User is not authenticated to make this request." }, 403)

            profile_data = json.loads(request.get_data())
            
            if list(profile_data.keys()) != ["new_password", "old_password", "profile_icon"]:
                return ({ "error": "The request failed." }, 400)
            
            if profile_data["new_password"] == "":
                profile_data["new_password"] = profile_data["old_password"]

            if "" in list(profile_data.values()):
                return ({ "error": "Please don't leave any blank fields." }, 400)

            with sqlite3.connect("data.db") as connection:
            
                cursor = connection.cursor()
                
                cursor.execute("SELECT password FROM User WHERE userID = ?;", [ auth_user["user_id"] ])

                user_list = cursor.fetchall()
                if len(user_list) == 0:
                    return ({ "error": "User with given ID was not found in the database." }, 404)

                if user_list[0][0] != profile_data["old_password"]:
                    return ({ "error": "Incorrect password was provided." }, 403)

                _valid_password = is_valid_password(profile_data["new_password"])
                if not _valid_password[0]:
                    return ({ "error": _valid_password[1] }, 400)

                _valid_profile_icon = is_valid_profile_icon(profile_data["profile_icon"])
                if not _valid_profile_icon[0]:
                    return ({ "error": _valid_profile_icon[1] }, 400)

                cursor.execute("UPDATE User SET password = ?, profileIcon = ? WHERE (userID = ?)", [ profile_data["new_password"], profile_data["profile_icon"], auth_user["user_id"] ])

                return ({ "msg": "Profile has been updated." }, 200)

        except:
            return ({ "error": "Server failed to parse the request." }, 400)

### end of flask endpoints ###

if __name__ == "__main__":
    App.run(host="0.0.0.0")