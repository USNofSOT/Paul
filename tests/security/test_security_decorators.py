import os
# Set up project path for imports
import sys
import unittest
from unittest.mock import MagicMock, patch

import discord

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.security.roles import Role
from src.security.decorators import require_any_role, audit_interaction
from src.security.evaluator import clear_role_cache


class TestSecurityDecorators(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        clear_role_cache()

    async def test_require_any_role_wrapper_blocks_direct_call(self):
        # Mock callback
        async def mock_callback(interaction):
            return "Executed"

        # Decorate
        decorated = require_any_role(Role.JE)(mock_callback)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 123
        interaction.command = None

        # Mock resolve_effective_roles to return no roles
        with patch('src.security.decorators.resolve_effective_roles', return_value=set()):
            # Our decorator now handles UI interactions by calling the error handler
            with patch('src.security.error_handler.handle_app_command_security_error',
                       return_value=True) as mock_handler:
                result = await decorated(interaction)
                self.assertIsNone(result)
                mock_handler.assert_called_once()

    async def test_require_any_role_wrapper_allows_authorized_call(self):
        # Mock callback
        async def mock_callback(interaction):
            return "Executed"

        # Decorate
        decorated = require_any_role(Role.JE)(mock_callback)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 123

        # Mock resolve_effective_roles to return JE
        with patch('src.security.decorators.resolve_effective_roles', return_value={Role.JE}):
            result = await decorated(interaction)
            self.assertEqual(result, "Executed")

    async def test_audit_interaction_success(self):
        # Mock command callback
        async def mock_callback(self_arg, interaction, **kwargs):
            return "Result"

        # Decorate
        decorated = audit_interaction(mock_callback)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 789
        interaction.command.qualified_name = "test_command"

        with patch('src.security.decorators.SecurityInteractionRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value.__enter__.return_value

            result = await decorated(None, interaction, arg1="val1")

            self.assertEqual(result, "Result")
            # Verify log_interaction was called with SUCCESS
            mock_repo.log_interaction.assert_called_once()
            args, kwargs = mock_repo.log_interaction.call_args
            self.assertEqual(kwargs['event_type'], "SUCCESS")
            self.assertIn("val1", kwargs['args'])

    async def test_audit_interaction_failure(self):
        # Mock command callback that raises exception
        async def mock_callback(self_arg, interaction, **kwargs):
            raise ValueError("Test Error")

        # Decorate
        decorated = audit_interaction(mock_callback)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 789
        interaction.command.qualified_name = "test_command"

        with patch('src.security.decorators.SecurityInteractionRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value.__enter__.return_value

            with self.assertRaises(ValueError):
                await decorated(None, interaction)

            # Verify log_interaction was called with FAILURE
            mock_repo.log_interaction.assert_called_once()
            args, kwargs = mock_repo.log_interaction.call_args
            self.assertEqual(kwargs['event_type'], "FAILURE")
            self.assertIn("Test Error", kwargs['details'])


if __name__ == "__main__":
    unittest.main()
