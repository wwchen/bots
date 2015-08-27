#!/usr/bin/env python

import time
import ConfigParser
from jira import JIRA
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
        self._slack_users = []

    def start(self):
        # connect to jira
        jira = JIRA(server=self._jira_hostname, basic_auth=(self._jira_username, self._jira_password))
        print "Connected to Jira"

        # connect to slack
        slack = SlackClient(self._slack_api_token)
        self._slack_users = fetch_slack_users(slack)
        # print [str(m) for m in self._slack_users]

        if slack.rtm_connect():
            print "Connected to Slack"
            while True:
                events = slack.rtm_read()
                for event in events:
                    print event
                    issue = self._parse_event(event)
                    if issue:
                        # self._parse_slack_user(issue, self._slack_users)
                        jira.create_issue(fields={
                            'project': {'key': 'SNOW'},
                            'summary': issue.text,
                            'description': issue.summary,
                            'issuetype': {'name': issue.type.name}
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

        user = event["user"]
        text = event["text"]
        summary = ""

        file_shared = "file_share" == event["subtype"] if "subtype" in event else None
        if file_shared:
            # https://api.slack.com/types/file
            text = event["file"]["title"]
            summary = event["file"]["url_private"]

        # determine if the text highlighted someone on slack
        text, slack_user = remove_slack_user_markup(text, self._slack_users)
        if slack_user:
            print "Slack user found: {}".format(slack_user)
            print "Text:", text

        # determine if the text is a bug
        if is_issue(text):
            return Issue(text, summary)

    def _parse_slack_user(self, issue, slack_users):
        slack_user, substring = remove_slack_user_markup(issue.text, slack_users)
        if slack_user:
            # todo mapping
            issue.text = issue.text.replace(substring, '')


if __name__ == '__main__':
    bot = JiraBot("../config/jirabot.conf")
    bot.start()
