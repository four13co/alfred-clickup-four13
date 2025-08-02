#!/usr/bin/env python
# encoding: utf-8
#
# Copyright  (c) 2020 Michael Schmidt-Korth
#
# GNU GPL v2.0 Licence. See https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
#
import sys
import datetime
import emoji
from main import DEBUG
from workflow import Workflow, ICON_WEB, ICON_CLOCK, ICON_WARNING, ICON_GROUP, web
from config import confNames, getConfigValue
from validation import validate_clickup_id, validate_api_key


def main(wf):
	getTasks(wf)


def getTasks(wf):
	'''Retrieves a list of Tasks from the ClickUp API.

----------
	'''
	log = wf.logger
	
	# Skip empty queries for search mode to avoid wasteful API calls
	if len(wf.args) > 1 and wf.args[1] == 'search' and (not wf.args[0] or wf.args[0].strip() == ''):
		wf3 = Workflow()
		# Get search entities configuration
		search_entities = getConfigValue(confNames['confSearchEntities']) or 'tasks'
		# Handle both old format (tasks+docs) and new format (tasks,docs)
		if '+' in search_entities:
			# Convert old format to new format
			search_entities = search_entities.replace('+', ',')
		
		entities = search_entities.split(',')
		search_types = []
		if 'tasks' in entities:
			search_types.append('tasks')
		if 'docs' in entities:
			search_types.append('docs')
		if 'chats' in entities:
			search_types.append('chats')
		if 'lists' in entities:
			search_types.append('lists')
		if 'folders' in entities:
			search_types.append('folders')
		if 'spaces' in entities:
			search_types.append('spaces')
		
		if search_entities == 'all':
			search_text = 'tasks, docs, chats, folders, and spaces'
		else:
			search_text = ' and '.join(search_types) if search_types else 'tasks'
		
		wf3.add_item(
			title = f'Start typing to search {search_text}...',
			subtitle = 'Enter at least one character to begin searching',
			valid = False,
			icon = 'icon.png'
		)
		wf3.send_feedback()
		return
	
	# For mode = search: ClickUp does not offer a parameter 'filter_by' - therefore we receive all tasks, and use Alfred/fuzzy to filter.
	if DEBUG > 0:
		log.debug('[ Calling API to list tasks ]')
	
	# Validate team/workspace ID
	try:
		team_id = validate_clickup_id(getConfigValue(confNames['confTeam']), 'workspace')
		url = f'https://api.clickup.com/api/v2/team/{team_id}/task'
	except ValueError as e:
		log.error(f'Invalid team/workspace ID: {e}')
		wf.add_item(title = 'Invalid Workspace ID', subtitle = 'Please check your workspace configuration', valid = True, arg = 'cu:config ', icon = 'error.png')
		wf.send_feedback()
		return
	
	params = {}
	wf3 = Workflow()

	# Use searchScope, default to 'auto' if not configured
	search_scope = getConfigValue(confNames['confSearchScope']) or 'auto'
	
	if search_scope == 'list':
		list_id = getConfigValue(confNames['confList'])
		if list_id:
			params['list_ids[]'] = validate_clickup_id(list_id, 'list')
	elif search_scope == 'folder':
		folder_id = getConfigValue(confNames['confProject'])
		if folder_id:
			params['project_ids[]'] = validate_clickup_id(folder_id, 'folder')
	elif search_scope == 'space':
		space_id = getConfigValue(confNames['confSpace'])
		if space_id:
			params['space_ids[]'] = validate_clickup_id(space_id, 'space')
	elif search_scope == 'auto':
		# Auto mode: start with list scope
		list_id = getConfigValue(confNames['confList'])
		if list_id:
			params['list_ids[]'] = validate_clickup_id(list_id, 'list')
	params['order_by'] = 'due_date'
	# ClickUp API will return up to 100 tasks per page (their maximum)
	params['page'] = 0
	
	# Differentiates between listing all Alfred-created tasks and searching for all tasks (any)
	if DEBUG > 0 and len(wf.args) > 1 and wf.args[1] == 'search':
		log.debug('[ Mode: Search (cus) ]')
		# Add search query if provided
		if len(wf.args) > 0 and wf.args[0]:
			params['query'] = wf.args[0]
	elif DEBUG > 0 and len(wf.args) > 1 and wf.args[1] == 'open':
		log.debug('[ Mode: Open tasks (cuo) ]')
		# from datetime import date, datetime, timezone, timedelta

		today = datetime.date.today()
		todayEndOfDay = datetime.datetime(today.year, today.month, today.day, 23, 59, 59)
		epoch = datetime.datetime(1970, 1, 1)
		todayEndOfDayMs = int((todayEndOfDay - epoch).total_seconds() / datetime.timedelta(microseconds = 1).total_seconds() / 1000)

		params['due_date_lt'] = todayEndOfDayMs
	else:
		log.debug('[ Mode: List tasks (cul) ]')
		defaultTag = getConfigValue(confNames['confDefaultTag'])
		if not defaultTag:
			wf3.add_item(
				title = 'No default tag configured',
				subtitle = 'Use "cu:config" to set a default tag before using this command',
				valid = False,
				icon = 'error.png'
			)
			wf3.send_feedback()
			exit()
		params['tags[]'] = defaultTag
	headers = {}
	try:
		api_key = validate_api_key(getConfigValue(confNames['confApi']))
		headers['Authorization'] = api_key
	except ValueError as e:
		log.error(f'Invalid API key format: {e}')
		wf3.add_item(title = 'Invalid API Key', subtitle = 'Please check your API key configuration', valid = True, arg = 'cu:config ', icon = 'error.png')
		wf3.send_feedback()
		return
	headers['Content-Type'] = 'application/json'
	if DEBUG > 1:
		log.debug(url)
		log.debug(headers)
		log.debug(params)
	try:
		request = web.get(url, params = params, headers = headers, timeout = 30)
		request.raise_for_status()
	except Exception as e:
		log.debug('Error on HTTP request: ' + str(e))
		wf3.add_item(title = 'Error connecting to ClickUp.', subtitle = 'Open configuration to check your parameters?', valid = True, arg = 'cu:config ', icon = 'error.png')
		wf3.send_feedback()
		exit()
	
	try:
		result = request.json()
		if DEBUG > 1:
			log.debug('Response received with %d tasks (ClickUp max: 100 per page)' % len(result.get('tasks', [])))
	except Exception as e:
		log.debug('Error parsing JSON response: ' + str(e))
		wf3.add_item(title = 'Error parsing ClickUp response.', subtitle = 'The response may be too large. Try a more specific search.', valid = False, icon = 'error.png')
		wf3.send_feedback()
		exit()

	# Check if response has tasks
	if 'tasks' not in result:
		log.debug('No tasks key in response: ' + str(result.keys()))
		wf3.add_item(title = 'No tasks found.', subtitle = 'Try a different search query.', valid = False, icon = 'note.png')
		wf3.send_feedback()
		exit()
	
	# Auto mode expansion logic - accumulate results from all levels
	if search_scope == 'auto' and len(wf.args) > 1 and wf.args[1] == 'search':
		all_tasks = list(result.get('tasks', []))  # Start with list-level tasks
		task_ids = {task['id'] for task in all_tasks}  # Track IDs to avoid duplicates
		
		if DEBUG > 0:
			log.debug('Auto mode: Got %d tasks at list level' % len(all_tasks))
		
		# Always try folder level to get more results
		if getConfigValue(confNames['confProject']):
			if DEBUG > 0:
				log.debug('Auto mode: Expanding to folder level')
			# Remove list constraint, add folder constraint
			temp_params = params.copy()
			if 'list_ids[]' in temp_params:
				del temp_params['list_ids[]']
			temp_params['project_ids[]'] = getConfigValue(confNames['confProject'])
			
			# Make another API call
			try:
				request = web.get(url, params = temp_params, headers = headers, timeout = 30)
				request.raise_for_status()
				folder_result = request.json()
				
				# Add new tasks (avoid duplicates)
				for task in folder_result.get('tasks', []):
					if task['id'] not in task_ids:
						all_tasks.append(task)
						task_ids.add(task['id'])
				
				if DEBUG > 0:
					log.debug('Auto mode: Total %d tasks after folder level' % len(all_tasks))
			except Exception as e:
				if DEBUG > 0:
					log.debug('Auto mode folder expansion failed: %s' % str(e))
		
		# If we still don't have many results, try space level
		if len(all_tasks) < 50 and getConfigValue(confNames['confSpace']):
			if DEBUG > 0:
				log.debug('Auto mode: Expanding to space level')
			# Remove folder constraint, add space constraint
			temp_params = params.copy()
			if 'list_ids[]' in temp_params:
				del temp_params['list_ids[]']
			if 'project_ids[]' in temp_params:
				del temp_params['project_ids[]']
			temp_params['space_ids[]'] = getConfigValue(confNames['confSpace'])
			
			# Make another API call
			try:
				request = web.get(url, params = temp_params, headers = headers, timeout = 30)
				request.raise_for_status()
				space_result = request.json()
				
				# Add new tasks (avoid duplicates)
				for task in space_result.get('tasks', []):
					if task['id'] not in task_ids:
						all_tasks.append(task)
						task_ids.add(task['id'])
				
				if DEBUG > 0:
					log.debug('Auto mode: Total %d tasks after space level' % len(all_tasks))
			except Exception as e:
				if DEBUG > 0:
					log.debug('Auto mode space expansion failed: %s' % str(e))
		
		# Replace result with accumulated tasks
		result['tasks'] = all_tasks
	
	# Check if we should also search for docs
	search_entities_raw = getConfigValue(confNames['confSearchEntities']) or 'tasks'
	# Handle both old format (tasks+docs) and new format (tasks,docs)
	if '+' in search_entities_raw:
		search_entities_raw = search_entities_raw.replace('+', ',')
	
	search_entities = search_entities_raw.split(',')
	docs_results = []
	
	if ('docs' in search_entities or search_entities_raw == 'all') and len(wf.args) > 1 and wf.args[1] == 'search':
		# Fetch docs using v3 API (workspace_id is same as team_id)
		try:
			workspace_id = validate_clickup_id(getConfigValue(confNames['confTeam']), 'workspace')
			docs_url = f'https://api.clickup.com/api/v3/workspaces/{workspace_id}/docs'
		except ValueError as e:
			log.error(f'Invalid workspace ID for docs: {e}')
			docs_url = None
		
		if DEBUG > 0:
			log.debug('Fetching docs from v3 API')
		
		try:
			docs_response = web.get(docs_url, headers=headers, timeout=30)
			docs_response.raise_for_status()
			docs_data = docs_response.json()
			
			if DEBUG > 1:
				log.debug('Docs API response: %d docs found' % len(docs_data.get('docs', [])))
			
			# Process docs
			for doc in docs_data.get('docs', []):
				doc_title = doc.get('name', 'Untitled Document')
				doc_id = doc.get('id', '')
				# Try to use the URL from the API response, otherwise construct it
				doc_url = doc.get('url', f'https://app.clickup.com/{workspace_id}/d/{doc_id}')
				
				docs_results.append({
					'type': 'doc',
					'title': doc_title,
					'id': doc_id,
					'url': doc_url
				})
			
			if DEBUG > 0:
				log.debug('Added %d docs to results' % len(docs_results))
				
		except Exception as e:
			if DEBUG > 0:
				log.debug('Failed to fetch docs: ' + str(e))
			# Continue with task results even if docs fail
	
	# Check if we should also search for chat channels
	chat_results = []
	
	if ('chats' in search_entities or search_entities_raw == 'all') and len(wf.args) > 1 and wf.args[1] == 'search':
		# Fetch chat channels using v3 API
		try:
			workspace_id = validate_clickup_id(getConfigValue(confNames['confTeam']), 'workspace')
			chat_url = f'https://api.clickup.com/api/v3/workspaces/{workspace_id}/chat/channels'
		except ValueError as e:
			log.error(f'Invalid workspace ID for chats: {e}')
			chat_url = None
		
		if DEBUG > 0:
			log.debug('Fetching chat channels from v3 API')
		
		try:
			chat_response = web.get(chat_url, headers=headers, timeout=30)
			chat_response.raise_for_status()
			chat_data = chat_response.json()
			
			if DEBUG > 1:
				log.debug('Chat API response: %d channels found' % len(chat_data.get('channels', [])))
			
			# Process chat channels
			for channel in chat_data.get('channels', []):
				channel_name = channel.get('name', 'Unnamed Channel')
				channel_id = channel.get('id', '')
				channel_type = channel.get('type', 'channel')  # Could be 'channel' or 'dm' (direct message)
				
				# Construct URL - this is an educated guess based on ClickUp's URL patterns
				channel_url = f'https://app.clickup.com/{workspace_id}/chat/channel/{channel_id}'
				
				chat_results.append({
					'type': 'chat',
					'title': channel_name,
					'id': channel_id,
					'url': channel_url,
					'channel_type': channel_type
				})
			
			if DEBUG > 0:
				log.debug('Added %d chat channels to results' % len(chat_results))
				
		except Exception as e:
			if DEBUG > 0:
				log.debug('Failed to fetch chat channels: ' + str(e))
			# Continue with other results even if chat fails
	
	# Check if we should search for Lists, Folders, and Spaces
	lists_results = []
	folders_results = []
	spaces_results = []
	
	if len(wf.args) > 1 and wf.args[1] == 'search':
		# Get the search query
		search_query = wf.args[0].lower() if len(wf.args) > 0 and wf.args[0] else ''
		
		# Fetch Spaces
		if 'spaces' in search_entities or search_entities_raw == 'all':
			if DEBUG > 0:
				log.debug('Fetching spaces for search')
			
			try:
				validated_workspace_id = validate_clickup_id(workspace_id, 'workspace')
				space_url = f'https://api.clickup.com/api/v2/team/{validated_workspace_id}/space'
				space_response = web.get(space_url, headers=headers, timeout=30)
				space_response.raise_for_status()
				space_data = space_response.json()
				
				# Filter spaces by name
				for space in space_data.get('spaces', []):
					space_name = space.get('name', '')
					if search_query in space_name.lower():
						space_id = space.get('id', '')
						# Construct URL for space
						space_url = f'https://app.clickup.com/{workspace_id}/s/{space_id}'
						
						spaces_results.append({
							'type': 'space',
							'title': space_name,
							'id': space_id,
							'url': space_url
						})
				
				if DEBUG > 0:
					log.debug('Found %d spaces matching query' % len(spaces_results))
					
			except Exception as e:
				if DEBUG > 0:
					log.debug('Failed to fetch spaces: ' + str(e))
		
		# Fetch Folders (need to fetch from each space)
		if 'folders' in search_entities or search_entities_raw == 'all':
			if DEBUG > 0:
				log.debug('Fetching folders for search')
				
			try:
				# First get all spaces to fetch folders from each
				validated_workspace_id = validate_clickup_id(workspace_id, 'workspace')
				space_url = f'https://api.clickup.com/api/v2/team/{validated_workspace_id}/space'
				space_response = web.get(space_url, headers=headers, timeout=30)
				space_response.raise_for_status()
				space_data = space_response.json()
				
				for space in space_data.get('spaces', []):
					space_id = space.get('id', '')
					# Get folders for this space
					validated_space_id = validate_clickup_id(space_id, 'space')
					folder_url = f'https://api.clickup.com/api/v2/space/{validated_space_id}/folder'
					try:
						folder_response = web.get(folder_url, headers=headers, timeout=30)
						folder_response.raise_for_status()
						folder_data = folder_response.json()
						
						# Filter folders by name
						for folder in folder_data.get('folders', []):
							folder_name = folder.get('name', '')
							if search_query in folder_name.lower():
								folder_id = folder.get('id', '')
								# Construct URL for folder
								folder_url = f'https://app.clickup.com/{workspace_id}/f/{folder_id}'
								
								folders_results.append({
									'type': 'folder',
									'title': folder_name,
									'id': folder_id,
									'url': folder_url,
									'space_name': space.get('name', '')
								})
								
					except Exception as e:
						if DEBUG > 0:
							log.debug('Failed to fetch folders for space %s: %s' % (space_id, str(e)))
				
				if DEBUG > 0:
					log.debug('Found %d folders matching query' % len(folders_results))
					
			except Exception as e:
				if DEBUG > 0:
					log.debug('Failed to fetch folders: ' + str(e))
		
		# Fetch Lists (need to fetch from all accessible locations)
		if 'lists' in search_entities or search_entities_raw == 'all':
			if DEBUG > 0:
				log.debug('Fetching lists for search')
				
			try:
				# Get all lists from workspace
				validated_workspace_id = validate_clickup_id(workspace_id, 'workspace')
				lists_url = f'https://api.clickup.com/api/v2/team/{validated_workspace_id}/list'
				lists_response = web.get(lists_url, headers=headers, timeout=30)
				lists_response.raise_for_status()
				lists_data = lists_response.json()
				
				# Filter lists by name
				for list_item in lists_data.get('lists', []):
					list_name = list_item.get('name', '')
					if search_query in list_name.lower():
						list_id = list_item.get('id', '')
						# Construct URL for list
						list_url = f'https://app.clickup.com/{workspace_id}/li/{list_id}'
						
						lists_results.append({
							'type': 'list',
							'title': list_name,
							'id': list_id,
							'url': list_url,
							'task_count': list_item.get('task_count', 0)
						})
				
				if DEBUG > 0:
					log.debug('Found %d lists matching query' % len(lists_results))
					
			except Exception as e:
				if DEBUG > 0:
					log.debug('Failed to fetch lists: ' + str(e))

	for task in result['tasks']:
		tags = ''
		if task.get('tags'):
			for allTaskTags in task.get('tags', []):
				tags += allTaskTags.get('name', '') + ' '

		subtitle_parts = []
		if task.get('due_date'):
			subtitle_parts.append(emoji.emojize(':calendar:') + str(datetime.datetime.fromtimestamp(int(task.get('due_date'))/1000)))
		if task.get('priority'):
			priority_info = task.get('priority', {})
			if priority_info.get('priority'):
				subtitle_parts.append(emoji.emojize(':exclamation_mark:') + priority_info['priority'].title())
		if task.get('tags') and tags.strip():
			subtitle_parts.append(emoji.emojize(':label:') + tags.strip())
		
		# Safe access to required fields with defaults
		status_text = task.get('status', {}).get('status', 'Unknown')
		task_name = task.get('name', 'Untitled Task')
		task_url = task.get('url', '')
		
		# Choose icon based on priority
		icon = 'icon.png'  # Default icon for tasks
		if task.get('priority'):
			priority_info = task.get('priority', {})
			priority_val = priority_info.get('priority')
			if priority_val == 'urgent':
				icon = 'prio1.png'
			elif priority_val == 'high':
				icon = 'prio2.png'
			elif priority_val == 'normal':
				icon = 'prio3.png'
			elif priority_val == 'low':
				icon = 'prio4.png'
		
		wf3.add_item(
			title = '[' + status_text + '] ' + task_name,
			subtitle = ' '.join(subtitle_parts) if subtitle_parts else 'ClickUp Task',
			match = task_name,  # Use just the task name for fuzzy matching
			valid = True,
			arg = task_url,
			icon = icon
		)
	
	# Add doc results after tasks
	for doc in docs_results:
		wf3.add_item(
			title = '[Doc] ' + doc['title'],
			subtitle = 'ClickUp Document',
			match = doc['title'],  # For fuzzy matching
			valid = True,
			arg = doc['url'],
			icon = 'note.png'  # Using existing note icon for docs
		)
	
	# Add chat channel results after docs
	for chat in chat_results:
		# Add indicator for DMs vs channels
		prefix = '[DM]' if chat['channel_type'] == 'dm' else '[Chat]'
		subtitle = 'Direct Message' if chat['channel_type'] == 'dm' else 'Chat Channel'
		
		wf3.add_item(
			title = prefix + ' ' + chat['title'],
			subtitle = subtitle,
			match = chat['title'],  # For fuzzy matching
			valid = True,
			arg = chat['url'],
			icon = 'label.png'  # Using label icon for chats
		)
	
	# Add list results
	for list_item in lists_results:
		wf3.add_item(
			title = '[List] ' + list_item['title'],
			subtitle = f"ClickUp List - {list_item['task_count']} tasks",
			match = list_item['title'],  # For fuzzy matching
			valid = True,
			arg = list_item['url'],
			icon = 'label.png'  # Using label icon for lists
		)
	
	# Add folder results
	for folder in folders_results:
		wf3.add_item(
			title = '[Folder] ' + folder['title'],
			subtitle = f"ClickUp Folder in {folder['space_name']}",
			match = folder['title'],  # For fuzzy matching
			valid = True,
			arg = folder['url'],
			icon = 'settings.png'  # Using settings icon for folders
		)
	
	# Add space results
	for space in spaces_results:
		wf3.add_item(
			title = '[Space] ' + space['title'],
			subtitle = 'ClickUp Space',
			match = space['title'],  # For fuzzy matching
			valid = True,
			arg = space['url'],
			icon = 'settings.png'  # Using settings icon for spaces
		)
	
	wf3.send_feedback()


if __name__ == "__main__":
	wf = Workflow()
	log = wf.logger
	sys.exit(wf.run(main))
