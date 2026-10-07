import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
import os
import csv
import logging
import gitlab


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


GROUP_BASE_PATH = "org/groups"
DEVELOPER_ACCESS_LEVEL = 30


# =========================================================
# GITLAB GROUP MEMBER SYNC
# =========================================================

class GitLabGroupMemberSync:

    def __init__(
        self,
        gitlab_url: str,
        token: str,
        dry_run: bool = False,
    ) -> None:

        self.dry_run = dry_run

        self.gl = gitlab.Gitlab(
            gitlab_url,
            private_token=token,
            keep_base_url=True
        )

        self.gl.auth()

    def configure_logging(self):

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
        )

    # ---------------------------------------------------------
    # LOAD CSV
    # ---------------------------------------------------------

    def _load_users_from_csv(
        self,
        csv_path: Path
    ):

        users = set()

        with csv_path.open(
            encoding="utf-8"
        ) as file:

            for line_number, line in enumerate(
                file,
                start=1
            ):

                username = line.strip()

                if not username:
                    continue

                if "," in username:

                    raise ValueError(
                        f"{csv_path.name}:{line_number} "
                        "Invalid format: file must contain only usernames"
                    )

                users.add(username)

        return users

    # ---------------------------------------------------------
    # GET GROUP
    # ---------------------------------------------------------

    def _get_group(self, group_path):

        try:

            return self.gl.groups.get(
                group_path
            )

        except gitlab.exceptions.GitlabGetError:

            logging.warning(
                "Group not found: %s",
                group_path
            )

            return None

    # ---------------------------------------------------------
    # GET CURRENT MEMBERS
    # ---------------------------------------------------------

    def _get_current_members(self, group):

        return {
            member.username: member
            for member in group.members.list(all=True)
        }

    # ---------------------------------------------------------
    # ADD MEMBER
    # ---------------------------------------------------------

    def add_member(
        self,
        group_path,
        username
    ):

        group = self._get_group(
            group_path
        )

        if not group:
            return False

        users = self.gl.users.list(
            username=username
        )

        if not users:

            logging.warning(
                "User not found: %s",
                username
            )

            return False

        if users[0].state == "blocked":

            logging.info(
                "Skipping blocked user: %s",
                username
            )

            return False

        current_members = (
            self._get_current_members(group)
        )

        if username in current_members:

            logging.info(
                "User already exists: %s",
                username
            )

            return False

        if self.dry_run:

            print(
                f"DRY_ADD {username}"
            )

            return True

        logging.info(
            "ADD user=%s",
            username
        )

        group.members.create(
            {
                "user_id": users[0].id,
                "access_level":
                    DEVELOPER_ACCESS_LEVEL,
            }
        )

        return True

    # ---------------------------------------------------------
    # REMOVE MEMBER
    # ---------------------------------------------------------

    def remove_member(
        self,
        group_path,
        username
    ):

        group = self._get_group(
            group_path
        )

        if not group:
            return False

        current_members = (
            self._get_current_members(group)
        )

        if username not in current_members:

            logging.info(
                "User is not a member: %s",
                username
            )

            return False

        if self.dry_run:

            print(
                f"DRY_REMOVE {username}"
            )

            return True

        logging.info(
            "REMOVE user=%s",
            username
        )

        current_members[
            username
        ].delete()

        return True

    # ---------------------------------------------------------
    # SYNC SINGLE GROUP
    # ---------------------------------------------------------

    def sync_group_from_csv(
        self,
        csv_path
    ):

        csv_file = Path(
            csv_path
        )

        group_path = (
            f"{GROUP_BASE_PATH}/{csv_file.stem}"
        )

        desired_users = (
            self._load_users_from_csv(
                csv_file
            )
        )

        self._sync_group(
            group_path,
            desired_users
        )

    # ---------------------------------------------------------
    # SYNC GROUP
    # ---------------------------------------------------------

    def _sync_group(
        self,
        group_path,
        desired_users
    ):

        group = self._get_group(
            group_path
        )

        if not group:
            return

        current_members = (
            self._get_current_members(group)
        )

        # ADD
        for username in sorted(
            desired_users
        ):

            if username not in current_members:

                self.add_member(
                    group_path,
                    username
                )

        # REMOVE
        for username, member in sorted(
            current_members.items()
        ):

            if username not in desired_users:

                self.remove_member(
                    group_path,
                    username
                )


# =========================================================
# GUI
# =========================================================

