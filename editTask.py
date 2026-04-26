#!/usr/bin/env python
# encoding: utf-8
#
# Copyright  (c) 2020 Michael Schmidt-Korth
#
# GNU GPL v2.0 Licence. See https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
#
import sys
import os
import requests
from datetime import datetime
from main import DEBUG, formatDate
from config import confNames, getConfigValue
from workflow import Workflow, ICON_WEB, ICON_CLOCK, ICON_WARNING, ICON_GROUP, ICON_INFO, ICON_TRASH, ICON_SETTINGS, ICON_NOTE, ICON_USER, ICON_HOME, ICON_FAVORITE, ICON_SWITCH, ICON_SWIRL, ICON_HELP, ICON_COLOR, web
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class Status:
    id: str
    status: str
    color: str
    orderindex: int
    type: str

@dataclass
class User:
    id: int
    username: str
    color: str
    email: str
    profilePicture: str
    initials: Optional[str] = None

@dataclass
class ChecklistItem:
    id: str
    name: str
    orderindex: int
    assignee: Optional[Any]
    group_assignee: Optional[Any]
    resolved: bool
    parent: Optional[Any]
    date_created: str
    start_date: Optional[Any]
    start_date_time: bool
    due_date: Optional[Any]
    due_date_time: bool
    sent_due_date_notif: Optional[Any]
    children: List[Any]

@dataclass
class Checklist:
    id: str
    task_id: str
    name: str
    date_created: str
    orderindex: int
    creator: int
    resolved: int
    unresolved: int
    items: List[ChecklistItem]

@dataclass
class Tag:
    name: str
    tag_fg: str
    tag_bg: str
    creator: int

@dataclass
class Priority:
    color: str
    id: str
    orderindex: str
    priority: str

@dataclass
class CustomFieldOption:
    id: str
    name: str
    color: Optional[str]
    orderindex: int

@dataclass
class CustomFieldTypeConfig:
    options: Optional[List[CustomFieldOption]] = None
    tracking: Optional[Dict[str, bool]] = None
    complete_on: Optional[int] = None
    subtask_rollup: Optional[bool] = None

@dataclass
class CustomFieldValue:
    percent_complete: Optional[int] = None

@dataclass
class CustomField:
    id: str
    name: str
    type: str
    type_config: CustomFieldTypeConfig
    date_created: str
    hide_from_guests: bool
    required: bool
    value: Optional[CustomFieldValue] = None

@dataclass
class Sharing:
    public: bool
    public_share_expires_on: Optional[Any]
    public_fields: List[str]
    token: Optional[Any]
    seo_optimized: bool

@dataclass
class ListInfo:
    id: str
    name: str
    access: bool

@dataclass
class ProjectInfo:
    id: str
    name: str
    hidden: bool
    access: bool

@dataclass
class FolderInfo:
    id: str
    name: str
    hidden: bool
    access: bool

@dataclass
class SpaceInfo:
    id: str

@dataclass
class Task:
    id: str
    custom_id: Optional[Any]
    custom_item_id: int
    name: str
    text_content: str
    description: str
    status: Status
    orderindex: str
    date_created: str
    date_updated: str
    archived: bool
    creator: User
    assignees: List[User]
    group_assignees: List[Any]
    watchers: List[User]
    checklists: List[Checklist]
    tags: List[Tag]
    parent: Optional[Any]
    top_level_parent: Optional[Any]
    points: Optional[Any]
    time_estimate: Optional[Any]
    time_spent: int
    custom_fields: List[CustomField]
    dependencies: List[Any]
    linked_tasks: List[Any]
    locations: List[Any]
    team_id: str
    url: str
    sharing: Sharing
    permission_level: str
    list: ListInfo
    project: ProjectInfo
    folder: FolderInfo
    space: SpaceInfo
    attachments: List[Any]
    date_closed: Optional[Any] = None
    date_done: Optional[Any] = None
    due_date: Optional[str] = None
    start_date: Optional[Any] = None
    priority: Optional[Priority] = None

