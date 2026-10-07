import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import requests
from repo_acl.platforms.zoho_mail import ZohoMailGroup, run, register

class TestSetUp(unittest.TestCase):
    
    def setUp(self):
        self.zm = ZohoMailGroup(
            client_id="test_id",
            client_secret="test_secret",
            refresh_token="test_refresh_token",
            dryrun=False
        )

    def patch_call_function(self,func_name):
        patcher = patch.object(ZohoMailGroup,func_name)
        mock_value = patcher.start()
        self.addCleanup(patcher.stop)
        return mock_value
    
    def patch_call_requests(self,key_data):
        patcher = patch(f"repo_acl.platforms.zoho_mail.requests.{key_data}")
        mock_key_value = patcher.start()
        self.addCleanup(patcher.stop)
        return mock_key_value
    
    def patch_call_list_dir(self):
        patcher = patch("os.listdir")
        mock_dir = patcher.start()
        self.addCleanup(patcher.stop)
        return mock_dir
    
    def patch_call_file_open(self,data):
        patcher = patch("builtins.open", new_callable=mock_open, read_data=data)
        mock_file_open = patcher.start()
        self.addCleanup(patcher.stop)
        return mock_file_open
        
class TestZohoMailDryRun(TestSetUp):
        
    def test_get_org_id_dry_run(self):
        mock_get = self.patch_call_requests(key_data="get")
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"zoid": "123"}, "status": {"code": 200}}
        mock_get.return_value = mock_response
        self.zm.dry_run = True
        zoid = self.zm.get_org_id()
        self.assertEqual(zoid,"DRY_RUN_ORG_ID")
        self.zm.dry_run = False

    def test_renew_access_token_dry_run(self):
        mock_post = self.patch_call_requests(key_data="post")
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "fake token"}
        mock_post.return_value = mock_response
        self.zm.dry_run = True
        self.zm.renew_access_token()
        self.assertEqual(self.zm.headers.get("Authorization"),"Zoho-oauthtoken DRY_RUN_TOKEN")
        self.zm.dry_run = False

    def test_get_group_id_dry_run(self):
        mock_get = self.patch_call_requests(key_data="get")
        org_id = self.patch_call_function(func_name="get_org_id")
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"groups": [{"emailId":"ex@gmail.com","zgid":"1234"}]}}
        mock_get.return_value = mock_response
        self.zm.dry_run = True
        value = self.zm.get_group_id(group_email = "ex@gmail.com")
        self.assertEqual(value,123456789)
        org_id.assert_called_once()
        self.zm.dry_run = False
    
    def test_add_users_to_group_dry_run(self):
        mock_put = self.patch_call_requests(key_data="put")
        re_acc_token = self.patch_call_function(func_name="renew_access_token")
        group_id = self.patch_call_function(func_name="get_group_id")
        group_id.return_value = 123
        self.zm.group_data=[{"group_name": "group_name",
                        "group_email": "group_email",
                        "group_users": ["user1","user2"]}]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"mode": "addMailGroupMember",
                "mailGroupMemberList": [
                    {"memberEmailId": "group_user", "role": "member"} 
                ],}
        mock_put.return_value = mock_response
        self.zm.dry_run = True
        with patch("builtins.print") as mock_print:
            self.zm.add_users_to_group()
            mock_print.assert_any_call("[DRY-RUN] Would add users to group_name (123)")
        re_acc_token.assert_called_once()
        group_id.assert_called_once()
        self.zm.dry_run = False
    
