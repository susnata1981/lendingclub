from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Column, Integer, Float, String, DateTime, Text
from sqlalchemy.orm import relationship

import sys, os, logging
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'util'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'db'))
import model
from request_service import RequestService
import config_loader, logger

if __name__ == '__main__':
    LOGGER = logger.getLogger('test_service', logging.DEBUG)
    config_path = os.path.join(os.path.dirname(__file__), '..', '..','config.py')
    config = config_loader.load_config(config_path)

    Base = declarative_base()
    engine = create_engine(config['SQLALCHEMY_DB_URL_LOCAL'], echo=True)
    db_session = scoped_session(sessionmaker(autocommit=False,autoflush=False,bind=engine))

    request_service = RequestService(db_session)
    account = db_session.query(model.Account).filter(model.Account.id == 1).one_or_none()

    #req = request_service.create_request(account, 300)
    print 'Request status:{0}'.format(account.request_money_list[0].status)

    request_service.approve_request(account.request_money_list[0])
    print 'Request status:{0}'.format(account.request_money_list[0].status)
