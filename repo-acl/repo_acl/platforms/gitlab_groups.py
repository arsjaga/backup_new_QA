import logging

from typing import Set
import gitlab
from repo_acl.readgroup import ReadGroup

GROUP_BASE_PATH = "org/groups"
DEVELOPER_ACCESS_LEVEL = 30

class GitLabGroupMemberSync:
    def __init__(
        self,
        gitlab_url: str,
        token: str,
        dry_run: bool = False,
    ) -> None:
        self.dry_run = dry_run
        self.missing_groups: Set[str] = set()
        self.blocked_users: Set[str] = set()
        self.missing_gitlab_users: Set[str] = set()
        self.read_group = ReadGroup()

        self.gl = gitlab.Gitlab(gitlab_url, private_token=token, keep_base_url=True)
        self.gl.auth()

    def configure_logging(self) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
        )

    def display_invalid_groups(self) -> None:
        print("\n")
        if self.missing_groups:
            for group_path in sorted(self.missing_groups):
                logging.error("Groups not found in GitLab: %s", group_path)
            # sys.exit(1)

    def display_blocked_users(self):
        print("\n")
        if self.blocked_users:
            for user in sorted(self.blocked_users):
                logging.error("Blocked user in GitLab: %s", user)

    def display_missing_gitlab_users(self):
        print("\n")
        if self.missing_gitlab_users:
            for user in sorted(self.missing_gitlab_users):
                logging.error("User not found in GitLab: %s", user)

    def _get_group(self, group_path: str):
        try:
            return self.gl.groups.get(group_path)
        except gitlab.exceptions.GitlabGetError:
            self.missing_groups.add(group_path)
            return

    def _get_current_members(self, group):
        return {member.username: member for member in group.members.list(all=True)}

    def block_user(self, username : str):
        users = self.gl.users.list(username=username)

        if not users:
            self.missing_gitlab_users.add(username)
            return None

        user = users[0]

        if user.state == "blocked":
            self.blocked_users.add(username)
            return None

        return user

    def _add_member(self, group, username: str) -> None:

        if self.dry_run:
            print(f"DRY_ADD {username}")
            return

        users = self.block_user(username)
        if not users:
            return

        logging.info("ADD user=%s", username)
        group.members.create(
            {
                "user_id": users.id,
                "access_level": DEVELOPER_ACCESS_LEVEL,
            }
        )

    def _remove_member(self, group, username: str) -> None:
        if self.dry_run:
            print(f"DRY_REMOVE {username}")
            return

        users = self.block_user(username)
        if not users:
            return

        logging.info("REMOVE user=%s", username)
        group.members.delete(users.id)

    def _sync_group(self, group_path: str, desired_users: Set[str]) -> None:

        logging.info("Processing group: %s", group_path)
        group = self._get_group(group_path)

        if not group:
            return

        current_members = self._get_current_members(group)

        for username in sorted(desired_users):
            if username not in current_members:
                self._add_member(group, username)

        for username in sorted(current_members):
            if username not in desired_users:
                self._remove_member(group, username)

    def sync_all_groups(self) -> None:
        self.configure_logging()
        groups = self.read_group.sync_all_groups_with_peopledb()
        for group in groups:
            group_path = f"{GROUP_BASE_PATH}/{group['name']}"
            self._sync_group(group_path, group["users"])

        self.read_group.display_invalid_users()
        self.display_invalid_groups()
        self.display_blocked_users()
        self.display_missing_gitlab_users()


def register(subparsers):
    parser = subparsers.add_parser(
        "gitlab-groups",
        help="GitLab group operations"
    )

    parser.add_argument("--gitlab-url", required=True)
    parser.add_argument("--access-token", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.set_defaults(func=run)


def run(args):
    syncer = GitLabGroupMemberSync(
        gitlab_url=args.gitlab_url,
        token=args.access_token,
        dry_run=args.dry_run,
    )
    syncer.sync_all_groups()
