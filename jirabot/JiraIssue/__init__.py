import re
from enum import Enum, unique

__author__ = 'wchen'


def _classify(text):
    for issue_type in list(IssueType):
        prefix = issue_type.value
        new_text = re.sub(prefix, '', text.strip(), re.IGNORECASE | re.UNICODE)
        if len(new_text) != len(text):
            return (issue_type, new_text)
    return (IssueType.Unknown, text)


def is_issue(text):
    return _classify(text)[0] != IssueType.Unknown


@unique
class IssueType(Enum):
    Bug = '(?i)^bug[ :-]\s*'
    Task = '(?i)^task[ :-]\s*'
    Unknown = ''


class Issue:
    def __init__(self, title, description='', assignee=None):
        result = _classify(title)
        assert result[0] != IssueType.Unknown
        self.text = result[1]
        self.type = result[0]
        self.summary = description
        self.assignee = assignee

    def __str__(self):
        if self.assignee:
            return u'({}\'s {} *{}* {})'.format(self.assignee, self.type.name, self.text, self.summary)
        return u'({} *{}* {})'.format(self.type.name, self.text, self.summary)
