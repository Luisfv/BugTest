"""
Exports Issues from a specified repository to a CSV file

Uses basic authentication (Github username + password) to retrieve Issues
from a repository that username has access to. Supports Github API v3.
"""
import csv
import requests
import sys

if len(sys.argv) != 4:
    print "Usage: python export_github_issues.py username password username/repo"
    sys.exit()
args = sys.argv

GITHUB_USER = args[1]
GITHUB_PASSWORD = args[2]
REPO = args[3]
ISSUES_FOR_REPO_URL = 'https://api.github.com/repos/%s/issues' % REPO
AUTH = (GITHUB_USER, GITHUB_PASSWORD)

def write_issues(response):
    "output a list of issues to csv"
    if not r.status_code == 200:
        raise Exception(r.status_code)
    for issue in r.json():
        comments = ""
        comments_list = []
        comments_url = issue['comments_url']
        comments_request = requests.get(comments_url)
        if not comments_request.status_code == 200:
            raise Exception(comments_request.status_code)
        else:
            comments = comments_request.json()
        if comments != "":
            comments_list = get_comments(comments)

        # Select the values from the issue to put into the row
        row = [issue['title'], issue['body'], comments_list]
        csvout.writerow(row)

def get_comments(comments):
    comments_list = []
    for c in comments:
        comment = (c['user']['login'].encode('utf-8'), c['body'].encode('utf-8'))
        comments_list.append(comment)
    return comments_list

r = requests.get(ISSUES_FOR_REPO_URL, auth=AUTH)
csvfile = '%s-issues.csv' % (REPO.replace('/', '-'))
csvout = csv.writer(open(csvfile, 'wb'))
# Edit this to change what values to write
csvout.writerow(('Title', 'Body', 'Comments'))
write_issues(r)

#more pages? examine the 'link' header returned
if 'link' in r.headers:
    pages = dict(
        [(rel[6:-1], url[url.index('<')+1:-1]) for url, rel in
            [link.split(';') for link in
                r.headers['link'].split(',')]])
    while 'last' in pages and 'next' in pages:
        r = requests.get(pages['next'], auth=AUTH)
        write_issues(r)
        if pages['next'] == pages['last']:
            break
