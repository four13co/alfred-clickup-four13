#!/usr/bin/env python
# encoding: utf-8
#
# Copyright  (c) 2020 Michael Schmidt-Korth
#
# GNU GPL v2.0 Licence. See https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
#
import sys
from workflow import Workflow, ICON_WARNING, web, PasswordNotFound
from validation import validate_clickup_id, validate_api_key

confNames = {'confApi': 'apiKey', 'confDue': 'dueDate', 'confList': 'list', 'confSpace': 'space', 'confTeam': 'workspace', 'confProject': 'folder', 'confNotification': 'notification', 'confDefaultTag': 'defaultTag', 'confUser': 'userId', 'confSearchScope': 'searchScope', 'confSearchEntities': 'searchEntities', 'confSuperAgentChannel': 'superAgentChannel'}


def maskApiKey(apiKey):
	'''Masks an API key for security display, showing only first 4 and last 4 characters.
	
	Args:
		apiKey (str): The API key to mask
		
	Returns:
		str: Masked API key (e.g., "pk_3****MD3G" for short keys, "pk_30050********************************MD3G" for long keys)
	'''
	if not apiKey:
		return ''
	
	if len(apiKey) <= 8:
		# For very short keys, show first 2 and last 2 with asterisks
		return apiKey[:2] + '****' + apiKey[-2:]
	elif len(apiKey) <= 12:
		# For short keys, show first 4 and last 4 with asterisks
		return apiKey[:4] + '****' + apiKey[-4:]
	else:
		# For long keys (typical ClickUp format), show first 8, asterisks, and last 4
		return apiKey[:8] + '*' * 32 + apiKey[-4:]


def main(wf):
	configuration()


