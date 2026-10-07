import argparse
import csv
import gitlab
import os
import sys

from repo_acl.platforms import zoho_mail
from repo_acl.platforms import zoho_cliq
from repo_acl.platforms import gitlab_groups

from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed


class ACL:

    def __init__(self, gitlab_url, token, dry_run=False):

        self.group_prefix = "org/groups/"
        self.dry_run = dry_run

        self.gl = gitlab.Gitlab(
            gitlab_url,
            private_token=token,
            keep_base_url=True,
        )

        self.gl.auth()

        self.access_map = {
            "guest": gitlab.const.GUEST_ACCESS,
            "reporter": gitlab.const.REPORTER_ACCESS,
            "developer": gitlab.const.DEVELOPER_ACCESS,
            "maintainer": gitlab.const.MAINTAINER_ACCESS,
            "owner": gitlab.const.OWNER_ACCESS,
            "no-access": gitlab.const.NO_ACCESS,
        }

    def share_group(self, username: str, project_path: str, access: str):

        group_path = f"{self.group_prefix}{username[1:]}"
        access_level = self.access_map[access]

        if self.dry_run:
            if access == "no-access":
                print(f"[DRY RUN] Would remove group '{group_path}' from project '{project_path}'")
            else:
                print(f"[DRY RUN] Would share group '{group_path}' with project '{project_path}' as {access}")
            return

        try:
            project = self.gl.projects.get(project_path, lazy=False)
            group = self.gl.groups.get(group_path)

            group_shared = any(share["group_id"] == group.id for share in project.shared_with_groups)

            if access == "no-access":
                if group_shared:
                    project.unshare(group.id)
                    print(f"Removed group {group.full_path} from project {project.path_with_namespace}")
                else:
                    print(f"Group {group.full_path} is not shared with project {project.path_with_namespace}")

            else:
                if group_shared:
                    print(f"Group {group.full_path} already shared with {project.path_with_namespace}")
                else:
                    project.share(group.id, group_access=access_level)
                    print(f"Added group {group.full_path} to project {project.path_with_namespace}")

        except Exception as e:
            print(f"[ERROR] Sharing failed for project {project_path} and group {group_path}: {e}")

    def process_csv(self, csv_file: str):
        with open(csv_file, newline="") as f:
            reader = csv.DictReader(f)

            for row in reader:
                if row["type"].strip().lower() != "project":
                    continue

                access = (row["access_level"].strip().lower())
                if access not in self.access_map:
                    print(f"[SKIP] Invalid access level: {access}")
                    continue

                self.share_group(
                    username=row["username"].strip(),
                    project_path=row["group_or_project_path"].strip(),
                    access=access,
                )

def acl_register(subparsers):

    parser = subparsers.add_parser(
        "acl",
        help="Share GitLab groups with projects",
    )

    parser.add_argument("--gitlab-url", required=True)
    parser.add_argument("--access-token", required=True)
    parser.add_argument("--csv-file", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.set_defaults(func=acl_run)


def acl_run(args):

    access_token = (args.access_token or os.getenv("GITLAB_ACCESS_TOKEN"))
    if not access_token:
        print("Error: Access token must be provided ")
        sys.exit(1)

    acl = ACL(gitlab_url=args.gitlab_url,token=access_token,dry_run=args.dry_run)
    acl.process_csv(args.csv_file)


def main():

    parser = argparse.ArgumentParser(prog="main.py")
    subparsers = parser.add_subparsers(
        dest="platform",
        required=True,
    )

    zoho_mail.register(subparsers)
    zoho_cliq.register(subparsers)
    gitlab_groups.register(subparsers)
    acl_register(subparsers)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()