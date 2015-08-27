import json
import re

__author__ = 'wchen'

SLACK_USER_REGEX = '(?P<markup><@(?P<user_id>U[0-9A-Z]*)(|\|(?P<name>[a-zA-Z]*))>)[ :-]*'

def fetch_slack_users(client):
    response = json.loads(client.api_call('users.list'))
    members = response['members']
    all_users = [SlackUser(m) for m in members]
    return [user for user in all_users if user.is_user()]

def remove_slack_user_markup(text, users):
    # note: resolves the first one only
    match = re.search(SLACK_USER_REGEX, text, re.UNICODE)
    if match:
        user_id = match.group('user_id')
        name = match.group('name')
        markup = match.group('markup')
        print "matched", user_id, name, markup
        for user in users:
            if user.id == user_id:
                text = text.replace(match.group(0), '').strip()
                return text, user
    return text, None


class SlackUser:
    def __init__(self, json):
        # expecting https://api.slack.com/types/user
        self.id = json['id']
        self.name = json['name']
        self.deleted = json['deleted']
        self.email = None
        self.is_bot = False

        if 'is_bot' in json:
            self.is_bot = json['is_bot']
        else:
            self.email = json['profile']['email']

    def is_user(self):
        return not self.deleted and not self.is_bot

    def __str__(self):
        return '<@{}|{}>: {}'.format(self.id, self.name, self.email)
