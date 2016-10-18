# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This file contains all of the configuration values for the application.
Update this file with the values for your specific Google Cloud project.
You can create and manage projects at https://console.developers.google.com
"""

ENABLE_PRODUCTION_MODE = False

# The secret key is used by Flask to encrypt session cookies.
SECRET_KEY = 'secret'

# Google Cloud Project ID. This can be found on the 'Overview' page at
# https://console.developers.google.com
PROJECT_ID = 'ziplly-140504'

DATA_BACKEND = 'cloudsql'

# SQLAlchemy configuration
# Replace user, pass, host, and database with the respective values of your
# Cloud SQL instance.
#'mysql+pymysql://zroot:11111111@173.194.244.126/zdb'
SQLALCHEMY_DATABASE_URI = \
    'mysql+pymysql://zroot:11111111@//cloudsql/ziplly-140504:zipllydb/zdb'

SQLALCHEMY_DB_URL_APP_ENGINE = \
'mysql+mysqldb://root@/zdb?unix_socket=/cloudsql/ziplly-140504:ziplly-140504:zipllydb'

SQLALCHEMY_DB_URL_LOCAL = 'mysql+mysqldb://root:admin@localhost:3306/zdb'

#PLAID configuration
CLIENT_ID='57bbc58566710877408d093e'
CLIENT_SECRET='0f3e8ecc989e5e6ed776b732d76161'

########################   PRODUCTION SETTINGS
DB_HOST = '/cloudsql/ziplly-140504:zipllydb'
DB_USERNAME = 'zroot'
DB_PASSWORD = '11111111'
DB_NAME = 'zdb'

#########################  LOCAL SETTINGS   ###########################
# DB_HOST = 'localhost'
# DB_USERNAME = 'root'
# DB_PASSWORD = 'admin'
# DB_NAME = 'zdb'


#########################  TWILIO ACCOUNT   ##############################
TWILIO_ACCOUNT_SID = <ACCOUNT> 
TWILIO_ACCOUNT_TOKEN = <ACCOUNT_TOKEN> 
TWILIO_PHONE_NUMBER = <PHONE_NUMBER> 
