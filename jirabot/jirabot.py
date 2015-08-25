#!/usr/bin/env python
import base64

import time
import ConfigParser
from jira import JIRA
from slackclient import SlackClient

class JiraBot:
    CONFIG_KEY_SLACK = "Slack"
    CONFIG_KEY_JIRA = "JIRA"

    # todo get user info, map to jira
    #
    def __init__(self, config_file):
        config = ConfigParser.ConfigParser()
        config.read(config_file)
        self._slack_api_token = config.get(self.CONFIG_KEY_SLACK, "api token")
        self._jira_hostname = config.get(self.CONFIG_KEY_JIRA, "hostname")
        self._jira_username = config.get(self.CONFIG_KEY_JIRA, "username")
        self._jira_password = config.get(self.CONFIG_KEY_JIRA, "password")

    def start(self):
        # connect to jira
        jira = JIRA(server=self._jira_hostname, basic_auth=(self._jira_username, self._jira_password))
        print "Connected to Jira"

        # connect to slack
        client = SlackClient(self._slack_api_token)
        if client.rtm_connect():
            print "Connected to Slack"
            while True:
                events = client.rtm_read()
                for bug in self._parse_events(events):
                    jira.create_issue(fields={
                        'project': {'key': 'SNOW'},
                        'summary': bug.text,
                        'description': bug.summary,
                        'issuetype': {'name': 'Bug'}
                    })
                    # 'attachment': [{
                    #     'value': base64.b64encode(open('../file.jpg').read())
                    # }]

                time.sleep(1)
        else:
            print "Connection failed. Invalid API token?"

    def _parse_events(self, events):
        if not events:
            return []

        print events

        bugs = []
        for event in events:
            if "message" == event["type"]:
                user = event["user"]
                text = event["text"]
                summary = ""
                file_shared = "file_share" == event["subtype"] if "subtype" in event else None
                if file_shared:
                    # https://api.slack.com/types/file
                    # todo do something with the attached file
                    text = event["file"]["title"]
                    summary = event["file"]["url_private"]
                    pass

                # determine if the text is a bug
                if text.lower().startswith('bug:'):
                    bug = Bug()
                    bug.user = user
                    bug.text = text.replace('bug:', '').strip()
                    bug.summary = summary
                    bugs.append(bug)

        if bugs:
            print bugs
        return bugs


class Bug:
    def __init__(self):
        self.text = ""
        self.summary = ""
        self.user = ""
        pass

    def __str__(self):
        return self.text, ":", self.summary


if __name__ == '__main__':
    bot = JiraBot("../config/jirabot.conf")
    bot.start()
    print "here"