def from_dict(cls, data):
    if hasattr(cls, '__dataclass_fields__'):
        # log.debug(">>>>> " + str(cls))
        fieldtypes = {f.name: f.type for f in cls.__dataclass_fields__.values()}
        return cls(**{f: from_dict(fieldtypes[f], data[f]) if f in data else None for f in fieldtypes})
    elif isinstance(data, list):
        # log.debug("<<<<< " + str(cls.__args__[0]))
        return [from_dict(cls.__args__[0], item) for item in data]
    else:
        # log.debug("<<<<< Returning data as is: >>>>>")
        return data

def main(wf):
    if len(wf.args):
        query = wf.args[0]
        log.debug("############################################################################################################")
        log.debug(wf.args)  # Debug Args Passed In
        log.debug("############################################################################################################")
    else:
        query = None
    if query:
        # closeTask(query.split('/')[-1])
        debugTask(query.split('/')[-1])

def get_local_profile_picture(url, user_id, wf3=None):
    # Define a local path for the image
    img_dir = os.path.join(wf3.datadir, 'profile_pics')
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, f'{user_id}.jpg')
    # Download if not already present
    if not os.path.exists(img_path):
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            with open(img_path, 'wb') as f:
                f.write(r.content)
    log.debug('image_path: ' + img_path)
    return img_path

