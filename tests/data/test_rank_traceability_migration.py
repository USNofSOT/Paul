from pathlib import Path


def test_rank_traceability_migration_uses_role_id_as_rank_key():
    migration = Path(
        "src/data/migrations/versions/afc3160331ca_add_rank_traceability.py"
    ).read_text()

    assert "sa.PrimaryKeyConstraint('role_id')" in migration
    assert "['rank_id'], ['rank.role_id']" in migration
    assert "['host_rank_id'], ['role_id']" in migration
    assert "['current_rank_id'], ['role_id']" in migration
    assert "['participant_rank_id'], ['role_id']" in migration
    assert (
            "op.create_table('rank',\n                    sa.Column('id'" not in migration
    )