def configuration():
	'''Provides list items to configure the workflow.

----------
	'''
	if len(wf.args):
		query = wf.args[0]
	else:
		query = None

	if not query:
		apiKeyValue = getConfigValue(confNames['confApi'])
		dueValue = getConfigValue(confNames['confDue'])
		listValue = getConfigValue(confNames['confList'])
		spaceValue = getConfigValue(confNames['confSpace'])
		teamValue = getConfigValue(confNames['confTeam'])
		projectValue = getConfigValue(confNames['confProject'])
		notificationValue = getConfigValue(confNames['confNotification'])
		if notificationValue == 'true':
			notificationValue = '✓'
		elif notificationValue == 'false':
			notificationValue = '✗'
		defaultTagValue = getConfigValue(confNames['confDefaultTag'])
		searchScopeValue = getConfigValue(confNames['confSearchScope']) or 'auto'
		searchEntitiesValue = getConfigValue(confNames['confSearchEntities']) or 'tasks'

		# Mask API key for security - match ClickUp's format: pk_30050********************************MD3G
		maskedApiKey = maskApiKey(apiKeyValue)
		# Mark required fields with asterisk
		wf3.add_item(title = ('*' if not apiKeyValue else '') + 'Set API key' + (' (' + maskedApiKey + ')' if maskedApiKey else ''), subtitle = 'Your personal ClickUp API key/token. (Required)', valid = False, autocomplete = confNames['confApi'] + ' ', icon='icon.png' if apiKeyValue else 'error.png')
		wf3.add_item(title = 'Set default due date' + (' (' + dueValue + ')' if dueValue else ''), subtitle = 'e.g. m30 (in 30 minutes), h2 (in two hours), d1 (in one day), w1 (in one week).', valid = False, autocomplete = confNames['confDue'] + ' ')
		wf3.add_item(title = ('*' if not teamValue else '') + 'Set ClickUp workspace' + (' (' + teamValue + ')' if teamValue else ''), subtitle = 'Workspace that defines which tasks can be searched. (Required)', valid = False, autocomplete = confNames['confTeam'] + ' ', icon='icon.png' if teamValue else 'error.png')
		wf3.add_item(title = ('*' if not spaceValue else '') + 'Set ClickUp space' + (' (' + spaceValue + ')' if spaceValue else ''), subtitle = 'Space that defines your available labels and priorities. (Required)', valid = False, autocomplete = confNames['confSpace'] + ' ', icon='icon.png' if spaceValue else 'error.png')
		wf3.add_item(title = 'Set ClickUp folder' + (' (' + projectValue + ')' if projectValue else ''), subtitle = 'Folder that which tasks can be searched. The Folder must be part of the workspace.', valid = False, autocomplete = confNames['confProject'] + ' ')
		wf3.add_item(title = ('*' if not listValue else '') + 'Set default ClickUp list' + (' (' + listValue + ')' if listValue else ''), subtitle = 'List you want to add tasks to by default. (Required)', valid = False, autocomplete = confNames['confList'] + ' ', icon='icon.png' if listValue else 'error.png')
		wf3.add_item(title = 'Set Show Notification' + (' (' + notificationValue + ')' if notificationValue else ''), subtitle = 'Show notification after creating task?', valid = False, autocomplete = confNames['confNotification'] + ' ')
		wf3.add_item(title = 'Set default Tag' + (' (' + defaultTagValue + ')' if defaultTagValue else ''), subtitle = 'Tag that is added to all new tasks.', valid = False, autocomplete = confNames['confDefaultTag'] + ' ')
		# Display formatted search scope value
		scopeDisplay = {'list': 'Performance', 'folder': 'Balanced', 'space': 'Comprehensive', 'auto': 'Auto'}.get(searchScopeValue, searchScopeValue)
		wf3.add_item(title = 'Set Search Scope' + (' (' + scopeDisplay + ')' if searchScopeValue else ''), subtitle = 'Performance (List), Balanced (Folder), Comprehensive (Space), or Auto', valid = False, autocomplete = confNames['confSearchScope'] + ' ')
		# Display formatted search entities value
		entities = searchEntitiesValue.split(',')
		enabled_types = []
		if 'tasks' in entities:
			enabled_types.append('Tasks')
		if 'docs' in entities:
			enabled_types.append('Docs')
		if 'chats' in entities:
			enabled_types.append('Chats')
		if 'lists' in entities:
			enabled_types.append('Lists')
		if 'folders' in entities:
			enabled_types.append('Folders')
		if 'spaces' in entities:
			enabled_types.append('Spaces')
		entitiesDisplay = ', '.join(enabled_types) if enabled_types else 'Tasks'
		wf3.add_item(title = 'Configure Search Types' + (' (' + entitiesDisplay + ')' if entitiesDisplay else ''), subtitle = 'Toggle which entity types to search', valid = False, autocomplete = confNames['confSearchEntities'] + ' ')
		superAgentChannelValue = getConfigValue(confNames['confSuperAgentChannel'])
		superAgentChannelMeta = wf.settings.get('superAgentChannelMeta') or {}
		superAgentDisplay = superAgentChannelMeta.get('name') or superAgentChannelValue or ''
		wf3.add_item(title = 'Set Super Agent channel' + (' (' + superAgentDisplay + ')' if superAgentDisplay else ''), subtitle = 'Chat channel that cusa <message> posts to.', valid = False, autocomplete = confNames['confSuperAgentChannel'] + ' ')
		wf3.add_item(title = 'Validate Configuration', subtitle = 'Check if provided configuration parameters are valid.', valid = False, autocomplete = 'validate', icon = './settings.png')
		clearCache = wf3.add_item(title = 'Clear Cache', subtitle = 'Clear list of available labels and lists to be retrieved again.', valid = True, arg = 'cu:config cache', icon = './settings.png')
		clearCache.setvar('isSubmitted', 'true') # No secondary screen necessary
	elif query.startswith(confNames['confApi'] + ' '): # Check for suffix ' ' which we add automatically so user can type immediately
		userInput = query.replace(confNames['confApi'] + ' ', '')
		# Mask the API key input for security - prevent shoulder surfing and screen recording exposure
		maskedInput = maskApiKey(userInput) if userInput else ''
		apiItem = wf3.add_item(title = 'Enter API key: ' + maskedInput, subtitle = 'Confirm to save to keychain?', valid = True, arg = 'cu:config ' + query)
		apiItem.setvar('isSubmitted', 'true')
	elif query.startswith(confNames['confDue'] + ' '):
		userInput = query.replace(confNames['confDue'] + ' ', '')
		dueType = userInput[:1]
		if dueType == 'm':
			dueType = 'minutes'
		elif dueType == 'h':
			dueType = 'hours'
		elif dueType == 'd':
			dueType = 'days'
		elif dueType == 'w':
			dueType = 'weeks'
		dueTime = userInput[1:]
		output = dueTime + ' ' + dueType
		if not dueType.isalpha() or not dueTime.isnumeric():
			output = '(Invalid input).'
		dueItem = wf3.add_item(title = 'Enter default due date (e.g. d2): ' + output, subtitle = 'Save?', valid = True, arg = 'cu:config ' + query)
		dueItem.setvar('isSubmitted', 'true')
	elif query.startswith(confNames['confList'] + ' '):
		# Fetch and display lists
		search_query = query.replace(confNames['confList'] + ' ', '').strip()
		
		# Get space or folder ID
		space_id = getConfigValue(confNames['confSpace'])
		folder_id = getConfigValue(confNames['confProject'])
		
		if not space_id:
			wf3.add_item(
				title='Space not set',
				subtitle='Please set your space first',
				valid=False,
				icon='error.png'
			)
		else:
			try:
				apiKey = wf.get_password('clickUpAPI')
				
				# Determine which endpoint to use
				if folder_id:
					url = f'https://api.clickup.com/api/v2/folder/{folder_id}/list'
					cache_key = f'lists_folder_{folder_id}'
				else:
					url = f'https://api.clickup.com/api/v2/space/{space_id}/list'
					cache_key = f'lists_space_{space_id}'
				
				# Fetch lists from cache or API
				lists = wf.cached_data(cache_key, None, max_age=300)  # 5 min cache
				
				if not lists:
					headers = {
						'Authorization': validate_api_key(apiKey),
						'Content-Type': 'application/json'
					}
					try:
						response = web.get(url, headers=headers, timeout=30)
						response.raise_for_status()
						data = response.json()
						lists = data.get('lists', [])
						wf.cache_data(cache_key, lists)
					except:
						wf3.add_item(
							title='Error fetching lists',
							subtitle='Check space/folder ID and internet connection',
							valid=False,
							icon='error.png'
						)
						wf3.send_feedback()
						return
				
				# Filter lists
				if search_query:
					filtered = [l for l in lists if search_query.lower() in l['name'].lower()]
				else:
					filtered = lists
				
				if filtered:
					for list_item in filtered:
						task_count = list_item.get('task_count', 0)
						wf3.add_item(
							title='📝 ' + list_item['name'],
							subtitle=f"List ID: {list_item['id']} - {task_count} tasks",
							arg=f"cu:config {confNames['confList']} {list_item['id']}",
							valid=True,
							icon='label.png'  # Using label icon for lists
						)
				else:
					# Allow manual ID entry
					if search_query and search_query.isnumeric():
						wf3.add_item(
							title=f'Use list ID: {search_query}',
							subtitle='Press Enter to use this ID',
							arg=f"cu:config {confNames['confList']} {search_query}",
							valid=True
						)
					else:
						wf3.add_item(
							title='No lists found',
							subtitle='Type to search or enter a list ID',
							valid=False
						)
			except PasswordNotFound:
				wf3.add_item(
					title='API key not set',
					subtitle='Please set your API key first',
					valid=False,
					icon='error.png'
				)
	elif query.startswith(confNames['confSpace'] + ' '):
		# Fetch and display spaces for the selected workspace
		search_query = query.replace(confNames['confSpace'] + ' ', '').strip()
		
		# Get workspace ID
		workspace_id = getConfigValue(confNames['confTeam'])
		if not workspace_id:
			wf3.add_item(
				title='Workspace not set',
				subtitle='Please set your workspace first',
				valid=False,
				icon='error.png'
			)
		else:
			try:
				apiKey = wf.get_password('clickUpAPI')
				
				# Fetch spaces from cache or API
				cache_key = f'spaces_{workspace_id}'
				spaces = wf.cached_data(cache_key, None, max_age=300)  # 5 min cache
				
				if not spaces:
					validated_workspace_id = validate_clickup_id(workspace_id, 'workspace')
					url = f'https://api.clickup.com/api/v2/team/{validated_workspace_id}/space'
					headers = {
						'Authorization': validate_api_key(apiKey),
						'Content-Type': 'application/json'
					}
					try:
						response = web.get(url, headers=headers, timeout=30)
						response.raise_for_status()
						data = response.json()
						spaces = data.get('spaces', [])
						wf.cache_data(cache_key, spaces)
					except:
						wf3.add_item(
							title='Error fetching spaces',
							subtitle='Check workspace ID and internet connection',
							valid=False,
							icon='error.png'
						)
						wf3.send_feedback()
						return
				
				# Filter spaces
				if search_query:
					filtered = [s for s in spaces if search_query.lower() in s['name'].lower()]
				else:
					filtered = spaces
				
				if filtered:
					for space in filtered:
						wf3.add_item(
							title='🏢 ' + space['name'],
							subtitle=f"ID: {space['id']} - Select this space",
							arg=f"cu:config {confNames['confSpace']} {space['id']}",
							valid=True
						)
				else:
					# Allow manual ID entry
					if search_query and search_query.isnumeric():
						wf3.add_item(
							title=f'Use space ID: {search_query}',
							subtitle='Press Enter to use this ID',
							arg=f"cu:config {confNames['confSpace']} {search_query}",
							valid=True
						)
					else:
						wf3.add_item(
							title='No spaces found',
							subtitle='Type to search or enter a space ID',
							valid=False
						)
			except PasswordNotFound:
				wf3.add_item(
					title='API key not set',
					subtitle='Please set your API key first',
					valid=False,
					icon='error.png'
				)
	elif query.startswith(confNames['confTeam'] + ' '):
		# Fetch and display workspaces
		search_query = query.replace(confNames['confTeam'] + ' ', '').strip()
		
		# Get API key
		try:
			apiKey = wf.get_password('clickUpAPI')
			
			# Fetch workspaces from cache or API
			workspaces = wf.cached_data('workspaces', None, max_age=300)  # 5 min cache
			
			if not workspaces:
				url = 'https://api.clickup.com/api/v2/team'
				headers = {
					'Authorization': validate_api_key(apiKey),
					'Content-Type': 'application/json'
				}
				try:
					response = web.get(url, headers=headers, timeout=30)
					response.raise_for_status()
					data = response.json()
					workspaces = data.get('teams', [])
					wf.cache_data('workspaces', workspaces)
				except:
					wf3.add_item(
						title='Error fetching workspaces',
						subtitle='Check your API key and internet connection',
						valid=False,
						icon='error.png'
					)
					wf3.send_feedback()
					return
			
			# Filter workspaces
			if search_query:
				filtered = [w for w in workspaces if search_query.lower() in w['name'].lower()]
			else:
				filtered = workspaces
			
			if filtered:
				for workspace in filtered:
					wf3.add_item(
						title='🏠 ' + workspace['name'],
						subtitle=f"ID: {workspace['id']} - Select this workspace",
						arg=f"cu:config {confNames['confTeam']} {workspace['id']}",
						valid=True
					)
			else:
				# Allow manual ID entry
				if search_query and search_query.isnumeric():
					wf3.add_item(
						title=f'Use workspace ID: {search_query}',
						subtitle='Press Enter to use this ID',
						arg=f"cu:config {confNames['confTeam']} {search_query}",
						valid=True
					)
				else:
					wf3.add_item(
						title='No workspaces found',
						subtitle='Type to search or enter a workspace ID',
						valid=False
					)
		except PasswordNotFound:
			wf3.add_item(
				title='API key not set',
				subtitle='Please set your API key first',
				valid=False,
				icon='error.png'
			)
	elif query.startswith(confNames['confProject'] + ' '):
		# Fetch and display folders
		search_query = query.replace(confNames['confProject'] + ' ', '').strip()
		
		# Get space ID
		space_id = getConfigValue(confNames['confSpace'])
		
		if not space_id:
			wf3.add_item(
				title='Space not set',
				subtitle='Please set your space first',
				valid=False,
				icon='error.png'
			)
		else:
			try:
				apiKey = wf.get_password('clickUpAPI')
				
				# Fetch folders from cache or API
				cache_key = f'folders_{space_id}'
				folders = wf.cached_data(cache_key, None, max_age=300)  # 5 min cache
				
				if not folders:
					validated_space_id = validate_clickup_id(space_id, 'space')
					url = f'https://api.clickup.com/api/v2/space/{validated_space_id}/folder'
					headers = {
						'Authorization': validate_api_key(apiKey),
						'Content-Type': 'application/json'
					}
					try:
						response = web.get(url, headers=headers, timeout=30)
						response.raise_for_status()
						data = response.json()
						folders = data.get('folders', [])
						wf.cache_data(cache_key, folders)
					except:
						wf3.add_item(
							title='Error fetching folders',
							subtitle='Check space ID and internet connection',
							valid=False,
							icon='error.png'
						)
						wf3.send_feedback()
						return
				
				# Add "No folder" option
				wf3.add_item(
					title='No folder (use space directly)',
					subtitle='Tasks will be organized at space level',
					arg=f"cu:config {confNames['confProject']} none",
					valid=True
				)
				
				# Filter folders
				if search_query:
					filtered = [f for f in folders if search_query.lower() in f['name'].lower()]
				else:
					filtered = folders
				
				if filtered:
					for folder in filtered:
						list_count = len(folder.get('lists', []))
						wf3.add_item(
							title='📁 ' + folder['name'],
							subtitle=f"ID: {folder['id']} - {list_count} lists",
							arg=f"cu:config {confNames['confProject']} {folder['id']}",
							valid=True
						)
				else:
					# Allow manual ID entry
					if search_query and search_query.isnumeric():
						wf3.add_item(
							title=f'Use folder ID: {search_query}',
							subtitle='Press Enter to use this ID',
							arg=f"cu:config {confNames['confProject']} {search_query}",
							valid=True
						)
					elif search_query and search_query != 'no':
						wf3.add_item(
							title='No folders found',
							subtitle='Type to search or enter a folder ID',
							valid=False
						)
			except PasswordNotFound:
				wf3.add_item(
					title='API key not set',
					subtitle='Please set your API key first',
					valid=False,
					icon='error.png'
				)
	elif query.startswith(confNames['confDefaultTag'] + ' '):
		userInput = query.replace(confNames['confDefaultTag'] + ' ', '')
		if ',' in userInput:
			userInput = '(Invalid input).'
		tagItem = wf3.add_item(title = 'Enter default tag: ' + userInput.lower(), subtitle = 'Save?', valid = True, arg = 'cu:config ' + query)
		tagItem.setvar('isSubmitted', 'true')
	elif query.startswith(confNames['confNotification'] + ' '):
		userInput = query.replace(confNames['confNotification'] + ' ', '')
		if userInput == '':
			# Show options when no input provided
			trueItem = wf3.add_item(title = 'Enable notifications ✓', subtitle = 'Show notification after creating tasks', valid = True, arg = 'cu:config ' + confNames['confNotification'] + ' true')
			trueItem.setvar('isSubmitted', 'true')
			falseItem = wf3.add_item(title = 'Disable notifications ✗', subtitle = 'No notification after creating tasks', valid = True, arg = 'cu:config ' + confNames['confNotification'] + ' false')
			falseItem.setvar('isSubmitted', 'true')
		elif userInput == 'true':
			userInput = '✓'
			notificationItem = wf3.add_item(title = 'Enable notification: ' + userInput, subtitle = 'Save?', valid = True, arg = 'cu:config ' + query)
			notificationItem.setvar('isSubmitted', 'true')
		elif userInput == 'false':
			userInput = '✗'
			notificationItem = wf3.add_item(title = 'Disable notification: ' + userInput, subtitle = 'Save?', valid = True, arg = 'cu:config ' + query)
			notificationItem.setvar('isSubmitted', 'true')
		else:
			# Invalid input
			wf3.add_item(title = 'Invalid input: ' + userInput, subtitle = 'Please select an option above', valid = False)
			trueItem = wf3.add_item(title = 'Enable notifications ✓', subtitle = 'Show notification after creating tasks', valid = True, arg = 'cu:config ' + confNames['confNotification'] + ' true')
			trueItem.setvar('isSubmitted', 'true')
			falseItem = wf3.add_item(title = 'Disable notifications ✗', subtitle = 'No notification after creating tasks', valid = True, arg = 'cu:config ' + confNames['confNotification'] + ' false')
			falseItem.setvar('isSubmitted', 'true')
	elif query.startswith(confNames['confSearchScope'] + ' '):
		userInput = query.replace(confNames['confSearchScope'] + ' ', '').strip()
		if userInput == '':
			# Show all options when no input provided
			listItem = wf3.add_item(title = 'Performance Mode (List Only)', subtitle = 'Search only your default list - fastest', valid = True, arg = 'cu:config ' + confNames['confSearchScope'] + ' list')
			listItem.setvar('isSubmitted', 'true')
			folderItem = wf3.add_item(title = 'Balanced Mode (Folder)', subtitle = 'Search your entire folder - good balance', valid = True, arg = 'cu:config ' + confNames['confSearchScope'] + ' folder')
			folderItem.setvar('isSubmitted', 'true')
			spaceItem = wf3.add_item(title = 'Comprehensive Mode (Space)', subtitle = 'Search your entire space - slowest', valid = True, arg = 'cu:config ' + confNames['confSearchScope'] + ' space')
			spaceItem.setvar('isSubmitted', 'true')
			autoItem = wf3.add_item(title = 'You Pick (Auto)', subtitle = 'Automatically adjusts based on result count', valid = True, arg = 'cu:config ' + confNames['confSearchScope'] + ' auto')
			autoItem.setvar('isSubmitted', 'true')
		elif userInput in ['list', 'folder', 'space', 'auto']:
			# Valid selection, confirm it
			displayName = {'list': 'Performance Mode', 'folder': 'Balanced Mode', 'space': 'Comprehensive Mode', 'auto': 'You Pick (Auto)'}.get(userInput, userInput)
			confirmItem = wf3.add_item(title = 'Set search scope to: ' + displayName, subtitle = 'Save?', valid = True, arg = 'cu:config ' + query)
			confirmItem.setvar('isSubmitted', 'true')
		else:
			# Invalid input, show options
			wf3.add_item(title = 'Invalid input: ' + userInput, subtitle = 'Please select an option below', valid = False)
			listItem = wf3.add_item(title = 'Performance Mode (List Only)', subtitle = 'Search only your default list - fastest', valid = True, arg = 'cu:config ' + confNames['confSearchScope'] + ' list')
			listItem.setvar('isSubmitted', 'true')
			folderItem = wf3.add_item(title = 'Balanced Mode (Folder)', subtitle = 'Search your entire folder - good balance', valid = True, arg = 'cu:config ' + confNames['confSearchScope'] + ' folder')
			folderItem.setvar('isSubmitted', 'true')
			spaceItem = wf3.add_item(title = 'Comprehensive Mode (Space)', subtitle = 'Search your entire space - slowest', valid = True, arg = 'cu:config ' + confNames['confSearchScope'] + ' space')
			spaceItem.setvar('isSubmitted', 'true')
			autoItem = wf3.add_item(title = 'You Pick (Auto)', subtitle = 'Automatically adjusts based on result count', valid = True, arg = 'cu:config ' + confNames['confSearchScope'] + ' auto')
			autoItem.setvar('isSubmitted', 'true')
	elif query.startswith(confNames['confSearchEntities'] + ' '):
		userInput = query.replace(confNames['confSearchEntities'] + ' ', '').strip()
		
		# Get current enabled entities
		current_entities = (getConfigValue(confNames['confSearchEntities']) or 'tasks').split(',')
		
		if userInput == '':
			# Show toggle options
			wf3.add_item(title = 'Toggle Search Entity Types', subtitle = 'Select an entity type to toggle on/off', valid = False)
			
			# Tasks (always enabled)
			wf3.add_item(
				title = '✓ Tasks (always enabled)', 
				subtitle = 'Search ClickUp tasks', 
				valid = False,
				icon = 'icon.png'
			)
			
			# Documents
			docs_enabled = 'docs' in current_entities
			docsItem = wf3.add_item(
				title = ('✓' if docs_enabled else '○') + ' Documents', 
				subtitle = 'Click to ' + ('disable' if docs_enabled else 'enable') + ' document search', 
				valid = True, 
				arg = 'cu:config ' + confNames['confSearchEntities'] + ' toggle:docs',
				icon = 'note.png'
			)
			docsItem.setvar('isSubmitted', 'false')
			
			# Chat Channels
			chats_enabled = 'chats' in current_entities
			chatsItem = wf3.add_item(
				title = ('✓' if chats_enabled else '○') + ' Chat Channels', 
				subtitle = 'Click to ' + ('disable' if chats_enabled else 'enable') + ' chat channel search', 
				valid = True, 
				arg = 'cu:config ' + confNames['confSearchEntities'] + ' toggle:chats',
				icon = 'label.png'
			)
			chatsItem.setvar('isSubmitted', 'false')
			
			# Lists
			lists_enabled = 'lists' in current_entities
			listsItem = wf3.add_item(
				title = ('✓' if lists_enabled else '○') + ' Lists', 
				subtitle = 'Click to ' + ('disable' if lists_enabled else 'enable') + ' list search', 
				valid = True, 
				arg = 'cu:config ' + confNames['confSearchEntities'] + ' toggle:lists',
				icon = 'label.png'
			)
			listsItem.setvar('isSubmitted', 'false')
			
			# Folders
			folders_enabled = 'folders' in current_entities
			foldersItem = wf3.add_item(
				title = ('✓' if folders_enabled else '○') + ' Folders', 
				subtitle = 'Click to ' + ('disable' if folders_enabled else 'enable') + ' folder search', 
				valid = True, 
				arg = 'cu:config ' + confNames['confSearchEntities'] + ' toggle:folders',
				icon = 'settings.png'
			)
			foldersItem.setvar('isSubmitted', 'false')
			
			# Spaces
			spaces_enabled = 'spaces' in current_entities
			spacesItem = wf3.add_item(
				title = ('✓' if spaces_enabled else '○') + ' Spaces', 
				subtitle = 'Click to ' + ('disable' if spaces_enabled else 'enable') + ' space search', 
				valid = True, 
				arg = 'cu:config ' + confNames['confSearchEntities'] + ' toggle:spaces',
				icon = 'settings.png'
			)
			spacesItem.setvar('isSubmitted', 'false')
			
		elif userInput.startswith('toggle:'):
			# This case is now handled directly by configStore.py
			# We should not reach here in normal flow, but if we do, show an error
			wf3.add_item(title = 'Toggle processing error', subtitle = 'This should be handled by configStore.py', valid = False)
		else:
			# Direct setting of entities (backward compatibility)
			# Validate the input
			entities = userInput.split(',')
			valid_entities = ['tasks', 'docs', 'chats', 'lists', 'folders', 'spaces']
			invalid = [e for e in entities if e not in valid_entities]
			
			if invalid:
				wf3.add_item(title = 'Invalid entities: ' + ', '.join(invalid), subtitle = 'Valid: tasks, docs, chats, lists, folders, spaces', valid = False)
			else:
				# Always ensure tasks is included
				if 'tasks' not in entities:
					entities.insert(0, 'tasks')
				
				confirmItem = wf3.add_item(
					title = 'Set search entities to: ' + ', '.join(entities), 
					subtitle = 'Save?', 
					valid = True, 
					arg = 'cu:config ' + query
				)
				confirmItem.setvar('isSubmitted', 'true')
	elif query.startswith(confNames['confSuperAgentChannel'] + ' '):
		# Fetch and display chat channels for the configured workspace
		search_query = query.replace(confNames['confSuperAgentChannel'] + ' ', '').strip()
		workspace_id = getConfigValue(confNames['confTeam'])
		if not workspace_id:
			wf3.add_item(
				title='Workspace not set',
				subtitle='Please set your workspace first',
				valid=False,
				icon='error.png'
			)
		else:
			try:
				apiKey = wf.get_password('clickUpAPI')
				cache_key = f'chat_channels_{workspace_id}'
				channels = wf.cached_data(cache_key, None, max_age=300)
				validated_workspace_id = None
				if not channels:
					try:
						validated_workspace_id = validate_clickup_id(workspace_id, 'workspace')
						url = f'https://api.clickup.com/api/v3/workspaces/{validated_workspace_id}/chat/channels'
						headers = {
							'Authorization': validate_api_key(apiKey),
							'Content-Type': 'application/json'
						}
						response = web.get(url, headers=headers, timeout=30)
						response.raise_for_status()
						data = response.json()
						channels = data.get('channels', data.get('data', []))
					except:
						wf3.add_item(
							title='Error fetching chat channels',
							subtitle='Check workspace ID and internet connection',
							valid=False,
							icon='error.png'
						)
						wf3.send_feedback()
						return

				# Enrich any unnamed channels (DMs/group DMs) with member info.
				# Runs whether channels came from cache or fresh fetch — handles older
				# unenriched cache entries from earlier workflow versions.
				needs_enrich = any(
					not (c.get('name') or '').strip() and not c.get('members')
					for c in channels
				)
				if needs_enrich:
					try:
						if validated_workspace_id is None:
							validated_workspace_id = validate_clickup_id(workspace_id, 'workspace')
						headers = {
							'Authorization': validate_api_key(apiKey),
							'Content-Type': 'application/json'
						}
						# Identify the current user so we can exclude them from DM labels
						self_user_id = getConfigValue(confNames['confUser'])
						for channel in channels:
							if (channel.get('name') or '').strip():
								continue
							if channel.get('members'):
								continue
							ch_id = channel.get('id')
							if not ch_id:
								continue
							try:
								members_url = f'https://api.clickup.com/api/v3/workspaces/{validated_workspace_id}/chat/channels/{ch_id}/members'
								members_response = web.get(members_url, headers=headers, timeout=15)
								members_response.raise_for_status()
								members_payload = members_response.json()
								raw_members = members_payload.get('data', members_payload.get('members', members_payload if isinstance(members_payload, list) else []))
								# Drop the current user so a 1:1 DM displays as the *other* person.
								if self_user_id:
									raw_members = [m for m in raw_members if str(m.get('id')) != str(self_user_id)]
								channel['members'] = raw_members
							except Exception:
								pass
						wf.cache_data(cache_key, channels)
					except ValueError:
						pass

				# Build a friendly label per channel — DMs in ClickUp v3 have no `name`
				def _channel_label(channel):
					name = (channel.get('name') or '').strip()
					if name:
						return name, 'channel'
					# Try common DM/participant shapes the v3 API may return
					members = channel.get('members') or channel.get('users') or channel.get('participants') or []
					member_names = []
					for m in members:
						user = m.get('user') if isinstance(m, dict) else None
						if isinstance(user, dict):
							member_names.append(user.get('username') or user.get('email') or '')
						elif isinstance(m, dict):
							member_names.append(m.get('username') or m.get('email') or m.get('name') or '')
					member_names = [n for n in member_names if n]
					ch_type = (channel.get('type') or '').lower()
					if member_names:
						joined = ', '.join(member_names[:3])
						if len(member_names) > 3:
							joined += f' +{len(member_names) - 3}'
						label_type = 'dm' if ch_type in ('dm', 'direct_message', 'direct') or len(member_names) <= 2 else 'group'
						return f'DM: {joined}' if label_type == 'dm' else f'Group: {joined}', label_type
					# Fall back: short id with explicit type
					short_id = channel.get('id', '')[:14]
					return f'{ch_type or "channel"} {short_id}', ch_type or 'channel'

				# Filter on the friendly label so DM searches work too
				if search_query:
					q = search_query.lower()
					filtered = [c for c in channels if q in _channel_label(c)[0].lower() or q in (c.get('id') or '').lower()]
				else:
					filtered = channels
				if filtered:
					for channel in filtered:
						channel_id = channel.get('id') or ''
						channel_label, channel_type = _channel_label(channel)
						type_badge = '👥' if channel_type in ('group',) else ('✉️' if channel_type in ('dm', 'direct_message', 'direct') else '💬')
						channelItem = wf3.add_item(
							title=f'{type_badge} {channel_label}',
							subtitle=f"{channel_type or 'channel'} · ID {channel_id} — Use as Super Agent target",
							arg=f"cu:config {confNames['confSuperAgentChannel']} {channel_id}|{channel_label}",
							valid=True
						)
						channelItem.setvar('isSubmitted', 'true')
				else:
					if search_query:
						wf3.add_item(
							title='No channels found',
							subtitle='Type to search by channel name',
							valid=False
						)
					else:
						wf3.add_item(
							title='No chat channels available',
							subtitle='Create one in ClickUp first',
							valid=False
						)
			except PasswordNotFound:
				wf3.add_item(
					title='API key not set',
					subtitle='Please set your API key first',
					valid=False,
					icon='error.png'
				)
	elif query.startswith('validate'): # No suffix ' ' needed, as user is not expected to provide any input.
		wf3.add_item(title = 'Checking API Key: ' + ('✓' if checkClickUpId('list', 'confList') else '✗'), valid = True, arg = 'cu:config ')
		wf3.add_item(title = 'Checking List Id: ' + ('✓' if checkClickUpId('list', 'confList') else '✗'), valid = True, arg = 'cu:config ')
		wf3.add_item(title = 'Checking Space Id: ' + ('✓' if checkClickUpId('space', 'confSpace') else '✗'), valid = True, arg = 'cu:config ')
		wf3.add_item(title = 'Checking Team Id: ' + ('✓' if checkClickUpId('team', 'confTeam') else '✗'), valid = True, arg = 'cu:config ')
		if getConfigValue(confNames['confProject']):
			wf3.add_item(title = 'Checking Project Id: ' + ('✓' if checkClickUpId('folder', 'confProject') else '✗'), valid = True, arg = 'cu:config ')
	wf3.send_feedback()


