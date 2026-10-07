VERSION ?= 1.0
PACKAGE_NAME = repo-acl
CSV_FILE ?= sample.csv
COVERAGE_FILES = repo_acl/*.py


dry-run:
	@repo-acl gitlab-groups --dry-run --gitlab-url=${CI_SERVER_URL} --access-token=${GITLAB_RO_ACCESS_TOKEN}
	@repo-acl acl --dry-run --csv-file=${CSV_FILE} --gitlab-url=${CI_SERVER_URL} --access-token=${GITLAB_RO_ACCESS_TOKEN}
	@repo-acl zoho-cliq --dry-run --client-id=${ZOHO_CLIQ_CLIENT_ID} --client-secret=${ZOHO_CLIQ_CLIENT_SECRET} --refresh-token=${ZOHO_CLIQ_REFRESH_TOKEN}
	@repo-acl zoho-mail --dry-run --client-id=${ZOHO_MAIL_CLIENT_ID} --client-secret=${ZOHO_MAIL_CLIENT_SECRET} --refresh-token=${ZOHO_MAIL_REFRESH_TOKEN}

update:
	@repo-acl gitlab-groups --gitlab-url=${CI_SERVER_URL} --access-token=${GITLAB_RO_ACCESS_TOKEN}
# 	@repo-acl acl --csv-file=${CSV_FILE} --gitlab-url=${CI_SERVER_URL} --access-token=${GITLAB_ACCESS_TOKEN}
# 	@repo-acl zoho-cliq --client-id=${ZOHO_CLIQ_CLIENT_ID} --client-secret=${ZOHO_CLIQ_CLIENT_SECRET} --refresh-token=${ZOHO_CLIQ_REFRESH_TOKEN}
# 	@repo-acl zoho-mail --client-id=${ZOHO_MAIL_CLIENT_ID} --client-secret=${ZOHO_MAIL_CLIENT_SECRET} --refresh-token=${ZOHO_MAIL_REFRESH_TOKEN}

unit-test:
	python3 -m pytest tests -v

build:
	mkdir -p build
	python3 -m build
	pip install dist/*.whl --root build --prefix /usr

deb: build
	fpm -s dir -t deb \
		--maintainer it-support@zilogic.com	\
		-n $(PACKAGE_NAME)    \
		-v $(VERSION)         \
		--prefix=/            \
		-C build              \
		-a noarch             \
		-d python3            \
		-d python3-requests   \
		-d python3-gitlab     \
		.

coverage:
	coverage erase
	@coverage run -m robot -v CI_SERVER_URL:"$(CI_SERVER_URL)" -d reports tests/
	coverage combine
	coverage report -m --include="$(COVERAGE_FILES)"
	coverage html --include="$(COVERAGE_FILES)"

clean:
	rm -rf build
	rm -rf *.egg-info *.deb
	rm -rf dist/
	rm -rf htmlcov
	rm -rf reports
	rm -rf tests/*/output
	rm -rf tests/*/input/peopledb