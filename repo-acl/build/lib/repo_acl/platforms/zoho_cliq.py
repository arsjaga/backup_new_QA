import os
import csv
import requests
import sys
import logging

GROUPS_DIR  = os.getenv("REPO_ACL_GROUPS_DIR", "./groups")
DOMAIN_NAME = "gowtham.work.gd"

class ZohoCliqGroups:
    """
    Manage Zoho Cliq channel members using CSV-based synchronization.
    """

    def __init__(self, client_id, client_secret, refresh_token, dryrun):
        """
        Initialize Zoho Cliq API credentials and configuration.

        Args:
            client_id (str): Zoho OAuth client ID.
            client_secret (str): Zoho OAuth client secret.
            refresh_token (str): OAuth refresh token.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.dry_run = dryrun
        self.token_url = "https://accounts.zoho.in/oauth/v2/token"
        self.api_base = "https://cliq.zoho.in/api/v2"
        self.access_token = None

    def renew_access_token(self) -> None:
        """
        Generate a new Zoho OAuth access token using the refresh token.
        This token is required for all Zoho Cliq API calls.
        """
        if self.dry_run:
            print("[DRY-RUN] Would renew access token")
            self.access_token = "DRY_RUN_TOKEN"
            return

        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }

        r = requests.post(self.token_url, data=data)
        r.raise_for_status()
        self.access_token = r.json()["access_token"]

    def headers(self) -> dict:
        """
        Return HTTP headers required for Zoho Cliq API calls.
        Automatically refreshes the access token if needed.

        """
        if not self.access_token:
            self.renew_access_token()

        return {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json",
        }

    def read_groups(self) -> list[dict]:
        """
        Read CSV files and map each file to a channel and its users.
        Each CSV file represents one channel.

        Args:
            groups_dir (str): Directory containing CSV files.
        """
        groups = []

        for file in os.listdir(GROUPS_DIR):
            if file.endswith(".csv"):
                users = set()

                with open(os.path.join(GROUPS_DIR, file)) as f:
                    for row in csv.reader(f):
                        if row and row[0]:
                            users.add(row[0].strip().lower() + "@" + DOMAIN_NAME)

                groups.append({
                    "name": file.replace(".csv", ""),
                    "users": users
                })

        return groups
    
    def get_user_details_by_email(self, email) -> set:
        """
        Fetch details for a specific Zoho Cliq user by email and return their email ID.
        """

        if self.dry_run:
            print("[DRY-RUN] Would fetch all users")
            return set()

        url = f"{self.api_base}/users/{email}"
        r = requests.get(url, headers=self.headers())
        result = r.json()
        data = result.get("data", {})
        user_email = (data.get("email_id", "").strip().lower())

        if user_email == email.lower():
            return user_email

        return None

    def find_channel_id_by_name(self, channel_name: str):
        """
        Find and return a channel ID using the channel name.
        Returns None if the channel does not exist.

        Args:
            channel_name (str): Name of the Zoho Cliq channel.
        """
        if self.dry_run:
            print(f"[DRY-RUN] Would lookup channel: {channel_name}")
            return "DRY_RUN_CHANNEL_ID"

        url = f"{self.api_base}/channels"
        r = requests.get(url, headers=self.headers())
        r.raise_for_status()

        normalized_target = channel_name.strip().lower()

        for channel in r.json().get("channels", []):
            api_name = channel.get("name", "").lstrip("#").lower()

            if api_name == normalized_target:
                return channel.get("channel_id")

        return None

    def fetch_channel_member_emails(self, channel_id: str):
        """
        Fetch all member email IDs of a channel.
        Returns a set of lowercase email addresses.

        Args:
            channel_id (str): Zoho Cliq channel ID.
        """
        if self.dry_run:
            print(f"[DRY-RUN] Would fetch members for channel {channel_id}")
            return set()

        url = f"{self.api_base}/channels/{channel_id}/members"
        r = requests.get(url, headers=self.headers())
        r.raise_for_status()

        emails = set()

        for member in r.json().get("members", []):
            email = member.get("email_id")
            if email:
                emails.add(email.lower())

        return emails

    def add_users(self, channel_id: str, emails) -> None:
        """
        Add users to a channel using email IDs.
        Args:
            channel_id (str): Zoho Cliq channel ID.
            emails (set[str]): Email addresses to add.
        """
        if self.dry_run:
            print(f"[DRY-RUN] Would add {len(emails)} users to {channel_id}")
            return

        url = f"{self.api_base}/channels/{channel_id}/members"
        r = requests.post(url, headers=self.headers(), json={"email_ids": list(emails), "silent": False})

        if r.status_code in (200, 204):
            print(f"Added {emails}")
        else:
            print("Add failed:", r.text)

    def remove_users(self, channel_id: str, emails) -> None:
        """
        Remove users from a channel using email IDs.
        Args:
            channel_id (str): Zoho Cliq channel ID.
            emails (set[str]): Email addresses to remove.
        """
        if self.dry_run:
            print(f"[DRY-RUN] Would remove {len(emails)} users from {channel_id}")
            return

        if not emails:
            return

        url = f"{self.api_base}/channels/{channel_id}/members"
        r = requests.delete(url, headers=self.headers(), json={"email_ids": list(emails), "silent": False})

        if r.status_code in (200, 204):
            print(f"Removed {emails}")
        else:
            print("Remove failed:", r.text)

    def sync_members(self, channel_id: str, desired_users) -> None:
        """
        Sync channel members with the CSV-defined user list.
        Adds missing users and removes extra users.
        Args:
            channel_id (str): Zoho Cliq channel ID.
            desired_users (set[str]): Expected user email addresses.
        """

        current_users = self.fetch_channel_member_emails(channel_id)
        valid_users = set()
        invalid_users = set()
        for user in desired_users:
            user_details = self.get_user_details_by_email(user)

            if user_details:
                valid_users.add(user.lower())
                print(f"Valid user: {user}")
            else:
                invalid_users.add(user.lower())
                print(f"Invalid user: {user}")

        to_add = valid_users - current_users
        to_remove = current_users - desired_users

        if to_add:
            self.add_users(channel_id, to_add)

        self.remove_users(channel_id, to_remove)


    def sync_groups_from_csv(self) -> None:
        """
        Read all CSV files and synchronize members
        for each corresponding Zoho Cliq channel.
        """
        groups = self.read_groups()
        for group in groups:
            channel_id = self.find_channel_id_by_name(group["name"])
            if not channel_id:
                logging.error("Channel ID not found for group: %s", group['name'])
                sys.exit(1)

            self.sync_members(channel_id, group["users"])

def register(subparsers):
    parser = subparsers.add_parser(
        "zoho-cliq",
        help="Zoho Cliq operations"
    )

    parser.add_argument("--client-id", required=True)
    parser.add_argument("--client-secret", required=True)
    parser.add_argument("--refresh-token", required=True)
    parser.add_argument("--dry-run", action="store_true")

    parser.set_defaults(func=run)


def run(args):
    zc = ZohoCliqGroups(
        client_id=args.client_id,
        client_secret=args.client_secret,
        refresh_token=args.refresh_token,
        dryrun=args.dry_run
    )
    zc.sync_groups_from_csv()
