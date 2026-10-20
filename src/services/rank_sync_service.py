import logging

from src.config.ranks import RANKS
from src.data.models import Rank
from src.data.repository.rank_repository import RankRepository

log = logging.getLogger(__name__)


class RankSyncService:
    def __init__(self):
        self.rank_repo = RankRepository()

    def sync_ranks(self):
        """
        Synchronizes ranks from the RANKS configuration to the database.
        """
        log.info("Starting rank synchronization...")

        try:
            # Fetch all current ranks from the database
            db_ranks = self.rank_repo.get_all_ranks()
            db_ranks_by_role_id = {rank.role_id: rank for rank in db_ranks}

            config_role_ids = set()

            for navy_rank in RANKS:
                if not navy_rank.role_ids:
                    log.warning(f"Rank {navy_rank.name} has no role IDs defined. Skipping.")
                    continue

                # Use the first role ID as the primary role ID for the rank
                role_id = navy_rank.role_ids[0]
                config_role_ids.add(role_id)

                # Determine marine name - if it's the same as name, we can store it or keep it as is
                # NavyRank defaults marine_name to name
                marine_name = navy_rank.marine_name

                if role_id in db_ranks_by_role_id:
                    # Update existing rank
                    rank = db_ranks_by_role_id[role_id]
                    rank.name = navy_rank.name
                    rank.marine_name = marine_name
                    rank.identifier = navy_rank.identifier
                    rank.index = navy_rank.index
                    rank.is_active = True
                    self.rank_repo.update(rank)
                    log.debug(f"Updated rank: {rank.name} (ID: {role_id})")
                else:
                    # Create new rank
                    new_rank = Rank(
                        role_id=role_id,
                        name=navy_rank.name,
                        marine_name=marine_name,
                        identifier=navy_rank.identifier,
                        index=navy_rank.index,
                        is_active=True
                    )
                    self.rank_repo.create(new_rank)
                    log.info(f"Created new rank: {new_rank.name} (ID: {role_id})")

            # Deactivate ranks that are not in the current configuration
            for db_rank in db_ranks:
                if db_rank.role_id not in config_role_ids and db_rank.is_active:
                    db_rank.is_active = False
                    self.rank_repo.update(db_rank)
                    log.info(f"Deactivated rank: {db_rank.name} (ID: {db_rank.role_id})")

            log.info("Rank synchronization completed successfully.")

        except Exception as e:
            log.error(f"Error during rank synchronization: {e}")
            raise e
