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
import hashlib
from main import DEBUG
from workflow import Workflow, ICON_WEB, ICON_CLOCK, ICON_WARNING, ICON_GROUP, web
from config import confNames, getConfigValue
from validation import validate_clickup_id, validate_api_key


def main(wf):
	getTasks(wf)


def safeStr(value):
	'''Safely convert any value to lowercase string, handling None'''
	if value is None:
		return ''
	return str(value).lower()

def filterAndScoreTasks(tasks, search_term):
	'''Filter tasks for relevance and add scoring for ranking.
	This replaces ClickUp's unreliable API query parameter.
	'''
	if not search_term:
		return tasks
		
	search_term_lower = search_term.lower()
	relevant_tasks = []
	
	for task in tasks:
		try:
			score = 0
			
			# Debug: Log the first few task names to see if they contain expected strings
			if DEBUG > 1 and len(relevant_tasks) < 3:
				task_name = safeStr(task.get('name', ''))
				print(f"DEBUG: Checking task '{task_name}' for '{search_term_lower}'", file=sys.stderr)
			
			# Check task name (highest priority)
			name = safeStr(task.get('name', ''))
			if search_term_lower in name:
				if name == search_term_lower:
					score += 10  # Exact match
				elif name.startswith(search_term_lower):
					score += 8   # Starts with
				else:
					score += 5   # Contains
			
			# Check description
			description = safeStr(task.get('description', ''))
			if search_term_lower in description:
				score += 2
			
			# Check task content/text
			text_content = safeStr(task.get('text_content', ''))
			if search_term_lower in text_content:
				score += 2
			
			# Check tags
			for tag in task.get('tags', []) or []:
				if tag:
					tag_name = safeStr(tag.get('name', ''))
					if search_term_lower in tag_name:
						score += 3
			
			# Check custom fields
			for cf in task.get('custom_fields', []) or []:
				if cf and cf.get('value') is not None:
					cf_value = safeStr(cf.get('value', ''))
					if search_term_lower in cf_value:
						score += 2
			
			# Check list name
			list_info = task.get('list', {}) or {}
			if list_info:
				list_name = safeStr(list_info.get('name', ''))
				if search_term_lower in list_name:
					score += 1
			
			# Check folder name
			folder_info = task.get('folder', {}) or {}
			if folder_info:
				folder_name = safeStr(folder_info.get('name', ''))
				if search_term_lower in folder_name:
					score += 1
			
			if score > 0:
				task['_relevance_score'] = score
				relevant_tasks.append(task)
				
		except Exception as e:
			# Log the error but continue processing other tasks
			print(f"Error processing task {task.get('id', 'unknown')}: {str(e)}", file=sys.stderr)
			continue
	
	# Debug: Log filtering summary
	if DEBUG > 0:
		print(f"DEBUG: filterAndScoreTasks processed {len(tasks)} tasks, found {len(relevant_tasks)} matches for '{search_term}'", file=sys.stderr)
		if len(relevant_tasks) == 0 and len(tasks) > 0:
			# Sample a few task names to see what we're working with
			sample_names = [safeStr(t.get('name', '')) for t in tasks[:5]]
			print(f"DEBUG: Sample task names: {sample_names}", file=sys.stderr)
	
	# Sort by relevance score (highest first)
	return sorted(relevant_tasks, key=lambda x: x.get('_relevance_score', 0), reverse=True)


