import os

def is_running_on_app_engine():
    '''Returns true if the application is running on app engine. Keep in
    mind that applcation can be in test mode even though it might be running
    on app engine. For that you need to use the ENABLE_PRODUCTION_MODE config
    flag.'''
    env = os.getenv('SERVER_SOFTWARE')
    # print 'ENVIRONMENT  = %s' % env
    if (env and env.startswith('Google App Engine/')):
        return True
    return False
