import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import requests
from repo_acl.platforms.zoho_cliq import ZohoCliqGroups, run, register

class TestSetUp(unittest.TestCase):
    
    def setUp(self):
        self.zc = ZohoCliqGroups(
            client_id="test_id",
            client_secret="test_secret",
            refresh_token="test_refresh_token",
            dryrun=False
        )

    def patch_call_function(self,func_name):
        patcher = patch.object(ZohoCliqGroups,func_name)
        mock_func = patcher.start()
        self.addCleanup(patcher.stop)
        return mock_func

    def patch_call_list_dir(self):
        patcher = patch("os.listdir")
        mock_list_dir = patcher.start()
        self.addCleanup(patcher.stop)
        return mock_list_dir

    def patch_call_open_file(self,data):
        patcher = patch("builtins.open", new_callable=mock_open, read_data=data)
        mock_open_file = patcher.start()
        self.addCleanup(patcher.stop)
        return mock_open_file

    def patch_call_requests(self,value):
        patcher = patch(f"repo_acl.platforms.zoho_cliq.requests.{value}")
        mock_request = patcher.start()
        self.addCleanup(patcher.stop)
        return mock_request

class TestZohoCliqDryRun(TestSetUp):

    def dry_run_true(self):
        self.zc.dry_run = True
        return
    
    def dry_run_false(self):
        self.zc.dry_run = False
        return

    def test_renew_access_token_dry_run(self):
        self.dry_run_true()
        with patch("builtins.print") as mock_print:
            self.zc.renew_access_token()
            mock_print.assert_any_call("[DRY-RUN] Would renew access token")
        self.assertEqual(self.zc.access_token,"DRY_RUN_TOKEN")
        self.dry_run_false()

    def test_find_channel_id_by_name_dry_run(self):
        self.dry_run_true()
        with patch("builtins.print") as mock_print:
            channel_id = self.zc.find_channel_id_by_name("user")
            mock_print.assert_any_call("[DRY-RUN] Would lookup channel: user")
            self.assertEqual(channel_id,"DRY_RUN_CHANNEL_ID")
        self.dry_run_false()

    def test_fetch_channel_member_emails_dry_run(self):
        self.dry_run_true()
        with patch("builtins.print") as mock_print:
            self.zc.fetch_channel_member_emails("11")
            mock_print.assert_any_call("[DRY-RUN] Would fetch members for channel 11")
        self.dry_run_false()

    def test_remove_users_dry_run(self):
        self.dry_run_true()
        with patch("builtins.print") as mock_print:
            self.zc.remove_users("11",{"user1@email.com"})
            mock_print.assert_any_call("[DRY-RUN] Would remove 1 users from 11")
        self.dry_run_false()

    def test_sync_members_dry_run(self):
        mock_emails = self.patch_call_function(func_name="fetch_channel_member_emails")
        mock_remove_usr = self.patch_call_function(func_name="remove_users")
        self.dry_run_true()
        mock_emails.return_value = {"user1@email.com","user2@email.com"}
        with patch("builtins.print") as mock_print:
            self.zc.sync_members("11",{"name1@email.com","user2@email.com"})
            mock_print.assert_any_call("[DRY-RUN] Would add 1 users to 11")
        mock_emails.assert_called_once()
        mock_remove_usr.assert_called_once()

