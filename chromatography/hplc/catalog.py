COLUMNS = {
    "c18_100x4.6_5um": {
        "phase": "C18",
        "length_mm": 100,
        "id_mm": 4.6,
        "particle_um": 5,
        "max_pressure_bar": 400,
    },
    "c18_150x4.6_5um": {
        "phase": "C18",
        "length_mm": 150,
        "id_mm": 4.6,
        "particle_um": 5,
        "max_pressure_bar": 400,
    },
}


def get_column(column_id: str) -> dict | None:
    return COLUMNS.get(column_id)
