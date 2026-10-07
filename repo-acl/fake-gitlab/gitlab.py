import json
import atexit
import os
import sys

db_path = os.getenv("FAKE_GITLAB_DB_PATH")
if not db_path:
    print("fake-gitlab: set FAKE_GITLAB_DB_PATH")
    sys.exit(1)

with open(db_path) as fp:
    DB = json.load(fp)

class exceptions:
    class GitlabGetError(Exception):
        pass

@atexit.register
def flush():
    with open(db_path, "w") as fp:
        json.dump(DB, fp, indent=4)

class Member:
    def __init__(self, member, member_list, group):
        self.data = member
        self._member_list = member_list
        self._group = group

        self.id = member["user_id"]
        self.access_level = member["access_level"]

        self.username = None
        for user in DB["users"]:
            if user["id"] == self.data["user_id"]:
                self.username = user["name"]

    def save(self):
        self.data["access_level"] = self.access_level

    def delete(self):
        user_id = self.data["user_id"]

        for i, m in enumerate(self._member_list):
            if m["user_id"] == user_id:
                del self._member_list[i]
                break

        for issue in DB.get("issues", []):
            if (
                issue["group_id"] == self._group.id
                and issue["assignee_id"] == user_id
            ):
                issue["assignee_id"] = user_id

        for merge_request in DB.get("merge_requests", []):
            if (
                merge_request["group_id"] == self._group.id
                and merge_request["assignee_id"] == user_id
            ):
                merge_request["assignee_id"] = user_id

class Members:
    def __init__(self, group):
        self.data = group.data["members"]
        self._group = group

    def create(self, member):
        self.data.append(member)

    def list(self, **kwargs):
        l = []
        for m in self.data:
            l.append(Member(m, self.data, self._group))
        return l

    def get(self, user_id):
        for member in self.data:
            if member["user_id"] == user_id:
                return Member(member, self.data, self._group)
        raise exceptions.GitlabGetError()

    def delete(self, user_id):
        for i, m in enumerate(self.data):
            if m["user_id"] == user_id:
                del self.data[i]
                return
        raise exceptions.GitlabGetError()

class Group:
    def __init__(self, group, group_list):
        self.data = group
        self._group_list = group_list
        self.members = Members(self)
        self.members_all = self.members

        self.id = group["id"]
        self.path = group["path"]

class Groups:
    def __init__(self):
        self.data = DB["groups"]

    def get(self, path):
        for g in DB["groups"]:
            if g["path"] == path:
                return Group(g, DB["groups"])
        else:
            raise exceptions.GitlabGetError

class User:
    def __init__(self, user):
        self.data = user
        self.state = user["state"]
        self.id = user["id"]
        self.username = user["name"]

class Users:
    def __init__(self):
        self.data = DB["users"]

    def list(self,username=None, **kwargs):
        result = []

        for user in self.data:
            if username is not None:
                if user["name"] != username:
                    continue
            result.append(User(user))
        return result


class Project:
    def __init__(self, project):
        self.data = project

        self.id = project["id"]
        self.project_path = project["project_path"]

        self.members = Members(self)
        self.members_all = self.members

        self.shared_with_groups = project.setdefault(
            "shared_with_groups",
            []
        )

    def share(self, group_id, group_access):

        for share in self.shared_with_groups:
            if share["group_id"] == group_id:
                raise Exception("Group already shared")

        self.shared_with_groups.append({
            "group_id": group_id,
            "group_access_level": group_access
        })

    def unshare(self, group_id):
        for i, share in enumerate(self.shared_with_groups):
            if share["group_id"] == group_id:
                del self.shared_with_groups[i]
                return

        raise exceptions.GitlabGetError()


class Projects:
    def __init__(self):
        self.data = DB.get("projects", [])

    def get(self, project_path, **kwargs):
        for project in self.data:
            if project["project_path"] == project_path:
                return Project(project)
        raise exceptions.GitlabGetError()

class const:
    GUEST_ACCESS = 10
    REPORTER_ACCESS = 20
    DEVELOPER_ACCESS = 30
    MAINTAINER_ACCESS = 40
    OWNER_ACCESS = 50
    NO_ACCESS = -1


class Gitlab:
    def __init__(self, gitlab_url, *args, **kwargs):
        self.gitlab_url = gitlab_url
        self.groups = Groups()
        self.users = Users()
        self.projects = Projects()

    def auth(self):
        gitlab_config = DB.get("gitlab", {})

        configured_url = gitlab_config.get("url")

        if configured_url and self.gitlab_url != configured_url:
            raise ConnectionError(
                f"GitLab server is not accessible: {self.gitlab_url}"
            )

        if gitlab_config.get("accessible") is False:
            raise ConnectionError(
                f"GitLab server is not accessible: {self.gitlab_url}"
            )


if __name__ == "__main__":
    gl = Gitlab()
    gl.auth()

    print(DB)
    group = gl.groups.get("automotive-team")
    print(group)
    group.members.create({"user_id": 10, "access_level": 30})