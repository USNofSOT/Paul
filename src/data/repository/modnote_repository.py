import logging
from typing import Optional, List

from src.data import ModNotes
from src.data.repository.common.base_repository import BaseRepository, Session
from src.utils.time_utils import utc_time_now

log = logging.getLogger(__name__)


class ModNoteRepository(BaseRepository[ModNotes]):
    def __init__(self, session: Optional[Session] = None):
        super().__init__(ModNotes, session)

    def count_modnotes(self, target_id: int, include_hidden: bool = False) -> int:
        query = self.session.query(ModNotes).filter(ModNotes.target_id == target_id)
        if not include_hidden:
            query = query.filter(ModNotes.hidden == False)
        return query.count()

    def get_modnotes(self, target_id: int, limit: int = 10, show_hidden: bool = False) -> List[ModNotes]:
        query = self.session.query(ModNotes).filter(ModNotes.target_id == target_id).order_by(ModNotes.note_time.desc())
        if not show_hidden:
            query = query.filter(ModNotes.hidden == False)
        return query.limit(limit).all()

    def create_modnote(self, target_id: int, moderator_id: int, note: str) -> Optional[ModNotes]:
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

    def _toggle_modnote(self, note_id: int, target_id: int, who_hid_id: int, hidden: bool) -> ModNotes:
        # Get modnote
        modnote = self.session.query(ModNotes).filter(ModNotes.id == note_id).first()

        if modnote is None:
            raise ValueError(f"Could not find note with ID {note_id}")
        if modnote.target_id != target_id:
            raise ValueError(f"Note {note_id} is not linked to target {target_id}")

        # Toggle hide status
        modnote.hidden = hidden

        if hidden:
            modnote.who_hid = who_hid_id
            modnote.hide_time = utc_time_now()

        self.session.commit()
        return modnote

    def hide_modnote(self, note_id: int, target_id: int, who_hid_id: int) -> ModNotes:
        try:
            return self._toggle_modnote(note_id=note_id, target_id=target_id, who_hid_id=who_hid_id, hidden=True)
        except Exception as e:
            log.error(f"Error hiding note: {e}")
            self.session.rollback()
            raise e

    def unhide_modnote(self, note_id: int, target_id: int, who_hid_id: int) -> ModNotes:
        try:
            return self._toggle_modnote(note_id=note_id, target_id=target_id, who_hid_id=who_hid_id, hidden=False)
        except Exception as e:
            log.error(f"Error unhiding note: {e}")
            self.session.rollback()
            raise e
