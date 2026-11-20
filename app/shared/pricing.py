from decimal import Decimal, ROUND_HALF_UP

def seat_layout(id_asiento: int) -> dict:
    # Convención del bus académico: asientos 1-4 son primer piso; el resto segundo piso.
    # En cada fila de tres posiciones, la primera es individual y las otras dos forman la pareja.
    return {"piso": 1 if id_asiento <= 4 else 2, "columna": "INDIVIDUAL" if (id_asiento - 1) % 3 == 0 else "DOBLE"}

def seat_fare_centavos(base_centavos: int, id_asiento: int) -> int:
    layout = seat_layout(id_asiento)
    multiplier = Decimal("1.20") if layout["piso"] == 1 else Decimal("1.00")
    if layout["columna"] == "INDIVIDUAL":
        multiplier *= Decimal("1.10")
    return int((Decimal(base_centavos) * multiplier).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
