#!/usr/bin/env python
# encoding: utf-8
#
# Sends a chat message to the configured Super Agent ClickUp chat channel.
# Two modes:
#   sendAgentMessage.py --filter "<typed text>"  -> Alfred Script Filter preview
#   sendAgentMessage.py --send   "<typed text>"  -> POSTs to ClickUp v3 chat
import sys
import json
from workflow import Workflow, web, PasswordNotFound
from workflow.notify import notify
from config import confNames, getConfigValue
from validation import validate_clickup_id, validate_api_key


def main(wf):
	args = list(wf.args)
	mode = 'filter'
	if args and args[0] in ('--filter', '--send'):
		mode = args.pop(0).replace('--', '')
	message = args[0] if args else ''

	if mode == 'filter':
		showFilter(wf, message)
	else:
		sendMessage(wf, message)


def showFilter(wf, message):
	channel_id = getConfigValue(confNames['confSuperAgentChannel'])
	channel_meta = wf.settings.get('superAgentChannelMeta') or {}
	channel_name = channel_meta.get('name') or channel_id or ''

	if not channel_id:
		wf.add_item(
			title='Super Agent channel not configured',
			subtitle='Run cu:config and choose "Set Super Agent channel" first.',
			valid=False,
			icon='error.png'
		)
		wf.send_feedback()
		return

	target = channel_name or channel_id
	if not message.strip():
		wf.add_item(
			title=f'Send to {target}',
			subtitle='Type a message and press Enter.',
			valid=False,
			icon='icon.png'
		)
	else:
		preview = (message[:80] + '…') if len(message) > 80 else message
		wf.add_item(
			title=f'Send to {target}',
			subtitle=preview,
			valid=True,
			arg=message,
			icon='icon.png'
		)
	wf.send_feedback()


def sendMessage(wf, message):
	if not message or not message.strip():
		notify('Super Agent', '', 'Empty message — nothing sent.')
		return

	channel_id = getConfigValue(confNames['confSuperAgentChannel'])
	workspace_id = getConfigValue(confNames['confTeam'])
	if not channel_id or not workspace_id:
		notify('Super Agent', 'Not configured', 'Set workspace and Super Agent channel in cu:config.')
		return

	try:
		validated_workspace_id = validate_clickup_id(workspace_id, 'workspace')
		validated_channel_id = validate_clickup_id(channel_id, 'channel')
	except ValueError as e:
		notify('Super Agent', 'Invalid IDs', str(e))
		return

	try:
		api_key = validate_api_key(getConfigValue(confNames['confApi']))
	except (ValueError, PasswordNotFound) as e:
		notify('Super Agent', 'Invalid API key', str(e))
		return

	url = f'https://api.clickup.com/api/v3/workspaces/{validated_workspace_id}/chat/channels/{validated_channel_id}/messages'
	headers = {
		'Authorization': api_key,
		'Content-Type': 'application/json'
	}
	body = {
		'type': 'message',
		'content_format': 'text/md',
		'content': message
	}

	try:
		request = web.post(url, data=json.dumps(body), headers=headers, timeout=30)
		request.raise_for_status()
	except Exception as e:
		log.debug(f'Chat send failed: {e}')
		notify('Super Agent — Send Failed', '', 'Check Alfred debug log for details.')
		return

	channel_meta = wf.settings.get('superAgentChannelMeta') or {}
	target = channel_meta.get('name') or channel_id
	preview = (message[:120] + '…') if len(message) > 120 else message
	notify('Sent to Super Agent', target, preview)


if __name__ == '__main__':
	wf = Workflow()
	log = wf.logger
	sys.exit(wf.run(main))
