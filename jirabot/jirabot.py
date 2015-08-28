#!/usr/bin/env python

import time
import ConfigParser
from jira import JIRA, JIRAError
from slackclient import SlackClient
from JiraIssue import *
from SlackUser import *


class JiraBot:
    CONFIG_KEY_SLACK = "Slack"
    CONFIG_KEY_JIRA = "JIRA"

    # todo get user info, map to jira
    def __init__(self, config_file):
        config = ConfigParser.ConfigParser()
        config.read(config_file)
        self._slack_api_token = config.get(self.CONFIG_KEY_SLACK, "api token")
        self._jira_hostname = config.get(self.CONFIG_KEY_JIRA, "hostname")
        self._jira_username = config.get(self.CONFIG_KEY_JIRA, "username")
        self._jira_password = config.get(self.CONFIG_KEY_JIRA, "password")
        self._jira_project = config.get(self.CONFIG_KEY_JIRA, "project")
        self._jira_users = []
        self._slack_users = []

    def start(self):
        # connect to jira
        jira = JIRA(server=self._jira_hostname, basic_auth=(self._jira_username, self._jira_password))
        self._jira_users = jira.search_assignable_users_for_issues('', self._jira_project)
        print [m.emailAddress for m in self._jira_users]
        print "Connected to Jira"

        # connect to slack
        slack = SlackClient(self._slack_api_token)
        self._slack_users = fetch_slack_users(slack)
        print [str(m) for m in self._slack_users]

        if slack.rtm_connect():
            print "Connected to Slack"
            while True:
                events = slack.rtm_read()
                for event in events:
                    print event
                    issue = self._parse_event(event)
                    if issue:
                        jira.create_issue(fields={
                            'project': {'key': 'SNOW'},
                            'summary': issue.text,
                            'description': issue.summary,
                            'issuetype': {'name': issue.type.name},
                            'assignee': {'name': issue.assignee}

                        })
                time.sleep(1)
        else:
            print "Connection failed. Invalid API token?"

    def _parse_event(self, event):
        if 'type' not in event or \
                        'user' not in event or \
                        'text' not in event:
            return None

        if 'message' != event['type']:
            return None

        print "========"

        # todo need to normalize/sanitize input data
        user = event["user"]
        text = event["text"]
        summary = ""
        assignee = None

        file_shared = "file_share" == event["subtype"] if "subtype" in event else None
        if file_shared:
            # https://api.slack.com/types/file
            text = event["file"]["title"]
            summary = event["file"]["url_private"]

        # determine if the text highlighted someone on slack
        text, slack_user = remove_slack_user_markup(text, self._slack_users)
        print "Text:", text
        if slack_user:
            print "Slack user found: {}".format(slack_user)
            # link to jira user, by email
            for jira_user in self._jira_users:
                if jira_user.emailAddress == slack_user.email:
                    print "Found matching Jira user: {}".format(jira_user.key)
                    assignee = jira_user.key

        # determine if the text is a bug
        if is_issue(text):
            issue = Issue(text, summary, assignee)
            print issue
            print "========"
            return issue
        print "========"

if __name__ == '__main__':
    bot = JiraBot("../config/jirabot.conf")
    while True:
        try:
            bot.start()
        except JIRAError as e:
            print "Restarting because of error: " + e
        except UnicodeEncodeError as e:
            print "Submitting the bug failed: " + e
        except KeyboardInterrupt:
            print "Caught keyboard interrupt. Exiting"
            break
