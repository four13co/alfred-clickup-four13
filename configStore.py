#!/usr/bin/env python
# encoding: utf-8
#
# Copyright  (c) 2020 Michael Schmidt-Korth
#
# GNU GPL v2.0 Licence. See https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
#
import sys
import argparse
import os
from main import DEBUG, formatDate
from workflow import Workflow, ICON_WEB, ICON_CLOCK, ICON_WARNING, ICON_GROUP, web, PasswordNotFound
from config import getConfigName, getUserInput, confNames
from workflow.notify import notify


def main(wf):
	updateConfiguration()


def updateConfiguration():
	'''Updates Workflow Settings or MacOS Keychain with user provided value.

----------
	'''
	if len(wf.args):
		query = wf.args[0]
	else:
		query = None

	configName = getConfigName(query)
	userInput = getUserInput(query, configName)
	if DEBUG > 1:
		log.debug('Query: ' + str(query))
	if configName == confNames['confApi']:
		if DEBUG > 0:
			log.debug(' [ Updating ' + configName + ' ]')
		if DEBUG > 1:
			log.debug('Current value: ')
		try:
			wf.get_password('clickUpAPI')
		except PasswordNotFound:
			if DEBUG > 0:
				log.debug('No value stored.')
			pass
		if DEBUG > 1:
			log.debug('New value: ')
		if userInput.strip() == '':
			wf.delete_password('clickUpAPI')
		else:
			wf.save_password('clickUpAPI', userInput)
	elif query == 'cu:config cache':
		if DEBUG > 0:
			log.debug(' [ Clearing cache ]')
		if DEBUG > 0:
			log.debug('Current value: ')
			log.debug(wf.cached_data('availableLabels', None, max_age = 600))
			log.debug(wf.cached_data('availableLists', None, max_age = 600))
		wf.clear_cache(lambda f: 'availableLabels')
		wf.clear_cache(lambda f: 'availableLists')
		if DEBUG > 0:
			log.debug('New value: ')
			log.debug(wf.cached_data('availableLabels', None, max_age = 600))
			log.debug(wf.cached_data('availableLists', None, max_age = 600))
		notify('Cleared Cache', 'Lists and labels will be retrieved from ClickUp again.')
		#Notify cache cleared
	elif configName == confNames['confSuperAgentChannel']:
		# Accept either "id|name" (from picker) or just "id" (from manual entry)
		if '|' in userInput:
			channel_id, channel_name = userInput.split('|', 1)
		else:
			channel_id, channel_name = userInput, ''
		channel_id = channel_id.strip()
		channel_name = channel_name.strip()
		if channel_id == '':
			if confNames['confSuperAgentChannel'] in wf.settings:
				wf.settings.pop(confNames['confSuperAgentChannel'])
			if 'superAgentChannelMeta' in wf.settings:
				wf.settings.pop('superAgentChannelMeta')
			wf.settings.save()
			notify('Super Agent Channel Cleared', 'cusa is now disabled until reconfigured.')
		else:
			wf.settings[confNames['confSuperAgentChannel']] = channel_id
			if channel_name:
				wf.settings['superAgentChannelMeta'] = {'name': channel_name}
			elif 'superAgentChannelMeta' in wf.settings:
				wf.settings.pop('superAgentChannelMeta')
			wf.settings.save()
			notify('Super Agent Channel Set', f'cusa <message> will post to {channel_name or channel_id}.')
		print("")
	elif configName == confNames['confSearchEntities'] and userInput.startswith('toggle:'):
		# Handle toggle command for search entities
		entity = userInput.replace('toggle:', '')
		
		from config import getConfigValue
		current_entities = (getConfigValue(confNames['confSearchEntities']) or 'tasks').split(',')
		
		if entity in ['docs', 'chats', 'lists', 'folders', 'spaces']:
			if entity in current_entities:
				# Remove it
				current_entities.remove(entity)
				action = 'Disabled'
			else:
				# Add it
				current_entities.append(entity)
				action = 'Enabled'
			
			# Always ensure tasks is included
			if 'tasks' not in current_entities:
				current_entities.insert(0, 'tasks')
			
			new_value = ','.join(current_entities)
			entity_name = {'docs': 'Documents', 'chats': 'Chat Channels', 'lists': 'Lists', 'folders': 'Folders', 'spaces': 'Spaces'}.get(entity, entity)
			
			# Update the setting
			updateSetting(confNames['confSearchEntities'], new_value)
			
			# Show notification
			notify(f'{action} {entity_name}', f'Search entities: {new_value}')
			
			# Return to search entities menu
			print(confNames['confSearchEntities'] + ' ')
		else:
			# Invalid entity, return to search entities menu
			notify('Invalid Entity', f'Cannot toggle {entity}')
			print(confNames['confSearchEntities'] + ' ')
	else:
		updateSetting(configName, userInput)
		# Show notification for saved settings
		setting_name = configName
		# Convert internal names to user-friendly names
		friendly_names = {
			'apiKey': 'API Key',
			'dueDate': 'Default Due Date',
			'list': 'Default List',
			'space': 'Space',
			'workspace': 'Workspace',
			'folder': 'Folder',
			'notification': 'Notification',
			'defaultTag': 'Default Tag',
			'hierarchyLimit': 'Hierarchy Limit',
			'userId': 'User ID',
			'searchEntities': 'Search Entities'
		}
		display_name = friendly_names.get(configName, configName or 'Setting')
		
		# Special handling for clearing values
		if userInput.strip() == '':
			if configName == 'folder' and userInput == 'none':
				notify('Setting Saved', f'{display_name} cleared (using space directly)')
			else:
				notify('Setting Cleared', f'{display_name} has been removed')
		else:
			# Special handling for notification true/false
			if configName == 'notification':
				value_display = 'Enabled' if userInput == 'true' else 'Disabled'
				notify('Setting Saved', f'{display_name} {value_display}')
			elif configName == confNames['confSearchEntities']:
				# For search entities, return to the menu after saving
				notify('Search Entities Updated', f'New configuration: {userInput}')
				print(confNames['confSearchEntities'] + ' ')
				return
			else:
				notify('Setting Saved', f'{display_name} has been updated')
		
		# Return to main config menu by outputting empty string
		print("")


def updateSetting(configName, userInput):
	'''Updates specific Workflow Setting.

----------
	@param str configName: The name of a configuration item-, e.g. 'dueDate'.
	@param str userInput: The user's input (configuration value).
	'''
	if DEBUG > 0:
		log.debug(' [ Updating ' + configName + ' ]')
		log.debug('Current value: ')
		log.debug(wf.settings[configName] if configName in wf.settings else '')
	if userInput.strip() == '':
		if configName == 'notification':
			wf.settings[configName] = 'false'
		else:
			wf.settings.pop(configName)
	else:
		if configName == 'notification' and userInput != 'true':
			wf.settings[configName] = 'false'
		else:
			wf.settings[configName] = userInput.strip()
	wf.settings.save()
	if DEBUG > 0:
		log.debug('New value: ')
		log.debug(wf.settings[configName])


if __name__ == "__main__":
	wf = Workflow()
	wf3 = Workflow()
	log = wf.logger
	sys.exit(wf.run(main))
