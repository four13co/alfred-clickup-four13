#!/usr/bin/env python
# encoding: utf-8
#
# Copyright  (c) 2020 Michael Schmidt-Korth
#
# GNU GPL v2.0 Licence. See https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
#
import sys
# import argparse
import os
import json
import datetime
from main import DEBUG, formatNotificationText
from config import confNames, getConfigValue
from workflow import Workflow, web
from workflow.notify import notify
from validation import validate_clickup_id, validate_api_key


def main(wf):
	if len(wf.args):
		query = wf.args[0]
	else:
		query = None
	
	taskParameters = json.loads(query)
	getCurrentUser()
	createTask(taskParameters['inputName'], taskParameters['inputContent'], taskParameters['inputDue'], taskParameters['inputPriority'], taskParameters['inputTags'], taskParameters['inputList'])


def getCurrentUser():
	'''If not yet stored, retrieves the current user Id to assign tasks to by default (so they appear in Inbox).'''
	if DEBUG > 0:
		log.debug('[ Calling API to create task ]')
	
	if not getConfigValue(confNames['confUser']):
		url = 'https://api.clickup.com/api/v2/user'
		params = None
		headers = {}
		try:
			api_key = validate_api_key(getConfigValue(confNames['confApi']))
			headers['Authorization'] = api_key
		except ValueError as e:
			log.error(f'Invalid API key format: {e}')
			wf3.add_item(title = 'Invalid API Key', subtitle = 'Please check your API key configuration', valid = True, arg = 'cu:config ', icon = 'error.png')
			wf3.send_feedback()
			exit()
		headers['Content-Type'] = 'application/json'
		
		if DEBUG > 1:
			log.debug(url)
			log.debug(headers)
		
		try:
			request = web.get(url, params = params, headers = headers, timeout = 30)
			request.raise_for_status()
		except:
			log.debug('Error on HTTP request')
			wf3.add_item(title = 'Error connecting to ClickUp.', subtitle = 'Open configuration to check your parameters?', valid = True, arg = 'cu:config ', icon = 'error.png')
			wf3.send_feedback()
			exit()
		result = request.json()
		if DEBUG > 1:
			log.debug('Response: ' + str(result))
		
		wf.settings['userId'] = result['user']['id']


def createTask(inputName, inputContent, inputDue, inputPriority, inputTags, inputList):
	'''Creates a Task by sending it to the ClickUp API.

----------
	@param str inputName: The user's input for the task title.
	@param str inputContent: The user's input for the task decsription.
	@param str inputDue: The user's input for the task due date.
	@param str inputPriority: The user's input for the task priority.
	@param str inputTags: The user's input for the task tags.
	@param str inputList: The user's input for the task list.
	'''
	if DEBUG > 0:
		log.debug('[ Calling API to create task ]')
	
	if not inputList:
		inputListId = getConfigValue(confNames['confList'])
	else:
		# Get value of first key in dictionary {Name, Id} by converting to List. The dict will always contain a single list name+Id the user specified.
		inputListId = next(iter(inputList.items()))[1] # Get value for first key of dict
	
	# Validate list ID
	try:
		inputListId = validate_clickup_id(inputListId, 'list')
	except ValueError as e:
		log.error(f'Invalid list ID: {e}')
		wf3.add_item(title = 'Invalid List ID', subtitle = 'Please check your list configuration', valid = True, arg = 'cu:config ', icon = 'error.png')
		wf3.send_feedback()
		exit()
	
	if inputDue != 'None':
		if len(inputDue) == 26: # 2020-01-01T12:00:00.000000
			inputDue = datetime.datetime.strptime(str(inputDue)[:len(inputDue) - 10], '%Y-%m-%d %H:%M') # Convert String to datetime. Remove seconds.milliseconds (e.g. :26.614286) from string
		else: # 2020-01-01T12:00:00
			inputDue = datetime.datetime.strptime(str(inputDue)[:len(inputDue)], '%Y-%m-%d %H:%M:%S')
		inputDueMs = (inputDue - datetime.datetime.fromtimestamp(0)).total_seconds() * 1000.0 # Convert datetime into ms. Use fromtimestamp() to get local timezone instead of utcfromtimestamp()
	
	url = f'https://api.clickup.com/api/v2/list/{inputListId}/task'
	params = None
	headers = {}
	try:
		api_key = validate_api_key(getConfigValue(confNames['confApi']))
		headers['Authorization'] = api_key
	except ValueError as e:
		log.error(f'Invalid API key format: {e}')
		wf3.add_item(title = 'Invalid API Key', subtitle = 'Please check your API key configuration', valid = True, arg = 'cu:config ', icon = 'error.png')
		wf3.send_feedback()
		exit()
	headers['Content-Type'] = 'application/json'
	data = {}
	data['name'] = inputName
	data['content'] = inputContent
	if inputDue != 'None':
		data['due_date'] = int(inputDueMs)
		data['due_date_time'] = True # Translated into true
	data['priority'] = inputPriority if inputPriority is not None else None # Translated into 'null'
	data['tags'] = inputTags
	if getConfigValue(confNames['confUser']): # Default assignee = current user
		data['assignees'] = [getConfigValue(confNames['confUser'])]
	
	if DEBUG > 1:
		log.debug(url)
		log.debug(headers)
		log.debug(data)
	
	try:
		import json
		request = web.post(url, params = params, data = json.dumps(data), headers = headers, timeout = 30)
		request.raise_for_status()
	except:
		log.debug('Error on HTTP request')
		wf.add_item(title = 'Error connecting to ClickUp.', subtitle = 'Open configuration to check your parameters?', valid = True, arg = 'cu:config ', icon = 'error.png')
		wf.send_feedback()
		exit()
	result = request.json()
	if DEBUG > 1:
		log.debug('Response: ' + str(result))
	
	# If user pressed 'opt' (optInput == true), we do not want to show a notification, as the task is opened in the browser
	hasUserNotPressedOpt = 'optInput' not in os.environ or os.environ['optInput'] == 'false'
	if getConfigValue(confNames['confNotification']) == 'true' and (hasUserNotPressedOpt):
		notify('Task Created', inputName, formatNotificationText(inputContent, inputDue, inputTags, inputPriority, None, False))
	elif 'optInput' in os.environ and os.environ['optInput'] == 'true':
		print(result['url'])


if __name__ == "__main__":
	wf = Workflow()
	wf3 = Workflow()
	log = wf.logger
	sys.exit(wf.run(main))
