"""Script to manage redmine project"""
import logging
from redminelib import Redmine
from icecream import ic
import docker
logging.basicConfig(filename="example.log", encoding="utf-8", level=logging.DEBUG)
client = docker.from_env()
if client.containers.get("3c155e01967d"):
    pass
else:
    container = client.containers.run("configured", name="redmine_test", detach=True)


class RedmineManager:
    """Class to manage a project"""

    def __init__(
        self,
        url,
        username,
        password,
        project_id,
        status_id_complete,
        status_id_ready,
        tracker_id,
        priority_id,
    ):
        self.redmine = Redmine(url, username=username, password=password)
        self.project_id = project_id
        self.status_id_complete = status_id_complete
        self.status_id_ready = status_id_ready
        self.tracker_id = tracker_id
        self.priority_id = priority_id
        self.issues = self.redmine.issue.filter(project_id=project_id)

    def _create_task(self, name):
        """Creates Tasks"""
        issue = self.redmine.issue.create(
            project_id=self.project_id,
            subject=name,
            tracker_id=self.tracker_id,
            priority_id=self.priority_id,
        )
        return issue

    def find_task(self, name_to_find):
        """Takes Subject Name and returns its ID"""
        for elem in self.issues:
            name = getattr(elem, "subject")
            if name_to_find == name:
                id_of_searched_task = getattr(elem, "id")
                return id_of_searched_task
        return 0

    def prepare_list(self):
        """Prepares List from graph on wiki"""
        wiki_page = self.redmine.wiki_page.get("Wiki", project_id=self.project_id)
        list_ = wiki_page.text
        list_ = list_.replace(" ", "")
        list_ = list_.replace('""', "")
        list_ = list_.replace("\n", "")
        list_ = list_.replace("\r", "")
        list_ = list_.split(";")
        new_list = []
        for elem in list_:
            new_list.append(elem.split("->"))
        return new_list

    def init_project(self):
        """Initialize project from graph on wiki"""
        checking_list = []
        for i in range(0, len(list_) - 1):
            if list_[i][0] in checking_list:
                if list_[i][1] in checking_list:
                    self.find_task(list_[i][0])
                    self.find_task(list_[i][1])
                    # done
                else:
                    self._create_task(list_[i][1])
                    checking_list.append(list_[i][1])
                    self.find_task(list_[i][0])
                    # done
            else:
                self._create_task(list_[i][0])
                checking_list.append(list_[i][0])
                if list_[i][1] in checking_list:
                    self.find_task(list_[i][1])
                else:
                    self._create_task(list_[i][1])
                    checking_list.append(list_[i][1])

    def get_number(self, issue, list_):
        """Gets task, returns number of subtasks"""
        number = 0
        for i in range(0, len(list_) - 1):
            if issue in list_[i][1]:
                number = number + 1
        return number

    def get_ids(self, issue, list_):
        """Gets task, returns IDs of  subtasks"""
        ids = []
        for i in range(0, len(list_) - 1):
            if issue in list_[i][1]:
                ids.append(self.find_task(list_[i][0]))
        return ids

    def _check_status(self, issue, list_):
        """Gets task, returns number of completed subtasks"""
        number = 0
        for i in range(0, len(list_) - 1):
            if issue in list_[i][1]:
                issue2 = self.redmine.issue.get(self.find_task(list_[i][0]))
                number += self._issue_status_check(issue2)
        return number

    def _issue_status_check(self, issue):
        """Gets issue and checks if status is completed"""
        number = 0
        if issue.status.id == self.status_id_complete:
            number = 1
        return number

    def _notification(self, id_of_issue):
        """Notification"""
        with open("gotowe_do_realizacji.txt", "w", encoding="utf8") as file:
            file.write(f"Task o id {id_of_issue} jest Gotowy do realizacji\n")
            file.close()

    def delete_all(self):
        """Deletes all issues"""
        for elem in self.issues:
            elem.delete()

    def get_issue(self, id_of_task):
        """Returns issue of given ID"""
        return self.redmine.issue.get(id_of_task)

    def get_issues(self):
        """Returs all issues"""
        return self.issues

    def update(self):
        """Updates Redmine by reading graph from wiki"""
        for i in range(0, len(list_) - 1):
            first = self.find_task(list_[i][0])
            second = self.find_task(list_[i][1])
            issue = self.redmine.issue.get(first)
            issue2 = self.redmine.issue.get(second)
            number_of_completed_tasks = 0
            if (
                issue.status.id == self.status_id_complete
                and issue2.status.id != self.status_id_ready
                and issue2.status.id != self.status_id_complete
            ):
                number_of_completed_tasks = self._check_status(issue2.subject, list_)
            if number_of_completed_tasks == self.get_number(issue2.subject, list_):
                issue2.status_id = self.status_id_ready
                issue2.save()
                ic(issue2.status_id)
                self._notification(second)


# Configuration
REDMINE_URL = "http://172.17.0.2:3000/"
REDMINE_USERNAME = "admin"
REDMINE_PASSWORD = "admin123"
PROJECT_ID = "project"
STATUS_ID_COMPLETE = 4
STATUS_ID_READY = 3
STATUS_ID_NEW = 1
TRACKER_ID = 1
PRIORITY_ID = 1

redmine_manager = RedmineManager(
    REDMINE_URL,
    REDMINE_USERNAME,
    REDMINE_PASSWORD,
    PROJECT_ID,
    STATUS_ID_COMPLETE,
    STATUS_ID_READY,
    TRACKER_ID,
    PRIORITY_ID,
)

# INITIALIZATION
list_ = redmine_manager.prepare_list()
# redmine_manager.delete_all()