class TestZohoCliqActual(TestSetUp):        
    
    def test_register(self):
        mock_parser = MagicMock()
        mock_chiled_parser = mock_parser.add_parser.return_value
        register(mock_parser)
        mock_parser.add_parser.assert_called_with(
            "zoho-cliq",
            help="Zoho Cliq operations"
        )
        mock_chiled_parser.add_argument.assert_any_call("--client-id", required=True)
        mock_chiled_parser.add_argument.assert_any_call("--client-secret", required=True)
        mock_chiled_parser.add_argument.assert_any_call("--refresh-token", required=True)
        mock_chiled_parser.add_argument.assert_any_call("--dry-run", action="store_true")

    def test_run(self):
        mock_sync_group = self.patch_call_function(func_name="sync_groups_from_csv")
        args = MagicMock()
        args.client_id = "test_id"
        args.client_secret = "test_secret"
        args.refresh_token = "test_refresh_token"
        args.dry_run = False
        run(args)
        mock_sync_group.assert_called_once()

    def test_read_groups_success(self):
        mock_open_file = self.patch_call_open_file(data="name,users")
        mock_list_dir = self.patch_call_list_dir()
        mock_list_dir.return_value = ["file.csv"]
        group = self.zc.read_groups()
        mock_list_dir.assert_called_once_with("./groups")
        mock_open_file.assert_called_once_with(os.path.join("./groups", "file.csv"))
        self.assertEqual(group[0].get("name"),"file")
        self.assertIn("name@zilogic.com",group[0].get("users"))

    def test_read_groups_failure(self):
        self.patch_call_open_file(data="   ,   ")
        mock_list_dir = self.patch_call_list_dir()
        mock_list_dir.return_value = ["file.csv"]
        with self.assertRaisesRegex(Exception,"User not found."):
            self.zc.read_groups()
        
    def test_find_channel_id_by_name_success(self):
        mock_get = self.patch_call_requests(value="get")
        mock_header = self.patch_call_function(func_name="headers")
        mock_response = MagicMock()
        mock_response.json.return_value = {"channels":[{"name":"#user","channel_id":"123"}]}
        mock_get.return_value = mock_response
        channel_id = self.zc.find_channel_id_by_name("user")
        self.assertEqual(channel_id,"123")
        mock_header.assert_called_once()

    def test_find_channel_id_by_name_failure(self):
        mock_get = self.patch_call_requests(value="get")
        mock_header = self.patch_call_function(func_name="headers")
        mock_response = MagicMock()
        mock_response.json.return_value = {"channels":[{"name":"#user","channel_id":"123"}]}
        mock_get.return_value = mock_response
        channel_id = self.zc.find_channel_id_by_name("#user")
        self.assertEqual(channel_id,None)
        mock_header.assert_called_once()

    def test_headers_success(self):
        mock_token = self.patch_call_function(func_name="renew_access_token")
        def mock_logic():
            self.zc.access_token = "asdfghjkl"
        mock_token.side_effect = mock_logic
        header_data = self.zc.headers()
        self.assertEqual(header_data.get("Authorization"),"Zoho-oauthtoken asdfghjkl")
        mock_token.assert_called_once()

    def test_headers_failure(self):
        mock_token = self.patch_call_function(func_name="renew_access_token")
        header_data = self.zc.headers()
        self.assertEqual(header_data.get("Authorization"),"Zoho-oauthtoken None")
        mock_token.assert_called_once()

    def test_renew_access_token_success(self):
        mock_post = self.patch_call_requests(value="post")
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token":"asdfghjkl","status code": "401"}
        mock_post.return_value = mock_response
        self.zc.renew_access_token()
        self.assertEqual(self.zc.access_token,"asdfghjkl")

    def test_fetch_channel_member_emails(self):
        mock_get = self.patch_call_requests(value="get")
        mock_header = self.patch_call_function(func_name="headers")
        mock_response = MagicMock()
        mock_response.json.return_value = {"members":[{"email_id":"user1@email.com"}]}
        mock_get.return_value = mock_response
        emails = self.zc.fetch_channel_member_emails("101")
        self.assertIn("user1@email.com",emails)
        mock_header.assert_called_once()

    def test_remove_users_success(self):
        mock_delete = self.patch_call_requests(value="delete")
        mock_header = self.patch_call_function(func_name="headers")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response
        with patch("builtins.print") as mock_print:
            self.zc.remove_users("11",{"user1@email.com"})
            mock_print.assert_any_call("Removed 1 users")
        mock_header.assert_called_once()

    def test_remove_users_failure(self):
        mock_delete = self.patch_call_requests(value="delete")
        mock_header = self.patch_call_function(func_name="headers")
        mock_response = MagicMock()
        mock_response.text = "Error"
        mock_response.status_code = 400
        mock_delete.return_value = mock_response
        with patch("builtins.print") as mock_print:
            self.zc.remove_users("11",{"user1@email.com"})
            mock_print.assert_any_call("Remove failed:","Error")
        mock_header.assert_called_once()

    def test_remove_users_without_emails(self):
        with patch("builtins.print") as mock_print:
            self.zc.remove_users("11",{})
            mock_print.assert_any_call("Emails not found.")

    def test_sync_members_success(self):
        mock_post = self.patch_call_requests(value="post")
        mock_mails = self.patch_call_function(func_name="fetch_channel_member_emails")
        mock_remove_usr = self.patch_call_function(func_name="remove_users")
        mock_mails.return_value = {"user1@email.com","user2@email.com"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        with patch("builtins.print") as mock_print:
            self.zc.sync_members("123",{"name1@email.com","user2@email.com"})
            mock_print.assert_any_call("Added 1 users")
        mock_mails.assert_called_once()
        mock_remove_usr.assert_called_once()

    def test_sync_members_failuer(self):
        mock_post = self.patch_call_requests(value="post")
        mock_mails = self.patch_call_function(func_name="fetch_channel_member_emails")
        mock_remove_usr = self.patch_call_function(func_name="remove_users")
        mock_mails.return_value = {"user1@email.com","user2@email.com"}
        mock_response = MagicMock()
        mock_response.text = "Error"
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        with patch("builtins.print") as mock_print:
            self.zc.sync_members("123",{"name1@email.com","user2@email.com"})
            mock_print.assert_any_call("Add failed:","Error")
        mock_mails.assert_called_once()
        mock_remove_usr.assert_called_once()

    def test_sync_groups_from_csv_success(self):
        mock_read_groups = self.patch_call_function(func_name="read_groups")
        mock_channel_id = self.patch_call_function(func_name="find_channel_id_by_name")
        mock_sync_members = self.patch_call_function(func_name="sync_members")
        mock_read_groups.return_value = [{"name":"group1","users":"user1"}]
        mock_channel_id.return_value = "123"
        self.zc.sync_groups_from_csv()
        mock_read_groups.assert_called_once()
        mock_channel_id.assert_called_once()
        mock_sync_members.assert_called_once()

    def test_sync_groups_from_csv_failure(self):
        mock_read_groups = self.patch_call_function(func_name="read_groups")
        mock_channel_id = self.patch_call_function(func_name="find_channel_id_by_name")
        mock_read_groups.return_value = [{"name":"group1","users":"user1"}]
        mock_channel_id.return_value = None
        with patch("builtins.print") as mock_print:    
            self.zc.sync_groups_from_csv()
            mock_print.assert_any_call("Channel name not found: group1")
        mock_read_groups.assert_called_once()
        mock_channel_id.assert_called_once()
        

if __name__ == "__main__":
    unittest.main()