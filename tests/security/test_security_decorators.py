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
        # Arrange
        clear_role_cache()

    async def test_require_any_role_wrapper_blocks_direct_call(self):
        # Arrange
        async def mock_callback(interaction):
            return "Executed"

        decorated = require_any_role(Role.JE)(mock_callback)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 123
        interaction.command = None

        with patch('src.security.decorators.resolve_effective_roles', return_value=set()):
            with patch('src.security.error_handler.handle_app_command_security_error',
                       return_value=True) as mock_handler:
                # Act
                result = await decorated(interaction)
                # Assert
                self.assertIsNone(result)
                mock_handler.assert_called_once()

    async def test_require_any_role_wrapper_allows_authorized_call(self):
        # Arrange
        async def mock_callback(interaction):
            return "Executed"

        decorated = require_any_role(Role.JE)(mock_callback)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 123

        with patch('src.security.decorators.resolve_effective_roles', return_value={Role.JE}):
            # Act
            result = await decorated(interaction)
            # Assert
            self.assertEqual(result, "Executed")

    async def test_audit_interaction_success(self):
        # Arrange
        async def mock_callback(self_arg, interaction, **kwargs):
            return "Result"

        decorated = audit_interaction(mock_callback)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 789
        interaction.command.qualified_name = "test_command"

        with patch('src.security.decorators.SecurityInteractionRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value.__enter__.return_value

            # Act
            result = await decorated(None, interaction, arg1="val1")

            # Assert
            self.assertEqual(result, "Result")
            mock_repo.log_interaction.assert_called_once()
            args, kwargs = mock_repo.log_interaction.call_args
            self.assertEqual(kwargs['event_type'], "SUCCESS")
            self.assertIn("val1", kwargs['args'])

    async def test_audit_interaction_failure(self):
        # Arrange
        async def mock_callback(self_arg, interaction, **kwargs):
            raise ValueError("Test Error")

        decorated = audit_interaction(mock_callback)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 789
        interaction.command.qualified_name = "test_command"

        with patch('src.security.decorators.SecurityInteractionRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value.__enter__.return_value

            # Act & Assert
            with self.assertRaises(ValueError):
                await decorated(None, interaction)

            mock_repo.log_interaction.assert_called_once()
            args, kwargs = mock_repo.log_interaction.call_args
            self.assertEqual(kwargs['event_type'], "FAILURE")
            self.assertIn("Test Error", kwargs['details'])


if __name__ == "__main__":
    unittest.main()
