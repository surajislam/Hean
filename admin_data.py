import json
import os
import fcntl
import threading
import random
import string
from datetime import datetime

class AdminDataManager:
    def __init__(self):
        self.data_file = 'admin_database.json'
        self._lock = threading.Lock()
        self.data = {}
        self.init_database()

    def generate_hash_code(self):
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choices(characters, k=12))

    def init_database(self):
        if not os.path.exists(self.data_file):
            admin_hash = "ADMIN9999RSX"
            default_data = {
                "users": [
                    {"id": 1, "name": "Admin User", "hash_code": admin_hash, "balance": 9999, "created_at": datetime.now().isoformat()},
                    {"id": 2, "name": "Special User", "hash_code": "SPECIAL9999X", "balance": 9999, "created_at": datetime.now().isoformat()}
                ],
                "demo_usernames": [],
                "valid_utrs": [],
                "custom_message": "You have just added balance, please wait for 2 minutes for search"
            }
            self.save_data(default_data)
            print(f"Admin hash code with ₹9999 balance: {admin_hash}")
        else:
            data = self.load_data()
            updated = False
            for key in ['users', 'demo_usernames', 'valid_utrs', 'custom_message']:
                if key not in data:
                    data[key] = [] if key != 'custom_message' else "You have just added balance, please wait for 2 minutes for search"
                    updated = True
            if updated:
                self.save_data(data)

    def load_data(self):
        try:
            with self._lock:
                with open(self.data_file, 'r') as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                    try:
                        self.data = json.load(f)
                        for key in ['users', 'demo_usernames', 'valid_utrs', 'custom_message']:
                            if key not in self.data:
                                self.data[key] = [] if key != 'custom_message' else "You have just added balance, please wait for 2 minutes for search"
                        return self.data
                    finally:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except (FileNotFoundError, json.JSONDecodeError):
            self.init_database()
            return self.data

    def save_data(self, data=None):
        if data is None:
            data = self.data
        else:
            self.data = data

        temp_file = self.data_file + '.tmp'
        with self._lock:
            with open(temp_file, 'w') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(data, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            os.replace(temp_file, self.data_file)

# Global admin instance
admin_db = AdminDataManager()
