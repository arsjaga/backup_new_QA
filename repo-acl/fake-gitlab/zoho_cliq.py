import json
import os
import atexit
import sys


DB_PATH = os.getenv("FAKE_ZOHO_DB_PATH")
if not DB_PATH:
    print("fake-gitlab: set FAKE_ZOHO_DB_PATH")
    sys.exit(1)

with open(DB_PATH, encoding="utf-8") as file:
    DB = json.load(file)

@atexit.register
def save_db():
    with open(DB_PATH, "w", encoding="utf-8") as file:
        json.dump(DB, file, indent=4)


class User:
    def __init__(self, user):
        self.data = user
        self.email_id = user["email_id"]


class Users:
    def __init__(self):
        self.data = DB.get("users", [])

    def get(self, email):
        for user in self.data:
            if user["email_id"].lower() == email.lower():
                return User(user)

        raise Exception("User not found")

    def list(self):
        return [User(user) for user in self.data]


class Channel:
    def __init__(self, channel):
        self.data = channel
        self.channel_id = channel["channel_id"]
        self.name = channel["name"]
        self.members = channel.setdefault("members", [])

    def add_member(self, email):
        if not any(
            member["email_id"].lower() == email.lower()
            for member in self.members
        ):
            self.members.append({"email_id": email})

    def remove_member(self, email):
        self.members[:] = [
            member
            for member in self.members
            if member["email_id"].lower() != email.lower()
        ]

    def get_members(self):
        return self.members


class Channels:
    def __init__(self):
        self.data = DB.get("channels", [])

    def get(self, channel_id):
        for channel in self.data:
            if str(channel["channel_id"]) == str(channel_id):
                return Channel(channel)

        raise Exception("Channel not found")

    def get_by_name(self, name):
        for channel in self.data:
            if channel["name"].lstrip("#").lower() == name.lower():
                return Channel(channel)

        raise Exception("Channel not found")

    def list(self):
        return [Channel(channel) for channel in self.data]


class Zoho:
    def __init__(self):
        self.users = Users()
        self.channels = Channels()


if __name__ == "__main__":
    zoho = Zoho()

    # print("Users:")
    # for user in zoho.users.list():
    #     print(user.email_id)

    # print("\nChannels:")
    # for channel in zoho.channels.list():
    #     print(channel.name)