class RobotBatchRunner(ctk.CTk):

    def __init__(self):

        super().__init__()

        self.geometry(
            "1200x750"
        )

        self.title(
            "ZILOGIC REPO ACL"
        )

        self.selected_directory = ""
        self.selected_csv_file = ""
        self.current_group = ""

        self.syncer = None

        self.create_widgets()

    # =========================================================
    # GUI
    # =========================================================

    def create_widgets(self):

        # -----------------------------------------------------
        # LEFT SIDE
        # -----------------------------------------------------

        sidebar_container = ctk.CTkFrame(
            self,
            width=300
        )

        sidebar_container.pack(
            side="left",
            fill="y",
            padx=10,
            pady=10
        )

        self.sidebar = ctk.CTkScrollableFrame(
            sidebar_container,
            width=280
        )

        self.sidebar.pack(
            expand=True,
            fill="both"
        )

        # -----------------------------------------------------
        # RIGHT SIDE
        # -----------------------------------------------------

        right_container = ctk.CTkFrame(
            self
        )

        right_container.pack(
            side="right",
            expand=True,
            fill="both",
            padx=10,
            pady=10
        )

        self.right_frame = ctk.CTkScrollableFrame(
            right_container
        )

        self.right_frame.pack(
            expand=True,
            fill="both",
            padx=10,
            pady=10
        )

        # -----------------------------------------------------
        # FILE
        # -----------------------------------------------------

        ctk.CTkLabel(
            self.sidebar,
            text="Select CSV File:"
        ).pack(
            pady=(10, 0)
        )

        self.file_input = ctk.CTkEntry(
            self.sidebar
        )

        self.file_input.pack(
            padx=10,
            pady=5,
            fill="x"
        )

        self.csv_button = ctk.CTkButton(
            self.sidebar,
            text="Browse CSV",
            command=self.select_csv_file
        )

        self.csv_button.pack(
            padx=10,
            pady=5,
            fill="x"
        )

        # -----------------------------------------------------
        # DIRECTORY
        # -----------------------------------------------------

        self.directory_button = ctk.CTkButton(
            self.sidebar,
            text="Browse Directory",
            command=self.select_directory
        )

        self.directory_button.pack(
            padx=10,
            pady=5,
            fill="x"
        )

        # -----------------------------------------------------
        # GROUPS
        # -----------------------------------------------------

        ctk.CTkLabel(
            self.sidebar,
            text="Groups",
            font=("Arial", 16, "bold")
        ).pack(
            pady=(20, 5)
        )

        self.group_frame = ctk.CTkFrame(
            self.sidebar
        )

        self.group_frame.pack(
            fill="x",
            padx=5,
            pady=5
        )

    # =========================================================
    # SELECT CSV
    # =========================================================

    def select_csv_file(self):

        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[
                ("CSV Files", "*.csv"),
                ("All Files", "*.*")
            ]
        )

        if file_path:

            self.selected_csv_file = file_path

            self.file_input.delete(
                0,
                "end"
            )

            self.file_input.insert(
                0,
                file_path
            )

            self.current_group = Path(
                file_path
            ).stem

            self.display_csv(
                file_path
            )

    # =========================================================
    # SELECT DIRECTORY
    # =========================================================

    def select_directory(self):

        directory = filedialog.askdirectory(
            title="Select Directory"
        )

        if not directory:
            return

        self.selected_directory = directory

        self.file_input.delete(
            0,
            "end"
        )

        self.file_input.insert(
            0,
            directory
        )

        self.clear_group_list()

        self.display_csv_files(
            directory
        )

    # =========================================================
    # CLEAR GROUP LIST
    # =========================================================

    def clear_group_list(self):

        for widget in (
            self.group_frame.winfo_children()
        ):

            widget.destroy()

    # =========================================================
    # DISPLAY GROUPS
    # =========================================================

    def display_csv_files(
        self,
        directory
    ):

        csv_files = sorted(
            [
                file
                for file in os.listdir(directory)
                if file.lower().endswith(".csv")
            ]
        )

        if not csv_files:

            ctk.CTkLabel(
                self.group_frame,
                text="No CSV files found."
            ).pack(
                pady=5
            )

            return

        for file_name in csv_files:

            group_name = Path(
                file_name
            ).stem

            button = ctk.CTkButton(
                self.group_frame,
                text=group_name,
                anchor="w",
                command=lambda name=file_name:
                    self.group_selected(name)
            )

            button.pack(
                fill="x",
                padx=5,
                pady=2
            )

    # =========================================================
    # GROUP SELECTED
    # =========================================================

    def group_selected(
        self,
        file_name
    ):

        file_path = os.path.join(
            self.selected_directory,
            file_name
        )

        self.selected_csv_file = file_path

        self.current_group = Path(
            file_path
        ).stem

        self.file_input.delete(
            0,
            "end"
        )

        self.file_input.insert(
            0,
            file_path
        )

        self.display_csv(
            file_path
        )

    # =========================================================
    # DISPLAY CSV
    # =========================================================

    def display_csv(
        self,
        file_path
    ):

        # Clear previous table
        for widget in (
            self.right_frame.winfo_children()
        ):

            widget.destroy()

        # -----------------------------------------------------
        # TITLE
        # -----------------------------------------------------

        ctk.CTkLabel(
            self.right_frame,
            text=f"Group: {Path(file_path).stem}",
            font=("Arial", 20, "bold")
        ).grid(
            row=0,
            column=0,
            columnspan=3,
            pady=15
        )

        # -----------------------------------------------------
        # HEADERS
        # -----------------------------------------------------

        ctk.CTkLabel(
            self.right_frame,
            text="User",
            font=("Arial", 14, "bold")
        ).grid(
            row=1,
            column=0,
            padx=20,
            pady=10
        )

        ctk.CTkLabel(
            self.right_frame,
            text="CI-Server",
            font=("Arial", 14, "bold")
        ).grid(
            row=1,
            column=1,
            padx=20,
            pady=10
        )

        ctk.CTkLabel(
            self.right_frame,
            text="Action",
            font=("Arial", 14, "bold")
        ).grid(
            row=1,
            column=2,
            padx=20,
            pady=10
        )

        # -----------------------------------------------------
        # READ CSV
        # -----------------------------------------------------

        try:

            with open(
                file_path,
                newline="",
                encoding="utf-8"
            ) as file:

                reader = csv.reader(file)

                rows = [
                    row
                    for row in reader
                    if row
                ]

        except Exception as error:

            messagebox.showerror(
                "CSV Error",
                str(error)
            )

            return

        # -----------------------------------------------------
        # GET CI SERVER
        # -----------------------------------------------------

        ci_server = os.getenv(
            "CI_SERVER_URL",
            "Not Configured"
        )

        # -----------------------------------------------------
        # DISPLAY USERS
        # -----------------------------------------------------

        for index, row in enumerate(
            rows,
            start=2
        ):

            username = row[0].strip()

            # User
            ctk.CTkLabel(
                self.right_frame,
                text=username,
                anchor="w"
            ).grid(
                row=index,
                column=0,
                padx=20,
                pady=5,
                sticky="w"
            )

            # CI Server
            ctk.CTkLabel(
                self.right_frame,
                text=ci_server,
                anchor="w"
            ).grid(
                row=index,
                column=1,
                padx=20,
                pady=5,
                sticky="w"
            )

            # Action frame
            action_frame = ctk.CTkFrame(
                self.right_frame
            )

            action_frame.grid(
                row=index,
                column=2,
                padx=20,
                pady=5
            )

            # ADD
            ctk.CTkButton(
                action_frame,
                text="Add",
                width=70,
                command=lambda user=username:
                    self.add_user(user)
            ).pack(
                side="left",
                padx=3
            )

            # REMOVE
            ctk.CTkButton(
                action_frame,
                text="Remove",
                width=70,
                command=lambda user=username:
                    self.remove_user(user)
            ).pack(
                side="left",
                padx=3
            )

    # =========================================================
    # CREATE SYNCER
    # =========================================================

    def create_syncer(self):

        gitlab_url = os.getenv(
            "CI_SERVER_URL"
        )

        token = os.getenv(
            "GITLAB_RO_ACCESS_TOKEN"
        )

        if not gitlab_url:

            messagebox.showerror(
                "Configuration Error",
                "CI_SERVER_URL is not configured."
            )

            return None

        if not token:

            messagebox.showerror(
                "Configuration Error",
                "GITLAB_RO_ACCESS_TOKEN is not configured."
            )

            return None

        try:

            return GitLabGroupMemberSync(
                gitlab_url=gitlab_url,
                token=token
            )

        except Exception as error:

            messagebox.showerror(
                "GitLab Error",
                str(error)
            )

            return None

    # =========================================================
    # ADD USER
    # =========================================================

    def add_user(
        self,
        username
    ):

        if not self.current_group:

            return

        syncer = self.create_syncer()

        if not syncer:
            return

        group_path = (
            f"{GROUP_BASE_PATH}/"
            f"{self.current_group}"
        )

        try:

            result = syncer.add_member(
                group_path,
                username
            )

            if result:

                messagebox.showinfo(
                    "Add User",
                    f"{username} added successfully."
                )

            else:

                messagebox.showwarning(
                    "Add User",
                    f"{username} was not added."
                )

        except Exception as error:

            messagebox.showerror(
                "Add User Error",
                str(error)
            )

    # =========================================================
    # REMOVE USER
    # =========================================================

    def remove_user(
        self,
        username
    ):

        if not self.current_group:

            return

        syncer = self.create_syncer()

        if not syncer:
            return

        group_path = (
            f"{GROUP_BASE_PATH}/"
            f"{self.current_group}"
        )

        try:

            result = syncer.remove_member(
                group_path,
                username
            )

            if result:

                messagebox.showinfo(
                    "Remove User",
                    f"{username} removed successfully."
                )

            else:

                messagebox.showwarning(
                    "Remove User",
                    f"{username} was not removed."
                )

        except Exception as error:

            messagebox.showerror(
                "Remove User Error",
                str(error)
            )


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    app = RobotBatchRunner()

    app.mainloop()