def getConfigName(query):
	'''Returns the name of a configuration item from a user's query, e.g. extracts 'defaultTag' from 'cu:config defaultTag'.

----------
	@param str query: The user's input.
	'''
	wf = Workflow()
	log = wf.logger
	hasValue = len(query.split(' ')) > 1
	if hasValue:
		# First element is our config name, whether there is a value or not
		return query.split(' ')[1]
	else:
		return query


def getUserInput(query, configName):
	'''Returns the value for a configuration item from a user's query, e.g. extracts 'to_sort' from 'cu:config defaultTag to_sort'.

----------
	@param str query: The user's input.
	@param str configName: The name of a configuration item-, e.g. 'dueDate'.
	'''
	return query.replace('cu:config ', '').replace(configName, '').strip()


def getConfigValue(configName):
	'''Returns the stored value for a configuration item Workflow settings or MacOS Keychain.

----------
	@param str configName: The name of a configuration item-, e.g. 'dueDate'.
	'''
	wf = Workflow()
	log = wf.logger
	if configName == confNames['confApi']:
		try:
			value = wf.get_password('clickUpAPI')
		except PasswordNotFound:
			value = None
			pass
	else:
		if configName in wf.settings:
			value = wf.settings[configName]
		else:
			value = None

	return value


def checkClickUpId(idType, configKey):
	'''Calls ClickUp API and returns whether call was successful or not..

----------
	@param str idType: The value to be used in the API URL.
	@param str configKey: The name of the setting to be retrieved.
	'''
	try:
		# Validate the ID based on its type
		id_value = getConfigValue(confNames[configKey])
		if not id_value:
			return False
		
		# Map idType to validation type
		validation_type = idType
		if idType == 'team':
			validation_type = 'workspace'
		elif idType == 'project':
			validation_type = 'folder'
			
		validated_id = validate_clickup_id(id_value, validation_type)
		url = f'https://api.clickup.com/api/v2/{idType}/{validated_id}'
		
		# Validate API key
		api_key = validate_api_key(getConfigValue(confNames['confApi']))
		headers = {
			'Authorization': api_key,
			'Content-Type': 'application/json'
		}
	except ValueError as e:
		log.error(f'Validation error in checkClickUpId: {e}')
		return False

	# Use requests instead of Workflow.web, as web does not return the response in case of failure (only 401 NOT_AUTHORIZED, which is the same for API key failure or listId etc. failure)
	import requests
	request = requests.get(url, headers = headers, timeout = 30)
	result = request.json()
	if 'ECODE' in result and result['ECODE'] == 'OAUTH_019': # Wrong API key
		return False
	elif 'ECODE' in result and result['ECODE'] == 'OAUTH_023': # Wrong ListId or team not authorized
		return False
	elif 'ECODE' in result and result['ECODE'] == 'OAUTH_027': # Wrong SpaceId/ProjectId or team not authorized
		return False
	elif idType != 'team' and 'id' in result and result['id'] == getConfigValue(confNames[configKey]) and 'name' in result and result['name'] != '':
		return True
	elif idType == 'team' and 'team' in result and 'id' in result['team'] and result['team']['id'] == getConfigValue(confNames[configKey]) and 'name' in result['team'] and result['team']['name'] != '':
		return True


if __name__ == "__main__":
	wf = Workflow()
	wf3 = Workflow()
	log = wf.logger
	sys.exit(wf.run(main))
