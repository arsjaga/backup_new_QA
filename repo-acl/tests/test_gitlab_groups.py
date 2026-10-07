import unittest
from unittest.mock import patch , MagicMock, mock_open
import logging
from pathlib import Path
import gitlab
from repo_acl.platforms.gitlab_groups import GitLabGroupMemberSync, run, register,DEVELOPER_ACCESS_LEVEL

class TestSetUp(unittest.TestCase):

    def setUp(self):
        self.patch_call_gitlab()
        self.gg = GitLabGroupMemberSync(
            gitlab_url = "test_url",
            token = "xxxxxxx",
            dry_run = False,
        )   

    def patch_call_gitlab(self):
        patcher = patch("gitlab.Gitlab")
        mock_gl = patcher.start()
        self.addCleanup(patcher.stop)
        return mock_gl

    def patch_call_function(self,func_name):
        patcher = patch.object(GitLabGroupMemberSync,func_name)
        mock_groups = patcher.start()
        self.addCleanup(patcher.stop)
        return mock_groups

    def patch_call_list_dir(self):
        patcher = patch("os.listdir")
        mock_list_dir = patcher.start()
        self.addClassCleanup(patcher.stop)
        return mock_list_dir

    def patch_call_file_open(self,data):
        patcher = patch("pathlib.open", new_callable=mock_open, read_data=data)
        mock_file_open = patcher.start()
        self.addClassCleanup(patcher.stop)
        return mock_file_open

    def patch_call_logging(self,value):
        patcher = patch(f"logging.{value}")
        mock_logging = patcher.start()
        self.addClassCleanup(patcher.stop)
        return mock_logging

    def patch_call_CSV_DIR(self):
        patcher = patch("repo_acl.platforms.gitlab_groups.CSV_DIR")
        mock_dir = patcher.start()
        self.addClassCleanup(patcher.stop)
        return mock_dir

class TestGitlabGuroupsDryRun(TestSetUp):

    def dry_run_true(self):
        self.gg.dry_run = True

    def dry_run_false(self):
        self.gg.dry_run = False
 
    def test_create_group_dry_run(self):
        data = MagicMock(id = 12,name = "parent_group")
        self.gg.gl.groups.get.return_value = data
        self.dry_run_true()
        with patch("builtins.print") as mock_print:
            result = self.gg._create_group("group/path/group_name")
            mock_print.assert_any_call("DRY_CREATE_GROUP group/path/group_name")
            self.assertAlmostEqual(result,None)
        self.dry_run_false()

    def test_add_member_dry_run(self):
        mock_group = MagicMock()
        self.dry_run_true()
        with patch("builtins.print") as mock_print:
            self.gg._add_member(mock_group,"kim")
            mock_print.assert_any_call("DRY_ADD kim")
        self.dry_run_false()

    def test_remove_member_dry_run(self):
        mock_member = MagicMock()
        self.dry_run_true()
        with patch("builtins.print") as mock_print:
            self.gg._remove_member(mock_member,"kim")
            mock_print.assert_any_call("DRY_REMOVE kim")
        self.dry_run_false() 