class TestZohoMailActual(TestSetUp):  
    
    def test_register(self):
        mock_parser = MagicMock()
        mock_child_parser = mock_parser.add_parser.return_value
        register(mock_parser)
        mock_parser.add_parser.assert_called_with(
            "zoho-mail",
            help="Zoho Mail operations"
        )
        mock_child_parser.add_argument.assert_any_call("--client-id", required=True)
        mock_child_parser.add_argument.assert_any_call("--client-secret", required=True)
        mock_child_parser.add_argument.assert_any_call("--refresh-token", required=True)
        mock_child_parser.add_argument.assert_any_call("--dry-run", action="store_true")

    def test_run(self):
        mock_get_data = self.patch_call_function(func_name="get_users_groups_data")
        mock_add_users = self.patch_call_function(func_name="add_users_to_group")
        args = MagicMock()
        args.client_id = "test_id"
        args.client_secret = "test_secret"
        args.refresh_token = "test_refresh_token"
        args.dry_run = False
        run(args)
        mock_get_data.assert_called_once()
        mock_add_users.assert_called_once()

    def test_get_user_groups_data_success(self):
        mock_listdir = self.patch_call_list_dir()
        mock_open_file = self.patch_call_file_open(data="user_name,user_email,group_users")
        mock_listdir.return_value = ["test.csv"]
        self.zm.get_users_groups_data()
        mock_listdir.assert_called_once_with("./groups")
        mock_open_file.assert_called_once_with(os.path.join("./groups", "test.csv"), "r")
        self.assertEqual(self.zm.group_data[0].get("group_users")[0],"username@gowtham.work.gd")
    
     
    def test_get_user_groups_data_failure(self):
        mock_listdir = self.patch_call_list_dir()
        self.patch_call_file_open(data="  ,  ,  ")
        mock_listdir.return_value = ["test1.csv"]
        with self.assertRaisesRegex(Exception,"Group user not found."):
            self.zm.get_users_groups_data()

    def test_renew_access_token_success(self):
        mock_post = self.patch_call_requests(key_data="post")
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "fake token"}
        mock_post.return_value = mock_response
        self.zm.renew_access_token()
        self.assertEqual(self.zm.headers.get("Authorization"),"Zoho-oauthtoken fake token")

    def test_renew_access_token_response_failure(self):
        mock_post = self.patch_call_requests(key_data="post")
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.ok = False
        mock_response.json.return_value = {"access_token": "fake token"}
        mock_post.return_value = mock_response
        with self.assertRaisesRegex(Exception,"Token refresh failed"):
            self.zm.renew_access_token()
        
    def test_renew_access_token_data_failure(self):
        mock_post = self.patch_call_requests(key_data="post")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"no_token": "fake token"}
        mock_post.return_value = mock_response
        with self.assertRaisesRegex(Exception,"Invalid token response"):
            self.zm.renew_access_token()

    def test_get_org_id_success(self):
        mock_get = self.patch_call_requests(key_data="get")
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"zoid": "123"}, "status": {"code": 200}}
        mock_get.return_value = mock_response
        zoid = self.zm.get_org_id()
        self.assertEqual(zoid,"123")

    def test_get_org_id_response_failure(self):
        mock_get = self.patch_call_requests(key_data="get")
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.ok = False
        mock_response.json.return_value = {"data": {"zoid": "123"}}
        mock_get.return_value = mock_response
        with self.assertRaisesRegex(Exception,"Failed to fetch organization ID:"):
            self.zm.get_org_id()
        
    def test_get_org_id_data_failure(self):
        mock_get = self.patch_call_requests(key_data="get")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        with self.assertRaisesRegex(Exception,"No organization data found."):
            self.zm.get_org_id()

    def test_get_org_id_zoid_failure(self):
        mock_get = self.patch_call_requests(key_data="get")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"data":{"key":"value"}}
        mock_get.return_value = mock_response
        with self.assertRaisesRegex(Exception,"Organization ID \\(zoid\\) not found."):
            self.zm.get_org_id()
   
    def test_get_group_id_success(self):
        mock_get = self.patch_call_requests(key_data="get")
        org_id = self.patch_call_function(func_name="get_org_id")
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"groups": [{"emailId":"ex@gmail.com","zgid":"1234"}]}}
        mock_get.return_value = mock_response
        value = self.zm.get_group_id(group_email = "ex@gmail.com")
        self.assertEqual(value,"1234")
        org_id.assert_called_once()
    
    def test_get_group_id_response_failure(self):
        mock_get = self.patch_call_requests(key_data="get")
        org_id = self.patch_call_function(func_name="get_org_id")
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.ok = False
        mock_response.json.return_value = {"data": {"groups": [{"emailId":"ex@gmail.com","zgid":"1234"}]}}
        mock_get.return_value = mock_response
        with self.assertRaisesRegex(Exception,"Failed to fetch groups:"):
            self.zm.get_group_id(group_email = "ex@gmail.com")

        org_id.assert_called_once()
   
    def test_get_group_id_data_failure(self):
        mock_get = self.patch_call_requests(key_data="get")
        org_id = self.patch_call_function(func_name="get_org_id")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"information": {"groups": [{"emailId":"ex@gmail.com","zgid":"1234"}]}}
        mock_get.return_value = mock_response
        with self.assertRaisesRegex(Exception,"Group not found:"):
            self.zm.get_group_id(group_email = "ex@gmail.com")
        
        org_id.assert_called_once()

    def test_add_users_to_group_success(self):
        mock_put = self.patch_call_requests(key_data="put")
        re_acc_token = self.patch_call_function(func_name="renew_access_token")
        group_id = self.patch_call_function(func_name="get_group_id")
        org_id = self.patch_call_function(func_name="get_org_id")
        self.zm.group_data=[{"group_name": "group_name",
                        "group_email": "group_email",
                        "group_users": ["user1","user2"]}]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"mode": "addMailGroupMember",
                "mailGroupMemberList": [
                    {"memberEmailId": "group_user", "role": "member"} 
                ],}
        mock_put.return_value = mock_response
        with patch("builtins.print") as mock_print:
            self.zm.add_users_to_group()
            mock_print.assert_any_call("[group_name] Users added successfully")
        re_acc_token.assert_called_once()
        group_id.assert_called_once()
        org_id.assert_called_once()
        
    def test_add_users_to_group_data_failure(self):
        re_acc_token = self.patch_call_function(func_name="renew_access_token")
        self.zm.group_data=[{"group_name": "group_name",
                        "group_email": "group_email",
                        "group_users": []}]
        
        with patch("builtins.print") as mock_print:
            self.zm.add_users_to_group()
            mock_print.assert_any_call("No users found, skipping")
        
        re_acc_token.assert_called_once()
        
    def test_add_users_to_group_zgid_failure(self):
        re_acc_token = self.patch_call_function(func_name="renew_access_token")
        group_id = self.patch_call_function(func_name="get_group_id")
        group_id.side_effect = Exception("mock_exception")
        self.zm.group_data=[{"group_name": "group_name",
                        "group_email": "group_email",
                        "group_users": ["user1","user2"]}]
        
        with patch("builtins.print") as mock_print:
            self.zm.add_users_to_group()
            mock_print.assert_any_call("[group_name] Group does not exist or error fetching ID: mock_exception")
        
        re_acc_token.assert_called_once()
        group_id.assert_called_once()
        
    def test_add_users_to_group_response_failure(self):
        mock_put = self.patch_call_requests(key_data="put")
        re_acc_token = self.patch_call_function(func_name="renew_access_token")
        group_id = self.patch_call_function(func_name="get_group_id")
        org_id = self.patch_call_function(func_name="get_org_id")
        self.zm.group_data=[{"group_name": "group_name",
                        "group_email": "group_email",
                        "group_users": ["user1","user2"]}]
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"mode": "addMailGroupMember",
                "mailGroupMemberList": [
                    {"memberEmailId": "group_user", "role": "member"} 
                ],}
        mock_put.return_value = mock_response
        with patch ("builtins.print") as mock_print:
            self.zm.add_users_to_group()
            mock_print.assert_any_call("[group_name] Failed to add users: {'mode': 'addMailGroupMember', 'mailGroupMemberList': [{'memberEmailId': 'group_user', 'role': 'member'}]}")
        re_acc_token.assert_called_once()
        group_id.assert_called_once()
        org_id.assert_called_once()

if __name__ == '__main__':
    unittest.main()