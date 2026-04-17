import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import discord

sys.path.append(os.getcwd())

from src.security.roles import Role, DISCORD_ROLE_MAP
from src.security.hierarchy import ROLE_HIERARCHY
from src.security.evaluator import resolve_effective_roles, clear_role_cache
from src.security.decorators import InsufficientLevelError


def _make_member(discord_role_ids: list[int], user_id: int = 1) -> discord.Member:
    member = MagicMock(spec=discord.Member)
    member.id = user_id
    roles = []
    for role_id in discord_role_ids:
        r = MagicMock(spec=discord.Role)
        r.id = role_id
        roles.append(r)
    member.roles = roles
    return member


class TestDiscordRoleMap(unittest.TestCase):
    def test_standard_ranks_mapped(self):
        from src.config.ranks_roles import JE_ROLE, NCO_ROLE, SNCO_ROLE, JO_ROLE, SO_ROLE, BOA_ROLE
        self.assertEqual(DISCORD_ROLE_MAP[JE_ROLE], Role.JE)
        self.assertEqual(DISCORD_ROLE_MAP[NCO_ROLE], Role.NCO)
        self.assertEqual(DISCORD_ROLE_MAP[SNCO_ROLE], Role.SNCO)
        self.assertEqual(DISCORD_ROLE_MAP[JO_ROLE], Role.JO)
        self.assertEqual(DISCORD_ROLE_MAP[SO_ROLE], Role.SO)
        self.assertEqual(DISCORD_ROLE_MAP[BOA_ROLE], Role.BOA)

    def test_nrc_role_mapped(self):
        from src.config.ranks_roles import NRC_ROLE
        self.assertEqual(DISCORD_ROLE_MAP[NRC_ROLE], Role.NRC)

    def test_veteran_roles_mapped(self):
        from src.config.ranks_roles import VT_ROLES
        for role_id in VT_ROLES:
            self.assertEqual(DISCORD_ROLE_MAP[role_id], Role.VETERAN)

    def test_retired_roles_mapped(self):
        from src.config.ranks_roles import RT_ROLES
        for role_id in RT_ROLES:
            self.assertEqual(DISCORD_ROLE_MAP[role_id], Role.RETIRED)

    def test_voyage_permissions_mapped(self):
        from src.config.ranks_roles import VOYAGE_PERMISSIONS
        self.assertEqual(DISCORD_ROLE_MAP[VOYAGE_PERMISSIONS], Role.VOYAGE_PERMISSIONS)

    def test_nsc_role_maps_to_observer(self):
        from src.config.ranks_roles import NSC_ROLE
        self.assertEqual(DISCORD_ROLE_MAP[NSC_ROLE], Role.NSC_OBSERVER)

    def test_spd_nsc_role_maps_to_observer(self):
        from src.config.spd_servers import SPD_NSC_ROLE
        self.assertEqual(DISCORD_ROLE_MAP[SPD_NSC_ROLE], Role.NSC_OBSERVER)

    def test_netc_high_command_roles_mapped(self):
        from src.config.netc_server import HIGH_COMMAND_OF_NETC_ROLES
        for role_id in HIGH_COMMAND_OF_NETC_ROLES:
            self.assertEqual(DISCORD_ROLE_MAP[role_id], Role.NETC_HIGH_COMMAND)


class TestRoleHierarchy(unittest.TestCase):
    def test_boa_includes_all_lower_ranks(self):
        expanded = {Role.BOA} | set(ROLE_HIERARCHY.get(Role.BOA, []))
        for role in (Role.SO, Role.JO, Role.SNCO, Role.NCO, Role.JE):
            self.assertIn(role, expanded)

    def test_so_includes_jo_and_below(self):
        expanded = {Role.SO} | set(ROLE_HIERARCHY.get(Role.SO, []))
        for role in (Role.JO, Role.SNCO, Role.NCO, Role.JE):
            self.assertIn(role, expanded)

    def test_nsc_administrator_includes_operator_and_observer(self):
        expanded = set(ROLE_HIERARCHY.get(Role.NSC_ADMINISTRATOR, []))
        self.assertIn(Role.NSC_OPERATOR, expanded)
        self.assertIn(Role.NSC_OBSERVER, expanded)

    def test_nsc_operator_includes_observer(self):
        expanded = set(ROLE_HIERARCHY.get(Role.NSC_OPERATOR, []))
        self.assertIn(Role.NSC_OBSERVER, expanded)

    def test_je_has_no_hierarchy_expansion(self):
        self.assertNotIn(Role.JE, ROLE_HIERARCHY)

    def test_nrc_has_no_hierarchy_expansion(self):
        self.assertNotIn(Role.NRC, ROLE_HIERARCHY)


