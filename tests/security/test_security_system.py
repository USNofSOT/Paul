import os
# Set up project path for imports if needed
import sys
import unittest
from unittest.mock import MagicMock, patch

import discord

sys.path.append(os.getcwd())

from src.security.roles import Role
from src.security.evaluator import resolve_effective_roles, clear_role_cache


class TestSecuritySystem(unittest.TestCase):
    def setUp(self):
        # Arrange
        clear_role_cache()

    def test_role_hierarchy_expansion(self):
        # Arrange
        member = MagicMock(spec=discord.Member)
        member.id = 123
        boa_role = MagicMock(spec=discord.Role)
        from src.config.ranks_roles import BOA_ROLE
        boa_role.id = BOA_ROLE
        member.roles = [boa_role]

        with patch('src.security.evaluator.UserRoleRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value.__enter__.return_value
            mock_repo.get_user_roles.return_value = set()

            # Act
            roles = resolve_effective_roles(member)

            # Assert
            self.assertIn(Role.BOA, roles)
            self.assertIn(Role.SO, roles)
            self.assertIn(Role.JO, roles)
            self.assertIn(Role.SNCO, roles)
            self.assertIn(Role.NCO, roles)
            self.assertIn(Role.JE, roles)

    def test_db_role_merging(self):
        # Arrange
        member = MagicMock(spec=discord.Member)
        member.id = 456
        member.roles = []

        with patch('src.security.evaluator.UserRoleRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value.__enter__.return_value
            mock_repo.get_user_roles.return_value = {Role.NSC_ADMINISTRATOR}

            # Act
            roles = resolve_effective_roles(member)

            # Assert
            self.assertIn(Role.NSC_ADMINISTRATOR, roles)
            self.assertIn(Role.NSC_OPERATOR, roles)
            self.assertIn(Role.NSC_OBSERVER, roles)

    def test_caching_logic(self):
        # Arrange
        member = MagicMock(spec=discord.Member)
        member.id = 789
        member.roles = []

        with patch('src.security.evaluator.UserRoleRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value.__enter__.return_value
            mock_repo.get_user_roles.return_value = {Role.JE}

            # Act
            roles1 = resolve_effective_roles(member)
            # Assert
            self.assertEqual(mock_repo.get_user_roles.call_count, 1)

            # Act (second call should be cached)
            roles2 = resolve_effective_roles(member)
            # Assert
            self.assertEqual(mock_repo.get_user_roles.call_count, 1)
            self.assertEqual(roles1, roles2)

    def test_fail_to_safety(self):
        # Arrange
        member = MagicMock(spec=discord.Member)
        member.id = 101

        from src.config.ranks_roles import JE_ROLE
        je_role = MagicMock(spec=discord.Role)
        je_role.id = JE_ROLE
        member.roles = [je_role]

        with patch('src.security.evaluator.UserRoleRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value.__enter__.return_value
            mock_repo.get_user_roles.side_effect = Exception("DB Down")

            # Act
            roles = resolve_effective_roles(member)

            # Assert
            self.assertIn(Role.JE, roles)
            self.assertEqual(len(roles), 1)


if __name__ == "__main__":
    unittest.main()
