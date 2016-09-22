"""
Exports Issues from a specified repository to a CSV file

Uses basic authentication (Github username + password) to retrieve Issues
from a repository that username has access to. Supports Github API v3.
"""
import csv
import requests
import sys
import getpass
import time

if len(sys.argv) != 3:
    print "Usage: python export_github_issues.py username username/repo"
    sys.exit()
args = sys.argv

GITHUB_USER = args[1]
GITHUB_PASSWORD = getpass.getpass()
REPO = args[2]
ISSUES_FOR_REPO_URL = 'https://api.github.com/repos/%s/issues' % REPO
AUTH = (GITHUB_USER, GITHUB_PASSWORD)
REQUEST_COUNT = 0
REQUESTS_REMAINING = requests.get("https://api.github.com/rate_limit", auth=AUTH).json()['rate']['remaining']
WAIT_TIME = 0

def write_issues(response):
    "output a list of issues to csv"
    global REQUEST_COUNT
    if not response.status_code == 200:
        raise Exception(response.status_code)
    for issue in response.json():
        comments = ""
        comments_list = []
        comments_url = issue['comments_url'].encode('utf-8')
        comments_request = requests.get(comments_url, auth=AUTH)
        time.sleep(WAIT_TIME)
        REQUEST_COUNT += 1
        if not comments_request.status_code == 200:
            raise Exception(comments_request.status_code)
        else:
            comments = comments_request.json()
        if comments != "":
            comments_list = get_comments(comments)
        all_comments = "\n".join(comments_list)
        params = issue['url'][29:].encode('utf-8')
        issue_url = "https://github.com/" +  params
        # Select the values from the issue to put into the row
        row = [issue['title'].encode('utf-8'), issue['body'].encode('utf-8'), all_comments, issue_url]
        csvout.writerow(row)

def get_comments(comments):
    comments_list = []
    for c in comments:
        comment = c['user']['login'].encode('utf-8') + ": " + c['body'].encode('utf-8')
        comments_list.append(comment)
    return comments_list

r = requests.get(ISSUES_FOR_REPO_URL, auth=AUTH)
time.sleep(WAIT_TIME)
REQUEST_COUNT += 1
csvfile = '%s-issues.csv' % (REPO.replace('/', '-'))
csvout = csv.writer(open(csvfile, 'wb'))
# Edit this to change what values to write
csvout.writerow(('Title', 'Body', 'Comments', 'URL'))
write_issues(r)

#more pages? examine the 'link' header returned
# if 'link' in r.headers:
#     pages = dict(
#         [(rel[6:-1], url[url.index('<')+1:-1]) for url, rel in
#             [link.split(';') for link in
#                 r.headers['link'].split(',')]])
#     while 'last' in pages and 'next' in pages:
#         r = requests.get(pages['next'], auth=AUTH)
#         write_issues(r)
#         if pages['next'] == pages['last']:
#             break

if 'link' in r.headers:
    pages = dict(
        [(rel[6:-1], url[url.index('<')+1:-1]) for url, rel in
            [link.split(';') for link in
                r.headers['link'].split(',')]])

    while 'last' in pages and 'next' in pages:
        r = requests.get(pages['next'], auth=AUTH)
        time.sleep(WAIT_TIME)
        REQUEST_COUNT += 1
        write_issues(r)
        # if REQUEST_COUNT > 500:
        #     print "Request limit. Stopping..."
        #     break
        if pages['next'] == pages['last']:
            break
        pages = dict(
        [(rel[6:-1], url[url.index('<')+1:-1]) for url, rel in
            [link.split(';') for link in
                r.headers['link'].split(',')]])
print REQUEST_COUNT
