import os
import csv
import requests
import argparse
import re
import sys
import logging

GROUPS_DIR  = os.getenv("REPO_ACL_GROUPS_DIR", "./groups")
DOMAIN_NAME = "gowtham.work.gd"

class ZohoMailGroup:
    """
    Creates Zoho Mail groups and adds users using data from a CSV file.
    Attributes:
        url (str): Base URL for Zoho Mail API.
        group_data (list): List to hold group and user information.
        headers (dict): Headers for API requests, including authorization token.
    """

    def __init__(self, client_id, client_secret, refresh_token, dryrun):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.dry_run = dryrun
        self.url = "https://mail.zoho.in/api/organization/"
        self.group_data = None
        self.headers = {}

    def get_org_id(self):
        """
        Fetches the organization ID using the Zoho Mail API.
        Returns:
            str: The organization ID (zoid).
        Raises:
            Exception: If the API call fails or the organization ID is not found.
        """
        response = requests.get(
            f"https://mail.zoho.in/api/organization", headers=self.headers
        )
        data = response.json()

        if self.dry_run:
            print("[DRY-RUN] Would fetch organization ID")
            return "DRY_RUN_ORG_ID"

        if not response.ok:
            raise Exception(f"Failed to fetch organization ID: {data}")

        org_data = data.get("data", {})
        if not org_data:
            raise Exception("No organization data found.")

        org_id = org_data.get("zoid")
        if not org_id:
            raise Exception("Organization ID (zoid) not found.")

        return org_id

    def renew_access_token(self) -> None:
        """
        Renews the Zoho OAuth access token using the refresh token.
        Updates the headers attribute with the new access token for authorization.
        """
        token_url = f"https://accounts.zoho.in/oauth/v2/token?refresh_token={self.refresh_token}&grant_type=refresh_token&client_id={self.client_id}&client_secret={self.client_secret}"
        response = requests.post(token_url, timeout=10)
        data = response.json()

        if self.dry_run:
            print("[DRY-RUN] Would renew access token")
            self.headers = {
                "Authorization": "Zoho-oauthtoken DRY_RUN_TOKEN",
                "Content-Type": "application/json",
            }
            return

        if not response.ok:
            raise Exception(f"Token refresh failed ({response.status_code}): {data}")

        access_token = data.get("access_token")
        if not access_token:
            raise Exception(f"Invalid token response: {data}")

        self.headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
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

    def get_group_id(self, group_email: str) -> int:
        """
        Fetches the Zoho Group ID (zgid) for a given group email.
        Args:
            group_email (str): The email address of the group.
        Returns:
            int: The Zoho Group ID (zgid).
        Raises:
            Exception: If the group is not found or the API call fails.
        """
        if self.dry_run:
            print(f"[DRY-RUN] Would fetch group ID for {group_email}")
            return "DRY_RUN_GROUP_ID"
        
        response = requests.get(f"{self.url}{self.get_org_id()}/groups", headers=self.headers)
        data = response.json()

        if not response.ok:
            raise Exception(f"Failed to fetch groups: {data}")

        groups = data.get("data", {}).get("groups", [])
        for group in groups:
            if group.get("emailId") == group_email:
                return group.get("zgid")

        raise Exception(f"Group not found: {group_email}")

    def split_group_list(self, data, size=100):
        """Split list into groups of given size"""
        groups = []
        for i in range(0, len(data), size):
            groups.append(data[i:i + size])
        return groups
    
    def fetch_channel_member_emails(self, zgid: str):

        if self.dry_run:
            print(f"[DRY-RUN] Would fetch members for group {zgid}")
            return set()

        url = f"{self.url}{self.get_org_id()}/groups/{zgid}/members"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        response = response.json()
        emails = set()

        members = (response.get("data", {}).get("mailGroupMemberList", []))
        for member in members:
            email = member.get("memberEmailId")
            if email:
                emails.add(email.lower())

        return emails

    def add_users_to_group(self, zgid: str, users_to_add):

        for batch in self.split_group_list(list(users_to_add), 100):
            if self.dry_run:
                print(f"[DRY-RUN] Would add users to group {zgid}")
                continue

            payload = {
                "mode": "addMailGroupMember",
                "mailGroupMemberList": [
                    {"memberEmailId": user, "role": "member"} for user in batch
                ],
                }
            url = f"{self.url}{self.get_org_id()}/groups/{zgid}"
            response = requests.put(url, headers=self.headers, json=payload )

            if response.status_code == 200:
                print(f"Added {batch} successfully")
            else:
                print("Added failed:", response.text)


    def remove_users_from_group(self, zgid: str, users_to_remove):

        for batch in self.split_group_list(list(users_to_remove), 100):
            if self.dry_run:
                print(f"[DRY-RUN] Would remove users from group {zgid}")
                continue

            payload = {
                "mode": "deleteMailGroupMember",
                "mailGroupMemberList": [
                    {"memberEmailId": user}
                    for user in batch
                ],
            }
            url = f"{self.url}{self.get_org_id()}/groups/{zgid}"
            response = requests.put(url, headers=self.headers, json=payload)

            if response.status_code == 200:
                print(f"Removed {batch} successfully")
            else:
                print("Remove failed:", response.text)

    def get_user_details_by_email(self, email):
        if self.dry_run:
            print(f"[DRY-RUN] Would fetch user details for {email}")
            return None

        url = f"{self.url}{self.get_org_id()}/accounts/{email}"
        response = requests.get(url,headers=self.headers)

        result = response.json()
        account = result.get("data", {})
        primary_email = account.get("primaryEmailAddress")
        if primary_email == email.lower():
                return primary_email

        return None

    def sync_members(self, zgid: str, desired_users) -> None:

        current_users = self.fetch_channel_member_emails(zgid)
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
            self.add_users_to_group(zgid, to_add)

        self.remove_users_from_group(zgid, to_remove)

    def sync_groups_from_csv(self) -> None:
        """
        Read all CSV files and synchronize members for each 
        corresponding Zoho Mail group.
        """
        self.renew_access_token()
        groups = self.read_groups()

        for group in groups:
            group_email = f"{group['name']}@{DOMAIN_NAME}"
            try:
                channel_id = self.get_group_id(group_email)

            except Exception as e:
                logging.error("Group not found: %s", group_email)
                sys.exit(1)

            self.sync_members(channel_id, group["users"])

def register(subparsers):
    parser = subparsers.add_parser(
        "zoho-mail",
        help="Zoho Mail operations"
    )

    parser.add_argument("--client-id", required=True)
    parser.add_argument("--client-secret", required=True)
    parser.add_argument("--refresh-token", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.set_defaults(func=run)


def run(args):
    zc = ZohoMailGroup(
        client_id=args.client_id,
        client_secret=args.client_secret,
        refresh_token=args.refresh_token,
        dryrun=args.dry_run
    )
    zc.sync_groups_from_csv()
