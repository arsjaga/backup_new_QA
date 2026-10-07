*** Settings ***

Library  Process
Library  OperatingSystem
Library  Collections

*** Keywords ***
Test directories are initialized
    [Arguments]  ${test_dir}

    Set Test Variable  ${INPUT_DIR}   ${CURDIR}/${test_dir}/input
    Set Test Variable  ${OUTPUT_DIR}  ${CURDIR}/${test_dir}/output
    Set Test Variable  ${EXP_DIR}     ${CURDIR}/${test_dir}/expected

The GitLab database file is prepared
    Create Directory   ${OUTPUT_DIR}
    Copy File  ${INPUT_DIR}/gitlab.json  ${OUTPUT_DIR}/gitlab.json

Execute ACL GitLab Group Synchronization
    [Arguments]  @{dry_run}

    Run Process  coverage  run  --parallel-mode  -m  repo_acl.main  acl  --csv-file  ${INPUT_DIR}/acl.csv  --gitlab-url  U  --access-token  X   @{dry_run}
    ...    env:FAKE_GITLAB_DB_PATH=${OUTPUT_DIR}/gitlab.json

ACL Git group sync is executed
    Execute ACL GitLab Group Synchronization

ACL GitL group sync is executed with dry-run
    Execute ACL GitLab Group Synchronization   --dry-run

The GitLab output should match the expected result
    Check Files Equal  ${OUTPUT_DIR}/gitlab.json  ${EXP_DIR}/gitlab.json

Check Files Equal
    [Arguments]  ${file1}  ${file2}
    ${c1}=  Get File  ${file1}
    ${c2}=  Get File  ${file2}
    Should be Equal  ${c1}  ${c2}

*** Test Cases ***

Scenario: Groups in `acl_file` not shared with GitLab project
    [Documentation]  ACL_REQ001
    Given Test directories are initialized  ACL_TST001
    And The GitLab database file is prepared
    When ACL Git group sync is executed
    Then The GitLab output should match the expected result

Scenario: Groups specified in the `acl_file` with an access level of no-access
    [Documentation]  ACL_REQ002
    Given Test directories are initialized  ACL_TST002
    And The GitLab database file is prepared
    When ACL Git group sync is executed
    Then The GitLab output should match the expected result

Scenario: Invalid data in `acl_file`
    [Documentation]  ACL_REQ003
    Given Test directories are initialized  ACL_TST003
    And The GitLab database file is prepared
    When ACL Git group sync is executed
    Then The GitLab output should match the expected result

Scenario: The `acl_file` not available
    [Documentation]  ACL_REQ004
    Given Test directories are initialized  ACL_TST004
    And The GitLab database file is prepared
    When ACL Git group sync is executed
    Then The GitLab output should match the expected result

Scenario: Groups already in `shared_with_groups`
    [Documentation]  ACL_REQ005
    Given Test directories are initialized  ACL_TST005
    And The GitLab database file is prepared
    When ACL Git group sync is executed
    Then The GitLab output should match the expected result

Scenario: Dry run execution in acl
    [Documentation]  ACL_REQ006
    Given Test directories are initialized  ACL_TST006
    And The GitLab database file is prepared
    When ACL GitL group sync is executed with dry-run
    Then The GitLab output should match the expected result