def debugTask(strTaskId):
    '''Debug function to fetch and log task details.
----------
    @param str strTaskId: Id of the Task to debug.
    '''
    from workflow.notify import notify
    log.debug('[ Calling API to fetch task details ]')
    wf3 = Workflow()
    url = 'https://api.clickup.com/api/v2/task/' + strTaskId
    headers = {}
    headers['Authorization'] = getConfigValue(confNames['confApi'])
    headers['Content-Type'] = 'application/json'
    log.debug("############################################################################################################")
    log.debug(strTaskId)
    log.debug(url)
    log.debug(headers)
    log.debug("############################################################################################################")
    try:
        import requests
        log.debug('headers: ' + str(headers))
        request = requests.get(url, headers=headers, timeout=10)
        request.raise_for_status()
        log.debug("Request Status Code: " + str(request.status_code))
        try:
            result = request.json()
        except Exception as exc:
            log.debug('Error parsing JSON response:' + str(exc))
            result = None
        log.debug("############################################################################################################")
        log.debug("############################################################################################################")
        log.debug("############################################################################################################")
        log.debug("Result Type: " + str(type(result)))
        log.debug("Result: " + str(result))
        log.debug("############################################################################################################")
        log.debug("############################################################################################################")
        log.debug("############################################################################################################")
        if result:
            task = from_dict(Task, result)
        else:
            log.debug("No task data found!!!!")
            # initialize empty task to avoid breaking the code
            task = Task(
                id='N/A', custom_id=None, custom_item_id=0, name='N/A', text_content='', description='',
                status=Status(id='N/A', status='N/A', color='', orderindex=0, type=''),
                orderindex='', date_created='', date_updated='', date_closed=None, date_done=None,
                archived=False,
                creator=User(id=0, username='N/A', color='', email='', profilePicture=''),
                assignees=[], group_assignees=[], watchers=[], checklists=[], tags=[], parent=None,
                top_level_parent=None,
                priority=Priority(color='', id='', orderindex='', priority=''),
                due_date=None, start_date=None, points=None, time_estimate=None, time_spent=0,
                custom_fields=[], dependencies=[], linked_tasks=[], locations=[], team_id='', url='',
                sharing=Sharing(public=False, public_share_expires_on=None, public_fields=[], token=None, seo_optimized=False),
                permission_level='', list=ListInfo(id='N/A', name='N/A', access=False),
                project=ProjectInfo(id='N/A', name='N/A', hidden=False, access=False),
                folder=FolderInfo(id='N/A', name='N/A', hidden=False, access=False),
                space=SpaceInfo(id='N/A'), attachments=[]
            )
        log.debug("############################################################################################################")
        # log.debug('Response: ' + str(result))
        log.debug("############################################################################################################")
        # log.debug(result['id'])
        # log.debug(result['name'])
        # log.debug(result['description'])
        # log.debug(result['status'])
        # log.debug('Status: ')
        # log.debug(result['status']['status'])
        # log.debug(result['date_created'])
        # log.debug(result['date_updated'])
        # log.debug(result['date_closed'])
        # log.debug(result['date_done'])
        # log.debug(result['archived'])
        # log.debug(result['creator'])
        # log.debug(result['assignees'])
        # log.debug(result['group_assignees'])
        # log.debug(result['watchers'])
        # log.debug(result['checklists'])
        # log.debug(result['checklists'])
        # log.debug(result['tags'])
        # log.debug(result['parent'])
        # log.debug(result['priority'])
        # log.debug(result['due_date'])
        # log.debug(result['start_date'])
        # log.debug(result['points'])
        # log.debug(result['time_estimate'])
        # log.debug(result['time_spent'])
        # log.debug(result['custom_fields'])
        # log.debug(result['dependencies'])
        # log.debug(result['linked_tasks'])
        # log.debug(result['locations'])
        # log.debug(result['team_id'])
        # log.debug(result['url'])
        # log.debug(result['sharing'])
        # log.debug(result['permission_level'])
        # log.debug(result['list'])
        # log.debug(result['project'])
        # log.debug(result['folder'])
        # log.debug(result['space'])
        # log.debug(result['attachments'])
        log.debug("############################################################################################################")
        log.debug("task.id " + str(task.id))
        log.debug("task.name " + str(task.name))
        log.debug("task.status.status " + str(task.status.status))
        log.debug("task.creator.username " + str(task.creator.username))
        if task.assignees:
            log.debug("task.assignees " + str(task.assignees))
        log.debug("task.dateCreated Raw " + str(task.date_created))
        log.debug("task.dateCreated Formatted " + formatDate(datetime.fromtimestamp(int(task.date_created)/1000)))
        log.debug("############################################################################################################")
        wf3.setvar('id', task.id)
        wf3.setvar('name', task.name)
        wf3.setvar('status', task.status.status)
        duedate = task.due_date if task.due_date else "None"
        wf3.setvar('duedate', duedate)
        # taskpriority = task.priority.priority if task.priority else "None"
        # wf3.setvar('priority', taskpriority)
        wf3.setvar('startdate', task.start_date)
        wf3.setvar('donedate', task.date_done)
        wf3.setvar('closedate', task.date_closed)
        wf3.setvar('createdate', task.date_created)
        wf3.setvar('updatedate', task.date_updated)
        wf3.setvar('description', task.description)
        wf3.setvar('url', task.url)
        wf3.setvar('creator', task.creator.username)
        wf3.setvar('profilePicture', task.creator.profilePicture)
        profile_icon_path = get_local_profile_picture(task.creator.profilePicture, task.creator.id, wf3)
        wf3.setvar('profileImagePath', profile_icon_path)
        # if task.assignees:
        #     wf3.setvar('assignees', str(task.assignees))
        # wf3.setvar('datecreatedraw', str(task.date_created))
        # wf3.setvar('datecreated', formatDate(datetime.fromtimestamp(int(task.date_created)/1000)))
        # wf3.setvar('checklists', str(task.checklists))
        wf3.add_item(
            title = 'Action Task Info: ' + task.name,
            subtitle = 'With TaskID: ' + task.id,
            valid = True,
            arg = 'display ' + task.id,
            icon = ICON_SWITCH
        )
        wf3.add_item(
            title = 'Status Options: ',
            subtitle = 'Current Status: ' + task.status.status,
            valid = True,
            arg = 'status ' + task.id,
            icon = ICON_INFO
        )
        wf3.add_item(
            title = 'DueDate Options:',
            subtitle = 'Current Due Date: ' + (task.due_date if task.due_date else 'None'),
            valid = True,
            arg = 'duedate ' + task.id,
            icon = ICON_CLOCK
        )
        wf3.add_item(
            title = 'Priority Options:',
            subtitle = '\!1 Urgent | \!2 High | \!3 Normal | \!4 Low | Current Priority',
            valid = True,
            arg = 'priority ' + task.id,
            icon = ICON_COLOR
        )
        wf3.add_item(
            title = 'Edit Task: ' + task.name,
            subtitle = 'With TaskID: ' + task.id,
            valid = True,
            arg = 'edit ' + task.id,
            icon = ICON_NOTE
        )
        wf3.add_item(
            title = 'Close Task: ' + task.name,
            subtitle = 'With TaskID: ' + task.id,
            valid = True,
            arg = 'close ' + task.id,
            icon = ICON_FAVORITE
        )
        wf3.add_item(
            title = 'Remove Task: ' + task.name,
            subtitle = 'With TaskID: ' + task.id,
            valid = True,
            arg = 'remove ' + task.id,
            icon = ICON_TRASH
        )
        wf3.add_item(
            title = 'User Options: ' + task.creator.username,
            subtitle = 'With TaskID: ' + task.id,
            valid = True,
            arg = 'user ' + task.id,
            icon = profile_icon_path
        )
        wf3.add_item(
            title = 'Config Settings',
            subtitle = 'Edit Workflow Settings: cu:config',
            valid = True,
            arg = 'settings',
            icon = 'settings.png'
        )
        wf3.add_item(
            title = 'Help!',
            subtitle = 'ClickUp Help Options: cu:help',
            valid = True,
            arg = 'help',
            icon = ICON_HELP
        )
        wf3.add_item(
            title = 'Back',
            subtitle = 'List Tasks Again: ',
            valid = True,
            arg = 'back ' + task.id,
            icon = ICON_HOME
        )


        wf3.send_feedback()
        log.debug("############################################################################################################")
        return
    except Exception as exc:
        log.debug('Error on HTTP request:' + str(exc))
        wf3.add_item(
            title = 'Error connecting to ClickUp.', subtitle = 'Open configuration to check your parameters?', valid = True, arg = 'cu:config ', icon = 'error.png')
        wf3.send_feedback()
        exit()

