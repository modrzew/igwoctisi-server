# -*- coding: utf-8 *-*
from sqlalchemy import *

engine = create_engine('sqlite:///IGWOCTISI.db')
connection = engine.connect()
meta = MetaData()
