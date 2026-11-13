from sqlalchemy import text
from datetime import datetime

from sqlalchemy.orm import Session


def save_epias_pt_data(
        db: Session,
        epias_data: dict
) -> int:

    for item in epias_data["items"]:
        measurement_time = datetime.fromisoformat(item["date"])
        db.execute(
            text(
                """
                    INSERT INTO ptf_data (
                        measurement_time,
                        hour,
                        price,
                        price_usd,
                        price_eur,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        :measurement_time,
                        :hour,
                        :price,
                        :price_usd,
                        :price_eur,
                        NOW(),
                        NOW()
                    )
                    ON CONFLICT (measurement_time)
                    DO UPDATE SET
                        hour = EXCLUDED.hour,
                        price = EXCLUDED.price,
                        price_usd = EXCLUDED.price_usd,
                        price_eur = EXCLUDED.price_eur,
                        updated_at = NOW()
                """
            ),
            {
                "measurement_time": measurement_time,
                "hour": item["hour"],
                "price": item["price"],
                "price_usd": item["priceUsd"],
                "price_eur": item["priceEur"]
            }
        )
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return len(epias_data["items"])



