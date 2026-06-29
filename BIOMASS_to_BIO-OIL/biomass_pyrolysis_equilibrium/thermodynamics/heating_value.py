"""Heating value correlations and conversions."""


def compute_hhv_mj_per_kg(
    c_pct: float,
    h_pct: float,
    o_pct: float,
    n_pct: float,
    s_pct: float,
    ash_pct: float,
) -> float:
    """Estimate HHV [MJ/kg] using the Channiwala and Parikh correlation."""

    return (
        0.3491 * c_pct
        + 1.1783 * h_pct
        + 0.1005 * s_pct
        - 0.1034 * o_pct
        - 0.0151 * n_pct
        - 0.0211 * ash_pct
    )


def compute_lhv_mj_per_kg(hhv_mj_per_kg: float, h_pct: float, moisture_pct: float, latent_heat_water_mj_per_kg: float) -> float:
    """Compute LHV [MJ/kg] from HHV, hydrogen, and moisture content."""

    return hhv_mj_per_kg - latent_heat_water_mj_per_kg * ((9.0 * h_pct / 100.0) + (moisture_pct / 100.0))
