from data.model.award_recipients_model import AwardRecipients
from data.repository.common.base_repository import BaseRepository


class AwardRecipientsRepository(BaseRepository):
    def __init__(self):
        super().__init__(AwardRecipients)
