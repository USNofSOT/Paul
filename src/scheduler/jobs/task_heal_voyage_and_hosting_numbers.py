import logging

from data import engine
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)


def heal_voyage_and_hosting_numbers():
    """ "
    Update the sailor table with the correct hosted and voyage counts.

    Sometimes the counts (voyage_count and hosted_count) in the sailor table
    can get out of sync with the actual number of voyages and hosted tables.

     This function updates the sailor table with the correct counts.
    """
    with Session() as session:
        sql = text("""
         UPDATE sailor s
        LEFT JOIN (
            SELECT
                s.discord_id AS id,
                COUNT(DISTINCT h.log_id) AS table_hosted_count,
                COUNT(DISTINCT v.log_id) AS table_voyages_count
            FROM
                sailor s
            LEFT JOIN
                hosted h ON h.target_id = s.discord_id
            LEFT JOIN
                voyages v ON v.target_id = s.discord_id
            GROUP BY
                s.discord_id
        ) AS counts
        ON s.discord_id = counts.id
        SET
            s.hosted_count = counts.table_hosted_count,
            s.voyage_count = counts.table_voyages_count
        WHERE
            s.hosted_count != counts.table_hosted_count
        OR
            s.voyage_count != counts.table_voyages_count;
        """)
        session.execute(sql)
        session.commit()
