import datetime
import logging
from typing import Type

from sqlalchemy.orm import sessionmaker

from src.data.engine import engine
from src.data import ModNotes

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)
class ModNoteRepository:
    def __init__(self):
        self.session = Session()

    def get_session(self):
        return self.session

    def close_session(self):
        self.session.close()

    def create_modnote(self, target_id : int, moderator_id : int, note : str, note_time : datetime.datetime) -> ModNotes:
        try:
            modnote = ModNotes(target_id=target_id,
                               moderator_id=moderator_id,
                               note=note,
                               note_time=note_time)
            self.session.add(modnote)
            self.session.commit()
            return modnote

        except Exception as e:
            log.error(f"Error saving mod note: {e}")
            self.session.rollback()
            raise e
        finally:
            self.session.close()
