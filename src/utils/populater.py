import asyncio
from logging import getLogger

from sqlalchemy.orm import sessionmaker

from src.config import VOYAGE_LOGS
from src.data import engine, create_tables, Sailor, Hosted, Voyages

log = getLogger(__name__)



class Populater():
    def __init__(self, bot) -> None:
        self.bot = bot
        # Ensure the Sailor table exists
        create_tables()

    async def synchronize(self, limit: int = None):
        session = sessionmaker(bind=engine)()
        hosted_session = sessionmaker(bind=engine)()
        sailor_session = sessionmaker(bind=engine)()

        channel = self.bot.get_channel(VOYAGE_LOGS)
        messages = channel.history(limit=limit, oldest_first=False)

        BATCH_SIZE = 50
        counter = 0

        log.info(f"Attempting to process existing voyage logs in {channel.name}.")

        async for message in channel.history(limit=limit, oldest_first=False):
            counter += 1
            log.info(f"[{message.id}] Processing voyage log {counter}.")

            log_id = message.id
            host_id = message.author.id
            log_time = message.created_at
            participant_ids = [user.id for user in message.mentions]

            if len(participant_ids) <= 0:
                log.info(f"[{log_id}] Skipping voyage log with no participants.")
                continue

            host = sailor_session.query(Sailor).filter(Sailor.discord_id == host_id).first()
            if not host:
                host = Sailor(discord_id=host_id, hosted_count=1)
            else:
                host.hosted_count += 1
            sailor_session.add(host)

            # If hosted entry already exists, skip
            if session.query(Hosted).filter(Hosted.log_id == log_id).first():
                log.info(f"[{log_id}] Skipping voyage log as it has already been processed.")
                continue

            # Create a Hosted entry
            hosted = Hosted(log_id=log_id, target_id=host_id, log_time=log_time)
            hosted_session.add(hosted) # We add this to sailor session to ensure it is committed

            for participant_id in participant_ids:
                participant = sailor_session.query(Sailor).filter(Sailor.discord_id == participant_id).first()
                if not participant:
                    participant = Sailor(discord_id=participant_id, voyage_count=1)
                else:
                    participant.voyage_count += 1
                sailor_session.add(participant)

                # Create a Voyage entry
                voyage = Voyages(log_id=log_id, target_id=participant_id, log_time=log_time)
                session.add(voyage)

            log.info(f"[{log_id}] Saving sailors and hosted data.")

            await asyncio.sleep(1)

            sailor_session.commit()
            hosted_session.commit() # We want to ensure the hosted data is committed so we know the points have been added
            if counter % BATCH_SIZE == 0:
                log.info(f"Batch saving voyages.")
                session.commit()

        sailor_session.commit()
        hosted_session.commit()
        session.commit()

        hosted_session.close()
        session.close()
        sailor_session.close()