# Clone of code in closeTask.py to start from as this will be extended
def closeTask(strTaskId):
    '''Updates an existing Task and sets its status to 'Closed'.

----------
    @param str strTaskId: Id of the Task to update.
    '''
    from workflow.notify import notify
    if DEBUG > 0:
        log.debug('[ Calling API to close task ]')
    wf3 = Workflow()
    url = 'https://api.clickup.com/api/v2/task/' + strTaskId

    headers = {}
    headers['Authorization'] = getConfigValue(confNames['confApi'])
    headers['Content-Type'] = 'application/json'
    data = {}
    data['status'] = 'Closed'
    if DEBUG > 1:
        log.debug(url)
        log.debug(headers)
        log.debug(data)

    try:
        import requests
        request = requests.put(url, json=data, headers=headers, timeout=10)
        request.raise_for_status()
        result = request.json()
        if DEBUG > 1:
            log.debug('Response: ' + str(result))
            notify('Closed Task', result['name'])
    except Exception as exc:
        log.debug('Error on HTTP request:' + str(exc))
        wf3.add_item(title = 'Error connecting to ClickUp.', subtitle = 'Open configuration to check your parameters?', valid = True, arg = 'cu:config ', icon = 'error.png')
        wf3.send_feedback()
        exit()


if __name__ == "__main__":
    wf = Workflow()
    log = wf.logger
    sys.exit(wf.run(main))
