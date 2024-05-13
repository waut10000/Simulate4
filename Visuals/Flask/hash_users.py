import bcrypt
import json

# Sample user data with plaintext passwords
users = {
    "Admin": "****",
    "Steve": "****"
}

# Dictionary to hold hashed passwords
hashed_users = {}

for user, password in users.items():
    # Generate a salt and hash the password
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    hashed_users[user] = hashed.decode('utf-8')

# Save hashed passwords to a file
with open('hashed_users.json', 'w') as f:
    json.dump(hashed_users, f, indent=4)

print("Hashed passwords are saved to 'hashed_users.json'")