def quickSearch(wf, log, url, headers, params, search_term, action='initial'):
	'''Fast iterative search that returns results in < 5 seconds.
	Uses action-based progression for user-controlled depth.
	'''
	import hashlib
	
	# Create session ID and parse action
	session_id = hashlib.md5(search_term.encode()).hexdigest()[:8]
	cache_key = f'search_session_{session_id}'
	
	# Parse action type and parameters
	if action.startswith('more_'):
		# Parse action like "more_updated_2" for strategy=updated, page=2
		parts = action.split('_')
		strategy = parts[1] if len(parts) > 1 else 'updated'
		page = int(parts[2]) if len(parts) > 2 else 1
		action_type = 'more'
	elif action.startswith('strategy_'):
		# Parse action like "strategy_created" to switch strategy
		strategy = action.split('_')[1] if '_' in action else 'updated'
		page = 0
		action_type = 'strategy'
	else:
		# Initial search
		strategy = 'updated'
		page = 0
		action_type = 'initial'
	
	# Get or create search session
	import time
	session = wf.cached_data(cache_key, max_age=600) or {
		'term': search_term,
		'strategies_tried': [],
		'results_by_strategy': {},
		'total_searched': 0,
		'created_at': time.time()
	}
	
	# Track strategy usage
	if strategy not in session['strategies_tried']:
		session['strategies_tried'].append(strategy)
	
	strategy_key = f"{strategy}_{page}"
	
	# Use cached results if available
	if strategy_key in session.get('results_by_strategy', {}):
		cached_results = session['results_by_strategy'][strategy_key]
		if DEBUG > 0:
			log.debug(f'Using cached results for {strategy_key}: {len(cached_results)} tasks')
		return cached_results, session
	
	# Prepare API parameters
	current_params = params.copy()
	current_params['page'] = page
	
	# Apply search strategy
	if strategy == 'updated':
		current_params['order_by'] = 'updated'
		current_params['reverse'] = True
	elif strategy == 'created':
		current_params['order_by'] = 'created'
		current_params['reverse'] = True  # Recent first
	elif strategy == 'due_date':
		current_params['order_by'] = 'due_date' 
		current_params['reverse'] = True
	
	# Make API call with timeout
	try:
		if DEBUG > 0:
			log.debug(f'Quick search: {strategy} page {page} for "{search_term}"')
		
		request = web.get(url, params=current_params, headers=headers, timeout=5)
		request.raise_for_status()
		data = request.json()
		tasks = data.get('tasks', [])
		
		# Filter tasks client-side
		matching_tasks = filterAndScoreTasks(tasks, search_term)
		
		# Cache results and update session
		if 'results_by_strategy' not in session:
			session['results_by_strategy'] = {}
		session['results_by_strategy'][strategy_key] = matching_tasks
		session['total_searched'] += len(tasks)
		
		# Save session
		wf.cache_data(cache_key, session)
		
		if DEBUG > 0:
			log.debug(f'Found {len(matching_tasks)}/{len(tasks)} matches (strategy: {strategy}, page: {page})')
		
		return matching_tasks, session
		
	except Exception as e:
		log.debug(f'Quick search error: {str(e)}')
		return [], session


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
	
	# For search mode, expand scope to be more comprehensive
	if len(wf.args) > 1 and wf.args[1] == 'search':
		# For search mode, default to team-level for maximum coverage
		# This ensures we search all accessible tasks, not just configured list/folder/space
		pass  # No scope restrictions for search - search at team level
	elif search_scope == 'list':
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
	# Differentiates between listing all Alfred-created tasks and searching for all tasks (any)
	if len(wf.args) > 1 and wf.args[1] == 'search':
		if DEBUG > 0:
			log.debug('[ Mode: Search (cus) ]')
		# For search mode, order by updated (most recent first) and exclude closed tasks
		params['order_by'] = 'updated'
		params['reverse'] = True
		params['include_closed'] = False
		params['subtasks'] = True
		params['page'] = 0
		# Note: Don't add ClickUp's 'query' parameter as it doesn't exist in the API
		# We'll do client-side filtering instead with pagination
	else:
		# For non-search modes, use the original due_date ordering
		params['order_by'] = 'due_date'
		params['page'] = 0
	
	if len(wf.args) > 1 and wf.args[1] == 'open':
		if DEBUG > 0:
			log.debug('[ Mode: Open tasks (cuo) ]')
		# from datetime import date, datetime, timezone, timedelta

		today = datetime.date.today()
		todayEndOfDay = datetime.datetime(today.year, today.month, today.day, 23, 59, 59)
		epoch = datetime.datetime(1970, 1, 1)
		todayEndOfDayMs = int((todayEndOfDay - epoch).total_seconds() / datetime.timedelta(microseconds = 1).total_seconds() / 1000)

		params['due_date_lt'] = todayEndOfDayMs
	elif len(wf.args) > 1 and wf.args[1] == 'search':
		# Search mode parameters already set above, no additional params needed here
		pass
	else:
		if DEBUG > 0:
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
		# Mask API key in headers for secure logging
		from config import maskApiKey
		safe_headers = headers.copy()
		if 'Authorization' in safe_headers:
			safe_headers['Authorization'] = maskApiKey(safe_headers['Authorization'])
		log.debug(safe_headers)
		log.debug(params)
	# Handle search mode with fast iterative search
	if len(wf.args) > 1 and wf.args[1] == 'search':
		search_term = wf.args[0] if len(wf.args) > 0 else ''
		action = wf.args[2] if len(wf.args) > 2 else 'initial'
		
		if DEBUG > 0:
			log.debug(f'FAST SEARCH MODE: "{search_term}" action={action}')
		
		# Perform quick search
		matching_tasks, session = quickSearch(wf, log, url, headers, params, search_term, action)
		
		if DEBUG > 0:
			log.debug(f'Quick search complete: {len(matching_tasks)} matches, {session["total_searched"]} tasks searched')
		
		# Collect all results from session for display
		all_results = []
		for strategy_key, tasks in session.get('results_by_strategy', {}).items():
			all_results.extend(tasks)
		
		# Remove duplicates and sort by relevance
		seen_ids = set()
		unique_results = []
		for task in all_results:
			task_id = task.get('id')
			if task_id not in seen_ids:
				seen_ids.add(task_id)
				unique_results.append(task)
		
		unique_results.sort(key=lambda x: x.get('_relevance_score', 0), reverse=True)
		
		# Add search action items FIRST for better UX
		if unique_results or session['total_searched'] > 0:
			# Determine current strategy info
			current_strategy = session['strategies_tried'][-1] if session['strategies_tried'] else 'updated'
			current_page = len([k for k in session.get('results_by_strategy', {}) if k.startswith(current_strategy)]) - 1
			
			# Add "Search More" action for current strategy
			if len(unique_results) > 0:  # Only if we've found some results
				next_page = current_page + 1
				wf3.add_item(
					title = f'🔍 Search Next 100 Tasks ({current_strategy})',
					subtitle = f'Found {len(unique_results)} matches so far • Searched {session["total_searched"]} tasks',
					valid = True,
					arg = f'cus {search_term} more_{current_strategy}_{next_page}',
					icon = 'icon.png'
				)
			
			# Add strategy switching options
			strategy_options = [
				('updated', 'Most Recently Updated'),
				('created', 'Most Recently Created'), 
				('due_date', 'By Due Date')
			]
			
			for strategy_id, strategy_name in strategy_options:
				if strategy_id not in session['strategies_tried']:
					wf3.add_item(
						title = f'📊 Try {strategy_name} Strategy',
						subtitle = f'Search tasks ordered by {strategy_name.lower()}',
						valid = True,
						arg = f'cus {search_term} strategy_{strategy_id}',
						icon = 'icon.png'
					)
		
		if not unique_results:
			if session['total_searched'] == 0:
				wf3.add_item(
					title = 'Start typing to search tasks...',
					subtitle = 'Enter search term to find matching tasks',
					valid = False,
					icon = 'note.png'
				)
			else:
				wf3.add_item(
					title = 'No tasks found.',
					subtitle = f'No tasks match "{search_term}" in {session["total_searched"]} tasks searched',
					valid = False,
					icon = 'note.png'
				)
			wf3.send_feedback()
			return
		
		# Create result structure for compatibility
		result = {'tasks': unique_results[:15]}  # Limit to top 15 results
	else:
		# Original single API call for non-search modes
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
	
	# Auto mode expansion logic - smart expansion based on search relevance
	# Note: Skip auto-expansion for search mode since we already use comprehensive pagination
	if search_scope == 'auto' and len(wf.args) > 1 and wf.args[1] == 'search':
		# For search mode, we already did comprehensive pagination, so skip expansion
		if DEBUG > 0:
			log.debug('Search mode: Skipping auto-expansion since pagination already provides comprehensive results')
		# Skip the entire auto-expansion section below
	elif search_scope == 'auto' and len(wf.args) > 1:
		# Keep the original auto-expansion logic for non-search modes
		all_tasks = list(result.get('tasks', []))  # Start with list-level tasks
		task_ids = {task['id'] for task in all_tasks}  # Track IDs to avoid duplicates
		search_query = wf.args[0].lower() if wf.args[0] else ''
		
		if DEBUG > 0:
			log.debug('Auto mode: Got %d tasks at list level' % len(all_tasks))
		
		# Count how many results are actually relevant to the search query
		relevant_count = 0
		if search_query:
			for task in all_tasks:
				task_name = task.get('name', '').lower()
				if search_query in task_name:
					relevant_count += 1
		
		if DEBUG > 0:
			log.debug('Auto mode: %d tasks contain search term "%s"' % (relevant_count, search_query))
		
		# Only expand if we have fewer than 10 relevant results
		should_expand = relevant_count < 10
		
		# Try folder level only if we need more relevant results
		if should_expand and getConfigValue(confNames['confProject']):
			if DEBUG > 0:
				log.debug('Auto mode: Expanding to folder level (need more relevant results)')
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
				folder_relevant = 0
				for task in folder_result.get('tasks', []):
					if task['id'] not in task_ids:
						all_tasks.append(task)
						task_ids.add(task['id'])
						# Count if this new task is relevant
						if search_query and search_query in task.get('name', '').lower():
							folder_relevant += 1
				
				relevant_count += folder_relevant
				if DEBUG > 0:
					log.debug('Auto mode: Total %d tasks after folder level (%d relevant)' % (len(all_tasks), relevant_count))
			except Exception as e:
				if DEBUG > 0:
					log.debug('Auto mode folder expansion failed: %s' % str(e))
		
		# Try space level only if we still need more relevant results and don't have too many total
		if relevant_count < 10 and len(all_tasks) < 30 and getConfigValue(confNames['confSpace']):
			if DEBUG > 0:
				log.debug('Auto mode: Expanding to space level (still need relevant results)')
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
				space_relevant = 0
				for task in space_result.get('tasks', []):
					if task['id'] not in task_ids:
						all_tasks.append(task)
						task_ids.add(task['id'])
						# Count if this new task is relevant
						if search_query and search_query in task.get('name', '').lower():
							space_relevant += 1
				
				relevant_count += space_relevant
				if DEBUG > 0:
					log.debug('Auto mode: Total %d tasks after space level (%d relevant)' % (len(all_tasks), relevant_count))
			except Exception as e:
				if DEBUG > 0:
					log.debug('Auto mode space expansion failed: %s' % str(e))
		elif relevant_count >= 10:
			if DEBUG > 0:
				log.debug('Auto mode: Skipping space expansion - already have %d relevant results' % relevant_count)
		
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
		# Only fetch docs if we don't already have enough relevant task results
		should_fetch_docs = True
		if search_scope == 'auto' and len(wf.args) > 0 and wf.args[0]:
			# Count relevant task results
			search_query = wf.args[0].lower()
			relevant_tasks = 0
			for task in result.get('tasks', []):
				if search_query in task.get('name', '').lower():
					relevant_tasks += 1
			# Skip docs if we already have plenty of relevant task results
			if relevant_tasks >= 15:
				should_fetch_docs = False
				if DEBUG > 0:
					log.debug('Skipping docs fetch - already have %d relevant task results' % relevant_tasks)
		
		if should_fetch_docs:
			# Fetch docs using v3 API (workspace_id is same as team_id) with search parameter
			try:
				workspace_id = validate_clickup_id(getConfigValue(confNames['confTeam']), 'workspace')
				docs_url = f'https://api.clickup.com/api/v3/workspaces/{workspace_id}/docs'
			except ValueError as e:
				log.error(f'Invalid workspace ID for docs: {e}')
				docs_url = None
			
			if DEBUG > 0:
				log.debug('Fetching docs from v3 API with search query')
			
			# Prepare docs search parameters
			docs_params = {}
			if len(wf.args) > 0 and wf.args[0]:
				docs_params['search'] = wf.args[0]
			
			try:
				docs_response = web.get(docs_url, params=docs_params, headers=headers, timeout=30)
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
		# Only fetch chats if we don't already have plenty of other results
		should_fetch_chats = True
		if search_scope == 'auto':
			total_results = len(result.get('tasks', [])) + len(docs_results)
			if total_results >= 20:
				should_fetch_chats = False
				if DEBUG > 0:
					log.debug('Skipping chats fetch - already have %d total results' % total_results)
		
		if should_fetch_chats:
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
