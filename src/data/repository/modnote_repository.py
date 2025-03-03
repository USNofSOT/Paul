import datetime
import logging
from typing import Type

from sqlalchemy.orm import sessionmaker

from src.data.engine import engine
from src.data import Sailor, ModNotes
from src.utils.time_utils import utc_time_now

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)
class ModNoteRepository:
    def __init__(self):
        self.session = Session()

    def get_session(self):
        return self.session

    def close_session(self):
        self.session.close()

    def count_modnotes(self, target_id : int, include_hidden : bool = False) -> int:
        if include_hidden:
            return self.session.query(ModNotes).filter(ModNotes.target_id == target_id).count()
        else:
            return self.session.query(ModNotes).filter(ModNotes.target_id == target_id).filter(ModNotes.hidden == False).count()

    def get_modnotes(self, target_id : int, limit : int = 10, show_hidden : bool = False) -> [ModNotes]:
        if show_hidden:
            return self.session.query(ModNotes).filter(ModNotes.target_id == target_id).order_by(ModNotes.note_time.desc()).limit(limit).all()
        else:
            return self.session.query(ModNotes).filter(ModNotes.target_id == target_id).filter(ModNotes.hidden == False).order_by(ModNotes.note_time.desc()).limit(limit).all()

    def create_modnote(self, target_id : int, moderator_id : int, note : str) -> ModNotes | None:
        try:
            modnote = ModNotes(target_id=target_id,
                               moderator_id=moderator_id,
                               note=note,
                               note_time=utc_time_now())
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
            modnote.hide_time = utc_time_now()
        else:
            pass #TODO: Consider wiping who_hid and hide_time if the note is un-hidden
        self.session.commit()
        return modnote
        
    def hide_modnote(self, id : int, target_id : int, who_hid_id : int) -> ModNotes | None:
        try:
            return self._toggle_modnote(id=id, target_id=target_id, who_hid_id=who_hid_id, hidden=True)
        except Exception as e:
            log.error(f"Error hiding note: {e}")
            self.session.rollback()
            raise e
        
    def unhide_modnote(self, id : int, target_id : int, who_hid_id : int) -> ModNotes | None:
        try:
            return self._toggle_modnote(id=id, target_id=target_id, who_hid_id=who_hid_id, hidden=False)
        except Exception as e:
            log.error(f"Error unhiding note: {e}")
            self.session.rollback()
            raise e
            
