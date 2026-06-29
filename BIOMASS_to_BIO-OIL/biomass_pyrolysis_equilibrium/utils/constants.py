"""Physical constants and thermodynamic reference values."""

R_J_PER_MOL_K = 8.314462618
P0_PA = 101_325.0

# Atomic weights [g/mol].
ATOMIC_WEIGHTS = {
    "C": 12.01,
    "H": 1.008,
    "O": 16.00,
    "N": 14.01,
    "S": 32.06,
}

# Standard entropies at 298.15 K [J/mol/K] for elemental reference states.
ELEMENT_STANDARD_ENTROPIES = {
    "C": 5.740,    # graphite
    "H": 65.342,   # H2(g) / atom basis handled in calculations
    "O": 102.575,  # O2(g) / atom basis handled in calculations
    "N": 95.805,   # N2(g) / atom basis handled in calculations
    "S": 31.880,   # rhombic sulfur
}

# Product standard formation enthalpies [kJ/mol].
STANDARD_FORMATION_ENTHALPY = {
    "CO2": -393.52,
    "H2O": -241.826,  # gas phase
    "SO2": -296.81,
}
