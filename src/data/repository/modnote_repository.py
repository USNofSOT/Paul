import datetime
import logging
from typing import Type

from sqlalchemy.orm import sessionmaker

from src.data.engine import engine
from src.data import Sailor, ModNotes

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)
class ModNoteRepository:
    def __init__(self):
        self.session = Session()

    def get_session(self):
        return self.session

    def close_session(self):
        self.session.close()

    def create_modnote(self, target_id : int, moderator_id : int, note : str) -> ModNotes | None:
        try:
            modnote = ModNotes(target_id=target_id,
                               moderator_id=moderator_id,
                               note=note,
                               note_time=datetime.datetime.now())
            self.session.add(modnote)
            self.session.commit()
            return modnote

        except Exception as e:
            log.error(f"Error saving mod note: {e}")
            self.session.rollback()
            raise e
        
    def _toggle_modnote(self, id : int, target_id : int, who_hid_id : int, hidden : bool) -> ModNotes | None:
        # Get sailor and modnote
        sailor = self.session.query(Sailor).filter(Sailor.discord_id == target_id).first()
        modnote = self.session.query(ModNotes).filter(ModNotes.id == id).first()

        # Raise an error if the note is not about this sailor
        assert modnote.target_id == sailor.discord_id, f"Note {id} is not linked to target {target_id}"

        # Toggle hide status
        modnote.hidden = hidden

        if hidden:
            modnote.who_hid = who_hid_id
            modnote.hide_time = datetime.datetime.now()
        else:
            pass #TODO: Consider wiping who_hid and hide_time if the note is un-hidden
        
    def hide_modnote(self, id : int, target_id : int, who_hid_id : int) -> ModNotes | None:
        try:
            return self._toggle_modnotes(id=id, target_id=target_id, who_hid_id=who_hid_id, hidden=True)
        except Exception as e:
            log.error(f"Error hiding note: {e}")
            self.session.rollback()
            raise e
        
    def unhide_modnote(self, id : int, target_id : int, who_hid_id : int) -> ModNotes | None:
        try:
            return self._toggle_modnotes(id=id, target_id=target_id, who_hid_id=who_hid_id, hidden=False)
        except Exception as e:
            log.error(f"Error unhiding note: {e}")
            self.session.rollback()
            raise e
            
