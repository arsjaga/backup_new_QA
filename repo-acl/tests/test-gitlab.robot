*** Settings ***

Library  Process
Library  OperatingSystem
Library  Collections

*** Keywords ***
Test directories are initialized
    [Arguments]  ${test_dir}

    Set Test Variable  ${INPUT_DIR}      ${CURDIR}/${test_dir}/input
    Set Test Variable  ${OUTPUT_DIR}     ${CURDIR}/${test_dir}/output
    Set Test Variable  ${EXP_DIR}        ${CURDIR}/${test_dir}/expected
    Set Test Variable  ${PEOPLEDB_DIR}   ${CURDIR}/peopledb

The GitLab database file is prepared
    Create Directory   ${OUTPUT_DIR}
    Copy Directory    ${PEOPLEDB_DIR}/peopledb    ${INPUT_DIR}
    Copy File  ${INPUT_DIR}/gitlab.json  ${OUTPUT_DIR}/gitlab.json

The GitLab database file is prepared with peopledb
    [Arguments]  ${test_dir}
    Create Directory   ${OUTPUT_DIR}
    Copy Directory    ${PEOPLEDB_DIR}/${test_dir}/peopledb    ${INPUT_DIR}
    Copy File  ${INPUT_DIR}/gitlab.json  ${OUTPUT_DIR}/gitlab.json

Execute GitLab Group Synchronization
    [Arguments]  @{dry_run}

    Run Process  coverage  run  --parallel-mode  -m  repo_acl.main  gitlab-groups  --gitlab-url  U  --access-token  X  @{dry_run}
    ...          env:REPO_ACL_GROUPS_DIR=${INPUT_DIR}/groups
    ...          env:FAKE_GITLAB_DB_PATH=${OUTPUT_DIR}/gitlab.json
    ...          env:PEOPLEDB_DIR=${INPUT_DIR}/peopledb
 
GitLab group sync is executed
    Execute GitLab Group Synchronization

GitLab group sync is executed with dry-run
    Execute GitLab Group Synchronization   --dry-run

GitLab group sync is executed with Gitlab server
    Execute GitLab Group Synchronization  --gitlab-url    ${CI_SERVER_URL}

The GitLab output should match the expected result
    Check Files Equal  ${OUTPUT_DIR}/gitlab.json  ${EXP_DIR}/gitlab.json

Check Files Equal
    [Arguments]  ${file1}  ${file2}
    ${c1}=  Get File  ${file1}
    ${c2}=  Get File  ${file2}
    Should be Equal  ${c1}  ${c2}

*** Test Cases ***

Scenario: User synchronization between Git and Gitlab groups
    [Documentation]  REQ001
    Given Test directories are initialized  TST001
    And The GitLab database file is prepared
    When GitLab group sync is executed
    Then The GitLab output should match the expected result

Scenario: Impact on Assigned Issues and Merge Requests
    [Documentation]  REQ002
    Given Test directories are initialized  TST002
    And The GitLab database file is prepared
    When GitLab group sync is executed
    Then The GitLab output should match the expected result

Scenario: Handling Gitlab blocked but Active in People DB
    [Documentation]  REQ003
    Given Test directories are initialized  TST003
    And The GitLab database file is prepared with peopledb  TST003
    When GitLab group sync is executed
    Then The GitLab output should match the expected result

Scenario: Group not present in Gitlab
    [Documentation]  REQ004
    Given Test directories are initialized  TST004
    And The GitLab database file is prepared
    When GitLab group sync is executed
    Then The GitLab output should match the expected result

Scenario: Gitlab parent group not available
    [Documentation]  REQ005
    Given Test directories are initialized  TST005
    And The GitLab database file is prepared
    When GitLab group sync is executed
    Then The GitLab output should match the expected result

Scenario: Execute Gitlab Groups in dry-run mode
    [Documentation]  REQ006
    Given Test directories are initialized  TST006
    And The GitLab database file is prepared
    When GitLab group sync is executed with dry-run
    Then The GitLab output should match the expected result

Scenario: Test Malformed group definition file in Git
    [Documentation]  REQ007
    Given Test directories are initialized  TST007
    And The GitLab database file is prepared
    When GitLab group sync is executed
    Then The GitLab output should match the expected result

Scenario: Git group location not available
    [Documentation]    REQ008
    Given Test directories are initialized  TST008
    And The GitLab database file is prepared
    When GitLab group sync is executed
    Then The GitLab output should match the expected result

# Scenario: Gitlab server accessibility
#     [Documentation]    REQ010
#     Given Test directories are initialized    TST010
#     And The GitLab database file is prepared
#     When GitLab group sync is executed with Gitlab server
#     Then The GitLab output should match the expected result

Scenario: User not found in GitLab but Active in peopledb
    [Documentation]    REQ011
    Given Test directories are initialized  TST011
    And The GitLab database file is prepared with peopledb  TST011
    When GitLab group sync is executed
    Then The GitLab output should match the expected result