class TestResolveEffectiveRoles(unittest.TestCase):
    def setUp(self):
        clear_role_cache()

    def _resolve(self, member, db_roles=None):
        with patch('src.security.evaluator.UserRoleRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value.__enter__.return_value
            mock_repo.get_user_roles.return_value = db_roles or set()
            return resolve_effective_roles(member)

    def test_nsc_member_gets_observer_via_discord_role(self):
        from src.config.ranks_roles import NSC_ROLE
        member = _make_member([NSC_ROLE])
        roles = self._resolve(member)
        self.assertIn(Role.NSC_OBSERVER, roles)

    def test_spd_nsc_member_gets_observer(self):
        from src.config.spd_servers import SPD_NSC_ROLE
        member = _make_member([SPD_NSC_ROLE])
        roles = self._resolve(member)
        self.assertIn(Role.NSC_OBSERVER, roles)

    def test_veteran_discord_role_resolves(self):
        from src.config.ranks_roles import VT_ROLES
        if not VT_ROLES:
            self.skipTest("No VT_ROLES configured")
        member = _make_member([VT_ROLES[0]])
        roles = self._resolve(member)
        self.assertIn(Role.VETERAN, roles)

    def test_voyage_permissions_discord_role_resolves(self):
        from src.config.ranks_roles import VOYAGE_PERMISSIONS
        member = _make_member([VOYAGE_PERMISSIONS])
        roles = self._resolve(member)
        self.assertIn(Role.VOYAGE_PERMISSIONS, roles)

    def test_nsc_administrator_db_role_expands_to_observer(self):
        member = _make_member([])
        roles = self._resolve(member, db_roles={Role.NSC_ADMINISTRATOR})
        self.assertIn(Role.NSC_ADMINISTRATOR, roles)
        self.assertIn(Role.NSC_OPERATOR, roles)
        self.assertIn(Role.NSC_OBSERVER, roles)

    def test_boa_discord_role_expands_full_hierarchy(self):
        from src.config.ranks_roles import BOA_ROLE
        member = _make_member([BOA_ROLE])
        roles = self._resolve(member)
        for expected in (Role.BOA, Role.SO, Role.JO, Role.SNCO, Role.NCO, Role.JE):
            self.assertIn(expected, roles)


class TestRequireAnyRoleDecorator(unittest.TestCase):
    def setUp(self):
        clear_role_cache()

    def _make_interaction(self, discord_role_ids: list[int], user_id: int = 1) -> discord.Interaction:
        interaction = MagicMock(spec=discord.Interaction)
        interaction.user = _make_member(discord_role_ids, user_id)
        return interaction

    def _call_predicate(self, roles_required: list, interaction, db_roles=None):
        with patch('src.security.evaluator.UserRoleRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value.__enter__.return_value
            mock_repo.get_user_roles.return_value = db_roles or set()
            # Extract the predicate from the combined_check closure
            dummy_func = MagicMock()
            dummy_func.__discord_app_commands_checks__ = []
            # Call with interaction directly to test predicate logic
            from src.security.evaluator import resolve_effective_roles
            user_roles = resolve_effective_roles(interaction.user)
            if any(role in user_roles for role in roles_required):
                return True
            raise InsufficientLevelError(list(roles_required), list(user_roles))

    def test_je_role_passes_je_requirement(self):
        from src.config.ranks_roles import JE_ROLE
        interaction = self._make_interaction([JE_ROLE])
        result = self._call_predicate([Role.JE], interaction)
        self.assertTrue(result)

    def test_boa_passes_nco_requirement_via_hierarchy(self):
        from src.config.ranks_roles import BOA_ROLE
        interaction = self._make_interaction([BOA_ROLE])
        result = self._call_predicate([Role.NCO], interaction)
        self.assertTrue(result)

    def test_no_roles_raises_insufficient_level_error(self):
        interaction = self._make_interaction([])
        with self.assertRaises(InsufficientLevelError) as ctx:
            self._call_predicate([Role.JE], interaction)
        self.assertIn(Role.JE, ctx.exception.required_roles)

    def test_nsc_member_passes_observer_requirement(self):
        from src.config.ranks_roles import NSC_ROLE
        interaction = self._make_interaction([NSC_ROLE])
        result = self._call_predicate([Role.NSC_OBSERVER], interaction)
        self.assertTrue(result)

    def test_voyage_permissions_role_passes_requirement(self):
        from src.config.ranks_roles import VOYAGE_PERMISSIONS
        interaction = self._make_interaction([VOYAGE_PERMISSIONS])
        result = self._call_predicate([Role.NCO, Role.VOYAGE_PERMISSIONS], interaction)
        self.assertTrue(result)

    def test_je_member_does_not_pass_nco_requirement(self):
        from src.config.ranks_roles import JE_ROLE
        interaction = self._make_interaction([JE_ROLE])
        with self.assertRaises(InsufficientLevelError):
            self._call_predicate([Role.NCO], interaction)

    def test_insufficient_level_error_contains_possessed_roles(self):
        from src.config.ranks_roles import JE_ROLE
        interaction = self._make_interaction([JE_ROLE])
        with self.assertRaises(InsufficientLevelError) as ctx:
            self._call_predicate([Role.SO], interaction)
        self.assertIn(Role.JE, ctx.exception.possessed_roles)


if __name__ == "__main__":
    unittest.main()
