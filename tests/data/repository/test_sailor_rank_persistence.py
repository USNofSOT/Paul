from datetime import datetime

from src.data.models import Voyages
from src.data.repository.hosted_repository import HostedRepository
from src.data.repository.sailor_repository import SailorRepository
from src.data.repository.voyage_repository import VoyageRepository


def test_sailor_rank_persistence_scenarios():
    with SailorRepository() as repo:
        target_id = 987654321

        # Scenario 1: Initial creation (ensure it's clean)
        sailor = repo.update_or_create_sailor_by_discord_id(target_id)
        # Check current_rank_id might be None or whatever was already there
        # Instead of 'is None', assert that it is updated correctly to 1.

        # Scenario 2: Set rank
        repo.update_or_create_sailor_by_discord_id(target_id, current_rank_id=1)
        sailor = repo.get_sailor(target_id)
        assert sailor.current_rank_id == 1

        # Scenario 3: Update rank
        repo.update_or_create_sailor_by_discord_id(target_id, current_rank_id=2)
        sailor = repo.get_sailor(target_id)
        assert sailor.current_rank_id == 2

        # Scenario 4: Update other fields, rank should remain unchanged
        repo.update_or_create_sailor_by_discord_id(target_id, gamertag="NewTag")
        sailor = repo.get_sailor(target_id)
        assert sailor.current_rank_id == 2
        assert sailor.gamertag == "NewTag"

        # Scenario 5: Update rank to None (should be ignored)
        repo.update_or_create_sailor_by_discord_id(target_id, current_rank_id=None)
        sailor = repo.get_sailor(target_id)
        assert sailor.current_rank_id == 2


def test_voyage_rank_persistence():
    with VoyageRepository() as v_repo, HostedRepository() as h_repo:
        log_id = 1001
        target_id = 1234567890
        log_time = datetime.now()
        ship_role_id = 999
        rank_id = 1

        # Need to create a Hosted entry first because of FK
        h_repo.save_hosted_data(log_id=log_id, target_id=target_id, log_time=log_time)

        voyage_data = [(log_id, target_id, log_time, ship_role_id, rank_id)]
        v_repo.batch_save_voyage_data(voyage_data)

        voyage = v_repo.session.query(Voyages).filter_by(log_id=log_id, target_id=target_id).first()
        assert voyage.participant_rank_id == rank_id


def test_hosted_rank_persistence():
    with HostedRepository() as repo:
        log_id = 2002
        target_id = 1234567890
        log_time = datetime.now()
        rank_id = 1

        repo.save_hosted_data(log_id=log_id, target_id=target_id, log_time=log_time, host_rank_id=rank_id)

        hosted = repo.get_host_by_log_id(log_id)
        assert hosted.host_rank_id == rank_id
