from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from pymongo import MongoClient
from datetime import datetime

# --- MongoDB Setup ---
cluster = MongoClient(
    'mongodb+srv://ranjith:ranjith@crud.4cw9f.mongodb.net/?retryWrites=true&w=majority&appName=crud'
)
db = cluster['whatsapp_bot']
users = db['users']
orders = db['orders']

# --- Flask App ---
app = Flask(__name__)

# --- Helper Functions ---
def log_message(number, text):
    """Store incoming user messages in MongoDB"""
    users.update_one(
        {'number': number},
        {"$push": {"messages": {"text": text, "date": datetime.now()}}},
        upsert=True
    )

def send_main_menu(response):
    """Send main menu options to user"""
    response.message(
        "Hi, thanks for contacting *Ranjith*.\n"
        "You can choose from one of the options below: \n\n"
        "*Type*\n\n"
        "1️⃣ To *contact* us \n"
        "2️⃣ To *order* snacks \n"
        "3️⃣ To know our *working hours* \n"
        "4️⃣ To get our *address*"
    )

def handle_user_choice(text, response, number):
    """Handle user input and provide responses"""
    if text == "1":
        response.message("📞 You can reach us at: *+91 95855 92233* or email *support@ranjith.com*")
    elif text == "2":
        response.message("🍔 Please type the snack name to order.\nExample: *Samosa* or *Cake*")
        users.update_one({'number': number}, {"$set": {"status": "ordering"}})
    elif text == "3":
        response.message("🕑 Our working hours are:\nMon - Sat: *9 AM - 9 PM*\nSunday: *Closed*")
    elif text == "4":
        response.message("📍 Our address is:\n*3/845A, Indra street, Ottappalam, Paramakudi,PARAMAKUDI, TAMIL NADU 623707*")
    else:
        response.message("❌ Invalid option. Please try again.")
        send_main_menu(response)

# --- Flask Route ---
@app.route("/", methods=['GET', 'POST'])
def reply():
    text = request.values.get('Body', '').strip()
    number = request.values.get('From', '')
    response = MessagingResponse()

    user = users.find_one({'number': number})

    if not user:  # new user
        users.insert_one({'number': number, "status": "main", "messages": []})
        send_main_menu(response)
    else:
        log_message(number, text)
        status = user.get("status", "main")

        if status == "main":
            handle_user_choice(text, response, number)

        elif status == "ordering":
            response.message(f"✅ Order placed for *{text}*.\nWe will contact you shortly!")
            orders.insert_one({"number": number, "item": text, "date": datetime.now()})
            users.update_one({'number': number}, {"$set": {"status": "main"}})
            send_main_menu(response)

    return str(response)

# --- Run App ---
if __name__ == "__main__":
    app.run(port=5000, debug=True)
