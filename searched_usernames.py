import json
import os
import fcntl
import threading
from datetime import datetime

class SearchedUsernameManager:
    def __init__(self):
        self.data_file = 'searched_usernames.json'
        self._lock = threading.Lock()
        self.init_database()

    def init_database(self):
        if not os.path.exists(self.data_file):
            default_data = {"searched_usernames": []}
            self.save_data(default_data)

    def load_data(self):
        try:
            with self._lock:
                with open(self.data_file, 'r') as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                    try:
                        data = json.load(f)
                        if 'searched_usernames' not in data:
                            data['searched_usernames'] = []
                        return data
                    finally:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except (FileNotFoundError, json.JSONDecodeError):
            self.init_database()
            return {"searched_usernames": []}

    def save_data(self, data):
        with self._lock:
            with open(self.data_file, 'w') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(data, f, indent=2)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def add_searched_username(self, username, user_hash):
        data = self.load_data()
        if any(item['username'].lower() == username.lower() for item in data['searched_usernames']):
            return
        new_id = max([item['id'] for item in data['searched_usernames']], default=0) + 1
        new_entry = {
            "id": new_id,
            "username": username,
            "searched_by": user_hash,
            "searched_at": datetime.now().isoformat(),
            "status": "not_found"
        }
        data['searched_usernames'].append(new_entry)
        self.save_data(data)

    def get_searched_usernames(self):
        data = self.load_data()
        for u in data['searched_usernames']:
            if 'mobile_number' not in u:
                u['mobile_number'] = 'Not Available'
        return data['searched_usernames']

    def delete_searched_username(self, username_id):
        data = self.load_data()
        data['searched_usernames'] = [u for u in data['searched_usernames'] if u['id'] != int(username_id)]
        self.save_data(data)

# Global instance
searched_username_manager = SearchedUsernameManager()
