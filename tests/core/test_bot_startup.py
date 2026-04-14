import discord

from src.core.bot import _build_startup_log_fields
from src.core.discord_compat import apply_team_member_permissions_compat


def test_build_startup_log_fields_only_includes_startup_details():
    fields = _build_startup_log_fields(guild_name="Test Guild")
    field_map = {field.label: field.value for field in fields}

    assert set(field_map) == {
        "Environment",
        "Guild",
        "Extensions",
        "Bot Log Channel",
    }
    assert field_map["Guild"] == "Test Guild"


def test_apply_team_member_permissions_compat_backfills_missing_permissions(
        monkeypatch,
):
    original_init = discord.team.TeamMember.__init__

    def legacy_init(self, team, state, data):
        self.team = team
        self.membership_state = discord.enums.try_enum(
            discord.TeamMembershipState, data["membership_state"]
        )
        self.permissions = data["permissions"]
        self.role = discord.enums.try_enum(discord.TeamMemberRole, data["role"])
        discord.user.BaseUser.__init__(self, state=state, data=data["user"])

    monkeypatch.setattr(discord.team.TeamMember, "__init__", legacy_init)

    apply_team_member_permissions_compat()

    team = discord.team.Team(
        state=None,
        data={
            "id": "1",
            "name": "Paul",
            "icon": None,
            "owner_user_id": "2",
            "members": [
                {
                    "membership_state": 2,
                    "role": "admin",
                    "user": {
                        "id": "2",
                        "username": "captain",
                        "discriminator": "0",
                        "avatar": None,
                    },
                }
            ],
        },
    )

    assert team.members[0].permissions == []
    assert discord.team.TeamMember.__init__ is not original_init
