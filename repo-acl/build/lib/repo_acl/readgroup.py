"""Read group users information from CSV files in the group directory
Then Read usernames from the PeopleDB CSV file in peopledb directory
Validate group membership against PeopleDB. identifies valid users
that are present in PeopleDB to sync with the Gitlab, Zoho group users."""

import csv
import os

from typing import Set

ACL_GROUPS_DIR = os.getenv("REPO_ACL_GROUPS_DIR", "./groups")
PEOPLEDB_DIR = os.getenv("PEOPLEDB_DIR", "./peopledb")
PEOPLEDB_FILE = "employees.csv"

class ReadGroup:
    """Validate the group users in Git to sync with the Gitlab group users"""

    def __init__(self):
        self.invalid_users: Set[str] = set()

    def read_groups(self, group_dir) -> list[dict]:
        """
        Read group user information from CSV files in the groups directory.

        Each CSV file represents a Git group, where the filename is the group
        name and each row contains a username. The function returns a list of
        dictionaries containing the group name and its desired users.

        Returns:
            list[dict]: A list of dictionaries with the following keys:
                - name: GitLab group name derived from the CSV filename.
                - users: Set of usernames configured for the group.
        """

        if not os.path.exists(group_dir):
            raise FileNotFoundError(f"Group directory does not exist: {group_dir}")

        groups = []
        for file in os.listdir(group_dir):
            if file.endswith(".csv"):
                users = set()

                with open(os.path.join(group_dir, file), encoding="utf-8") as f:
                    for row in csv.reader(f):
                        if row and row[0]:
                            user = row[0].strip().lower()
                            users.add(user)
                groups.append({
                    "name": file.replace(".csv", ""),
                    "users": users
                })
        return groups

    def read_peopledb_file(self, peopledb_dir, file) -> set[str]:
        """
        Read usernames from the PeopleDB CSV file.

        Args:
            peopledb_dir: Directory containing the PeopleDB CSV file.
            file : employees.csv

        Returns:
            set[str]: Set of usernames available in PeopleDB.

        format:
            id,cn,sn,user,active
            ZS001,ZILOGIC,Z,zilogic.z,true
        """
        users = set()
        with open(os.path.join(peopledb_dir, file), encoding="utf-8") as f:
            for row in csv.reader(f):
                user = row[3].strip().lower()
                user_status = row[4].strip().lower() == "true"
                if user and user_status:
                    users.add(user)
        return users

    def sync_all_groups_with_peopledb(self) -> list[dict]:
        """
        Validate group users against PeopleDB.

        Reads group users from the configured groups directory and PeopleDB,
        identifies users that are missing from PeopleDB, and returns each group
        with only the users that are present in PeopleDB.

        Returns:
            list[dict]: Synchronized group information, where each dictionary
                        contains the group name and a set of valid  and invalid
                        PeopleDB users.
        """
        groups = self.read_groups(ACL_GROUPS_DIR)
        peopledb_users = self.read_peopledb_file(PEOPLEDB_DIR, PEOPLEDB_FILE)

        synced_groups_with_peopledb = []

        for group in groups:

            invalid_users = group["users"] - peopledb_users
            self.invalid_users.update(invalid_users)

            valid_users = group["users"] & peopledb_users

            synced_groups_with_peopledb.append({
                "name": group["name"],
                "users": valid_users,
                "invalid_users": invalid_users,
            })

        return synced_groups_with_peopledb

    def display_invalid_users(self) -> None:
        """
        Display users who are not found in the PeopleDB.
        The invalid users are sorted before being displayed.
        """
        print("\n")
        if self.invalid_users:
            for user in sorted(self.invalid_users):
                print("Users not found in PeopleDB: ", user)
            # sys.exit(1)
