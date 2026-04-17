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
        clear_role_cache()

    def test_role_hierarchy_expansion(self):
        # Mock member with BOA role
        member = MagicMock(spec=discord.Member)
        member.id = 123
        boa_role = MagicMock(spec=discord.Role)
        # Find the actual BOA role ID from mapping for testing
        from src.config.ranks_roles import BOA_ROLE
        boa_role.id = BOA_ROLE
        member.roles = [boa_role]

        # Patch the repository to return no DB roles
        with patch('src.security.evaluator.UserRoleRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value.__enter__.return_value
            mock_repo.get_user_roles.return_value = set()

            roles = resolve_effective_roles(member)

            self.assertIn(Role.BOA, roles)
            self.assertIn(Role.SO, roles)
            self.assertIn(Role.JO, roles)
            self.assertIn(Role.SNCO, roles)
            self.assertIn(Role.NCO, roles)
            self.assertIn(Role.JE, roles)

    def test_db_role_merging(self):
        # Mock member with no Discord roles
        member = MagicMock(spec=discord.Member)
        member.id = 456
        member.roles = []

        # Patch repository to return an NSC role
        with patch('src.security.evaluator.UserRoleRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value.__enter__.return_value
            mock_repo.get_user_roles.return_value = {Role.NSC_ADMINISTRATOR}

            roles = resolve_effective_roles(member)

            self.assertIn(Role.NSC_ADMINISTRATOR, roles)
            self.assertIn(Role.NSC_OPERATOR, roles)
            self.assertIn(Role.NSC_OBSERVER, roles)

    def test_caching_logic(self):
        member = MagicMock(spec=discord.Member)
        member.id = 789
        member.roles = []

        with patch('src.security.evaluator.UserRoleRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value.__enter__.return_value
            mock_repo.get_user_roles.return_value = {Role.JE}

            # First call
            roles1 = resolve_effective_roles(member)
            self.assertEqual(mock_repo.get_user_roles.call_count, 1)

            # Second call (should be cached)
            roles2 = resolve_effective_roles(member)
            self.assertEqual(mock_repo.get_user_roles.call_count, 1)
            self.assertEqual(roles1, roles2)

    def test_fail_to_safety(self):
        member = MagicMock(spec=discord.Member)
        member.id = 101

        # JE rank in Discord
        from src.config.ranks_roles import JE_ROLE
        je_role = MagicMock(spec=discord.Role)
        je_role.id = JE_ROLE
        member.roles = [je_role]

        # Repo raises exception
        with patch('src.security.evaluator.UserRoleRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value.__enter__.return_value
            mock_repo.get_user_roles.side_effect = Exception("DB Down")

            roles = resolve_effective_roles(member)

            # Should still have Discord role
            self.assertIn(Role.JE, roles)
            # Cache should still be updated with what we have
            self.assertEqual(len(roles), 1)


if __name__ == "__main__":
    unittest.main()
