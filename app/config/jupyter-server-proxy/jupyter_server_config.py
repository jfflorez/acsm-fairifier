c.ServerProxy.servers = {
    'dash-app': {
        'command': [], # there is a running process ready to be listened to
        'port': 8050,
        'timeout': 30,
        'absolute_url': True,  # Changed to True
        'launcher_entry': {
            'enabled': True,
            'title': 'Data Flagging App',
        },
#        'new_browser_tab': False
    }
}