class TestGitlabGuroupsActual(TestSetUp):

    def test_register(self):
        mock_parser = MagicMock()
        mock_chailed_parser = mock_parser.add_parser.return_value
        register(mock_parser)
        mock_chailed_parser.add_argument.assert_any_call("--gitlab-url", required=True)
        mock_chailed_parser.add_argument.assert_any_call("--gitlab-url", required=True)
        mock_chailed_parser.add_argument.assert_any_call("--dry-run", action="store_true")

    def test_run(self):
        self.patch_call_gitlab()
        mock_groups = self.patch_call_function(func_name = "sync_all_groups")
        args = MagicMock()
        args.gitlab_url = "test_url"
        args.access_token = "xxxxxxx"
        args.dry_run = False
        run(args)
        mock_groups.assert_called_once()

    def test_configure_logging(self):
        mock_config = self.patch_call_logging(value="basicConfig")
        self.gg.configure_logging()
        mock_config.assert_called_with(level=logging.INFO,format="%(asctime)s [%(levelname)s] %(message)s")

    def test_load_users_from_csv_success(self):
        data = "name1\nname2\nname3"
        mock_list_dir = self.patch_call_list_dir()
        mock_file_open = self.patch_call_file_open(data)
        mock_list_dir.open = mock_file_open
        mock_list_dir.name = "groups"
        users = self.gg._load_users_from_csv(mock_list_dir)
        self.assertIn("name1",users)
        self.assertIn("name2",users)
        self.assertIn("name3",users)

    def test_load_users_from_csv_failure(self):
        data="name1\nname2,\nname3"
        mock_list_dir = self.patch_call_list_dir()
        mock_file_open = self.patch_call_file_open(data)
        mock_list_dir.open = mock_file_open
        mock_list_dir.name = "groups"
        with self.assertRaisesRegex(ValueError,"groups:2 Invalid format: file must contain only usernames"):
            self.gg._load_users_from_csv(mock_list_dir)

    def test_sync_group_success(self):
        mock_info = self.patch_call_logging(value = "info")
        mock_group = self.patch_call_function(func_name = "_get_group")
        mock_current_mem = self.patch_call_function(func_name = "_get_current_members")
        mock_add_mem = self.patch_call_function(func_name = "_add_member")
        mock_remove_mem = self.patch_call_function(func_name = "_remove_member")
        mock_group.return_value = "name"
        mock_current_mem.return_value = { "user_x" : "member1"}  
        self.gg._sync_group("group_path",{"user_y"})
        mock_info.assert_called_with("Processing group: %s","group_path")
        mock_group.assert_called_once()
        mock_current_mem.asssert_called_once()
        mock_add_mem.assert_called_once()
        mock_remove_mem.assert_called_once()

    def test_sync_group_failure(self):
        mock_info = self.patch_call_logging(value = "info")
        mock_group = self.patch_call_function(func_name = "_get_group")
        mock_group.return_value = None
        with patch("builtins.print") as mock_print:
            self.gg._sync_group("group_path",{"user_y"})
            mock_print.assert_any_call("Group not found.")
        mock_info.assert_called_with("Processing group: %s","group_path")
    
    def test_get_group_success(self):
        data = [{"id": 1,"name": "Foobar Group",}]
        self.gg.gl.groups.get.return_value = data
        value=self.gg._get_group("some/group/path")
        self.assertEqual(value[0].get("name"),"Foobar Group")

    def test_get_group_failure(self):
        mock_warning = self.patch_call_logging(value = "warning")
        mock_create_group = self.patch_call_function(func_name = "_create_group")
        self.gg.gl.groups.get.side_effect = gitlab.exceptions.GitlabGetError()
        self.gg._get_group("some/group/path")
        mock_warning.assert_called_with("Group not found, creating: %s","some/group/path")
        mock_create_group.assert_called_once()

    def test_get_current_members(self):
        mock_group = MagicMock()
        mock_member = MagicMock(name="group-data")
        mock_member.username = "kim"
        mock_group.members.list.return_value = [mock_member]
        member = self.gg._get_current_members(mock_group)
        name = list(member.keys())[0]
        self.assertEqual(name,"kim")
        self.assertEqual(member[name]._mock_name,"group-data")

    def test_add_member_success(self):
        mock_info = self.patch_call_logging(value = "info")
        mock_group = MagicMock()
        fake_user = MagicMock(id=101)
        self.gg.gl.users.list.return_value = [fake_user]
        self.gg._add_member(mock_group,"kim")
        mock_info.assert_called_with("ADD user=%s role=Developer","kim")
        mock_group.members.create.assert_called_once_with({
                "user_id": 101,
                "access_level": DEVELOPER_ACCESS_LEVEL
            })
        
    def test_add_member_failure(self):
        mock_info = self.patch_call_logging(value = "info")
        mock_warning = self.patch_call_logging(value = "warning")
        mock_group = MagicMock()
        self.gg.gl.users.list.return_value = None
        self.gg._add_member(mock_group,"kim")
        mock_info.assert_called_with("ADD user=%s role=Developer","kim")
        mock_warning.assert_called_with("User not found: %s","kim")

    def test_remove_member(self):
        mock_info = self.patch_call_logging(value = "info")
        mock_member = MagicMock()
        self.gg._remove_member(mock_member,"kim")
        mock_info.assert_called_with("REMOVE user=%s","kim")

    def test_create_group_success(self):
        mock_info = self.patch_call_logging(value = "info")
        data = MagicMock(id = 12,name = "parent_group")
        self.gg.gl.groups.get.return_value = data
        self.gg._create_group("group/path/group_name")
        mock_info.assert_called_with("Creating group: %s","group/path/group_name")
        self.gg.gl.groups.create.assert_called_once_with({
                "name": "group_name",
                "path": "group_name",
                "parent_id": 12,
            })

    def test_create_group_failure(self):
        mock_error = self.patch_call_logging(value = "error")
        self.gg.gl.groups.get.side_effect = gitlab.exceptions.GitlabGetError()
        result = self.gg._create_group("group/path/group_name")
        mock_error.assert_called_with("Parent group not found: %s","group/path")
        self.assertEqual(result,None)

    def test_sync_all_groups_success(self):
        mock_dir = self.patch_call_CSV_DIR()
        mock_sync_group = self.patch_call_function(func_name = "_sync_group")
        mock_usr_load = self.patch_call_function(func_name = "_load_users_from_csv")
        mock_conf = self.patch_call_function(func_name = "configure_logging")
        mock_dir.glob.return_value = [Path("groups/test.csv")]
        self.gg.sync_all_groups()
        mock_conf.assert_called_once()
        mock_usr_load.assert_called_once()
        mock_sync_group.assert_called_once()
    
    def test_sync_all_groups_failure(self):
        mock_dir = self.patch_call_CSV_DIR()
        mock_dir.is_dir.return_value = False
        with self.assertRaisesRegex(RuntimeError,"CSV directory not found:"):
            self.gg.sync_all_groups()
            
    
if __name__ == "__main__":
    unittest.main()