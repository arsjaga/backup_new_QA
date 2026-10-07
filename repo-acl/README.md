# repo-acl - Repository Access Control List

## Setup

* `acl.csv` contains access list for groups to projects.

```csv
username,access_level,group_or_project_path,type
@world,developer,org/zc,project
@scrum-masters,developer,org/repo-acl,project
```

## Commands

* `$ repo-acl access --csv acl.csv`
