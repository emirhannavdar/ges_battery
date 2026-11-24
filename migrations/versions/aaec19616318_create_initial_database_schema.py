from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'aaec19616318'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.Column("disabled", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("CURRENT_TIMESTAMP"),nullable=False,),
        sa.Column("is_operator", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("role", sa.String(50), nullable=True),
        sa.Column("refresh_jti", sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="users_pkey"),
        sa.UniqueConstraint("username", name="users_username_key"),
        sa.UniqueConstraint("email", name="users_email_key"),
        schema="public",
    )

    op.create_table(
        "ptf_data",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("measurement_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hour", sa.Time(), nullable=False),
        sa.Column("price", sa.Numeric(12,2), nullable=False),
        sa.Column("price_usd", sa.Numeric(12,2), nullable=False),
        sa.Column("price_eur", sa.Numeric(12,2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="ptf_data_pkey"),
        sa.UniqueConstraint("measurement_time", name="ptf_data_measurement_time_key"),
        schema="public",
    )
    op.create_index(
        "idx_ptf_measurement_time",
        "ptf_data",
        ["measurement_time"],
        schema="public",
    )

    op.create_table(
        "weather_data",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("measurement_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("temperature", sa.Double(), nullable=True),
        sa.Column("solar_radiation", sa.Double(), nullable=True),
        sa.Column("cloud_cover", sa.Double(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("datetime_hours", sa.String(50), nullable=True),
        sa.Column("datetime_days", sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint("id", name="weather_data_pkey"),
        sa.UniqueConstraint("location_id", "measurement_time", name="weather_data_location_id_measurement_time_key"),
        schema="public",
    )

    op.create_table(
        "simulation_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), server_default="created", nullable=False),
        sa.Column("inverter_count", sa.Integer(), nullable=False),
        sa.Column("state", postgresql.JSONB(), nullable=False),
        sa.Column("version", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="simulation_sessions_pkey"),
        sa.ForeignKeyConstraint(["user_id"],["public.users.id"],name="simulation_sessions_user_id_fkey"),
        schema="public",
    )
    op.create_index(
        "idx_simulation_sessions_user",
        "simulation_sessions",
        ["user_id"],
        schema="public",
    )

    op.create_table(
        "simulation_runs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("simulation_date", sa.Date(), nullable=False),
        sa.Column("inverter_count", sa.Integer(), nullable=False),
        sa.Column("processed_hours", sa.Integer(), nullable=False),
        sa.Column("total_inverter_energy_kwh", sa.Double(), nullable=False),
        sa.Column("total_grid_energy_kwh", sa.Double(), nullable=False),
        sa.Column("total_transformer_loss_kwh", sa.Double(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("inverter_ac_rated_kw", sa.Double(), nullable=True),
        sa.Column("inverter_dc_rated_kw", sa.Double(), nullable=True),
        sa.Column("ekk_active_power_limit_kw", sa.Double(), nullable=True),
        sa.Column("transformer_efficiency", sa.Double(), nullable=True),
        sa.Column("total_curtailed_energy_kwh", sa.Double(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="simulation_runs_pkey"),
        schema="public",
    )
    op.create_index(
        "ges_simulation_owner_idx",
        "simulation_runs",
        ["username", "created_at"],
        schema="public",
    )

    op.create_table(
        "simulation_hourly_results",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("simulation_id", sa.BigInteger(), nullable=False),
        sa.Column("hour", sa.Time(), nullable=False),
        sa.Column("irradiance_w_m2", sa.Double(), nullable=False),
        sa.Column("ambient_temperature_c", sa.Double(), nullable=False),
        sa.Column("inverter_power_kw", sa.Double(), nullable=False),
        sa.Column("grid_power_kw", sa.Double(), nullable=False),
        sa.Column("transformer_loss_kw", sa.Double(), nullable=False),
        sa.Column("ekk_limit_exceeded", sa.Boolean(), nullable=False),
        sa.Column("available_active_power_kw", sa.Double(), nullable=True),
        sa.Column("curtailed_power_kw", sa.Double(), nullable=True),
        sa.Column("curtailed_energy_kwh", sa.Double(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="simulation_hourly_results_pkey"),
        sa.UniqueConstraint("simulation_id","hour",name="simulation_hourly_results_simulation_id_hour_key"),
        sa.ForeignKeyConstraint(["simulation_id"],["public.simulation_runs.id"],name="simulation_hourly_results_simulation_id_fkey",ondelete="CASCADE"),
        schema="public",
    )

def downgrade() -> None:
    op.drop_table("simulation_hourly_results", schema="public")
    op.drop_table("simulation_runs", schema="public")
    op.drop_table("simulation_sessions", schema="public")
    op.drop_table("weather_data", schema="public")
    op.drop_table("ptf_data", schema="public")
    op.drop_table("users", schema="public")
