from sqlalchemy.orm import sessionmaker

from engine import engine
from src.database.models import Sailor

# Get a session from the engine
Session = sessionmaker(bind=engine)

def get_audit_logs(member_id, action_types=None):
    raise NotImplementedError


def get_award_ping_setting(user_id):
    session = Session()
    try:
        sailor: Sailor | None = session.query(Sailor).filter(Sailor.discord_id == user_id).first()
        return sailor.award_ping_enabled if sailor else None
    except Exception as e:
        print(f"Error retrieving award ping setting: {e}")
        return None
    finally:
        session.close()


if __name__ == '__main__':
    print(
        get_award_ping_setting(
            user_id=123456789
        )
    )
