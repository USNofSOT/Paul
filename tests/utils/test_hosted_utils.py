import unittest
from unittest.mock import MagicMock, patch

from data import Hosted, VoyageType
from utils.hosted_utils import ShipHistory


class TestShipHistory(unittest.TestCase):
    def setUp(self):
        self.mock_hosted = self.create_mock_hosted(
            auxiliary_ship_name="USS Grizzly",
            ship_name="USS Illustrious",
            ship_voyage_count=5,
            fish_count=10,
            gold_count=1000,
            doubloon_count=50,
            ancient_coin_count=5,
            target_id=1,
        )

        self.mock_hosted_2 = self.create_mock_hosted(
            auxiliary_ship_name="USS Grizzly",
            ship_name="USS Illustrious",
            ship_voyage_count=8,
            fish_count=20,
            gold_count=4000,
            doubloon_count=12,
            ancient_coin_count=2,
            target_id=2,
            voyage_type=VoyageType.PATROL,
        )

    def create_mock_hosted(self, **kwargs):
        mock_hosted = MagicMock(spec=Hosted)
        for key, value in kwargs.items():
            setattr(mock_hosted, key, value)
        return mock_hosted

    def assert_ship_history(self, ship_history, **kwargs):
        for key, value in kwargs.items():
            self.assertEqual(getattr(ship_history, key), value)

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_name(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assert_ship_history(ship_history, ship_name="USS Grizzly")

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_is_auxiliary_multiple(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted, self.mock_hosted_2]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assertTrue(ship_history.is_auxiliary)

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_auxiliary(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assertTrue(ship_history.is_auxiliary)

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_auxiliary_to(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assert_ship_history(ship_history, auxiliary_to="USS Illustrious")

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_total_voyages(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assert_ship_history(ship_history, total_voyages=1)

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_total_voyages_multiple(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted, self.mock_hosted_2]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assert_ship_history(ship_history, total_voyages=2)

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_voyage_count(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assert_ship_history(ship_history, voyage_count=5)

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_voyage_count_multiple(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted, self.mock_hosted_2]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assert_ship_history(ship_history, voyage_count=8)

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_total_fishes_caught(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assert_ship_history(ship_history, total_fishes_caught=10)

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_total_fishes_caught_multiple(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted, self.mock_hosted_2]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assert_ship_history(ship_history, total_fishes_caught=30)

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_total_gold_earned(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assert_ship_history(ship_history, total_gold_earned=1000)

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_total_gold_earned_multiple(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted, self.mock_hosted_2]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assert_ship_history(ship_history, total_gold_earned=5000)

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_total_doubloons_earned(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assert_ship_history(ship_history, total_doubloons_earned=50)

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_total_doubloons_earned_multiple(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted, self.mock_hosted_2]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assert_ship_history(ship_history, total_doubloons_earned=62)

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_total_ancient_coins_earned(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assert_ship_history(ship_history, total_ancient_coins_earned=5)

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_total_ancient_coins_earned_multiple(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted, self.mock_hosted_2]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assert_ship_history(ship_history, total_ancient_coins_earned=7)

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_hosts(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assertEqual(len(ship_history.hosts), 1)

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_hosts_multiple(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted, self.mock_hosted_2]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assertEqual(len(ship_history.hosts), 2)

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_voyage_types(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assertEqual(len(ship_history.voyage_types), 5)

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_voyage_types_multiple(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = [self.mock_hosted, self.mock_hosted_2]
        ship_history = ShipHistory(ship_name="USS Grizzly")
        self.assertEqual(len(ship_history.voyage_types), 5)

    @patch("data.repository.hosted_repository.HostedRepository.retrieve_ship_history")
    def test_ship_history_no_history(self, mock_retrieve_ship_history):
        mock_retrieve_ship_history.return_value = []
        with self.assertRaises(ValueError):
            ShipHistory(ship_name="USS Grizzly")


if __name__ == "__main__":
    unittest.main()
