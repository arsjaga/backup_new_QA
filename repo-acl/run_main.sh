#!/bin/bash
set -e

apt-get update
apt-get install python3 python-is-python3 python3-pip -y
apt-get install ./peopledb.deb
cp -r /usr/share/peopledb/ .
pip install -r requirements.txt --break-system-packages
pip install . --break-system-packages
apt-get update
apt-get install python3 python-is-python3 python3-pip -y
pip install -r requirements.txt --break-system-packages

# export CI_SERVER_URL='https://repo.zilogic.com'
# export GITLAB_RO_ACCESS_TOKEN='Cf63_ZLvTF_oYyuG5pftx286MQp1OjRwCA.01.0y099k3ll'

# export CI_SERVER_URL='http://172.16.48.188'
# export GITLAB_RO_ACCESS_TOKEN='zilogic-test-glpat-9Rzvp_DVmXsdomax2NJaGm86MQp1OjEzCA.01.0y13q9ao8'

export CI_SERVER_URL='http://172.16.48.187:7000'
export GITLAB_RO_ACCESS_TOKEN='glpat-v42VDUo1KJrHhDIc_uXypW86MQp1OnoH.01.0w0hx95ra'

export ZOHO_CLIQ_CLIENT_ID='1000.SP2MC1UYKJ8CCBX9GW0SZZZ1OS6DEB'
export ZOHO_CLIQ_CLIENT_SECRET='53b78c5942c70e86fd1b69bfc02dc175de2e4c915b'
export ZOHO_CLIQ_REFRESH_TOKEN='1000.8cac9ad8f7c7b03a66523fea048c263d.a219ae295fddad47dc674de627bc6cbf'

export ZOHO_MAIL_CLIENT_ID='1000.SP2MC1UYKJ8CCBX9GW0SZZZ1OS6DEB'
export ZOHO_MAIL_CLIENT_SECRET='53b78c5942c70e86fd1b69bfc02dc175de2e4c915b'
export ZOHO_MAIL_REFRESH_TOKEN='1000.239be3227638946d00b84d324f8f81cb.2c1ab46ef5864a876936876684e89b01'
# make dry-run
make update
export PYTHONPATH=$PWD/fake-gitlab
make coverage












# export FAKE_GITLAB_DB_PATH="$CI_PROJECT_DIR/tests/TST001/output/gitlab.json"
# export REPO_ACL_GROUPS_DIR="$CI_PROJECT_DIR/tests/TST001/input/groups"
# pylint -m repo_acl.main gitlab gitlab-groups --dry-run --csv-file=sample.csv --gitlab-url=${CI_SERVER_URL} --access-token=${GITLAB_RO_ACCESS_TOKEN}
# make unit-test
# python3 -m pytest tests \
#   --cov=repo_acl/platforms \
#   --cov-report=term-missing \
#   --cov-report=xml:coverage.xml \
#   --junitxml=report.xml
# export CI_SERVER_URL='https://repo.zilogic1.com'
# echo $PYTHONPATH
# robot -d reports tests
# export COVERAGE_PROCESS_START=$PWD/.coveragerc

# ./run_robot.sh



# 123.176.34.2


# 1000.8957a7cd9d290acd22af16a9dbdde0fb.30b739c0a432d9bdea8f53d69a7af017


# 
# curl -X POST https://accounts.zoho.in/oauth/v2/token \
#         -d "grant_type=authorization_code" \
#         -d "client_id=1000.KIF9STU4HFBHZLP49RHBP1X71B5INR" \
#         -d "client_secret=8519d24262981b49c4d8e57118d5b24a25f2847c48" \
#         -d "code=1000.4888ca09b89dd72add62c4bd35053034.a011c44cb70c62bbca8a1c6625a78f71" 

# curl -X POST "https://accounts.zoho.in/oauth/v2/token" \
#   -d "grant_type=authorization_code" \
#   -d "client_id=1000.SP2MC1UYKJ8CCBX9GW0SZZZ1OS6DEB" \
#   -d "client_secret=53b78c5942c70e86fd1b69bfc02dc175de2e4c915b" \
#   -d "code=1000.c75207dcaf4701510fc3ad5dc01d5e31.4f979b6e2afbe66b9bdfaae1c0125072" \
  # -d "redirect_uri=http://localhost"


# ZohoMail.organization.groups.ALL, ZohoMail.partner.organization.READ




# $env:REPO_ACL_GROUPS_DIR="tests/TST009/input/groups"
# $env:FAKE_GITLAB_DB_PATH="tests/TST009/input/gitlab.json"
# $env:PEOPLEDB_DIR="tests/TST009/input/peopledb.csv"
# $env:PYTHONPATH="$PWD/fake-gitlab"
# python -m repo_acl.main  gitlab-groups  --gitlab-url  http://172.16.48.188  --access-token  X
# python -m repo_acl.main  acl  --csv-file  .\tests\ACL_TST001\input\acl.csv  --gitlab-url  U  --access-token X

python -m repo_acl.main  zoho-cliq  --client-id=${ZOHO_CLIQ_CLIENT_ID} --client-secret=${ZOHO_CLIQ_CLIENT_SECRET} --refresh-token=${ZOHO_CLIQ_REFRESH_TOKEN}
@repo-acl zoho-cliq --client-id=${ZOHO_CLIQ_CLIENT_ID} --client-secret=${ZOHO_CLIQ_CLIENT_SECRET} --refresh-token=${ZOHO_CLIQ_REFRESH_TOKEN}

$env:ZOHO_CLIQ_CLIENT_ID='1000.SP2MC1UYKJ8CCBX9GW0SZZZ1OS6DEB'
$env:ZOHO_CLIQ_CLIENT_SECRET='53b78c5942c70e86fd1b69bfc02dc175de2e4c915b'
$env:ZOHO_CLIQ_REFRESH_TOKEN='1000.8cac9ad8f7c7b03a66523fea048c263d.a219ae295fddad47dc674de627bc6cbf'