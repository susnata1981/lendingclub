from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, auto_increment=True)
    email = Column(String(255))

    def __repr__(self):
        return "User(id = %d, email = %s)" % (self.id, self.email)


#mysql://root:admin@localhost/zdb
