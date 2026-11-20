from decimal import Decimal, ROUND_HALF_UP

def seat_layout(id_asiento: int, tipo_bus: str = "DOS_PISOS_48") -> dict:
    if tipo_bus == "UN_PISO_48":
        local = id_asiento - 1
        return {"piso": 1, "fila": local // 4 + 1, "columna": f"C{(local % 4) + 1}", "columna_numero": (local % 4) + 1, "columnas": 4, "individual": (local % 4) == 0}
    # Bus de dos pisos: 8 asientos abajo y 40 arriba, configuración 2+1.
    local = id_asiento - 1 if id_asiento <= 8 else id_asiento - 9
    # La columna individual es la posición central de cada bloque 2+1.
    piso = 1 if id_asiento <= 8 else 2
    columnas = 3 if piso == 1 else 4
    return {"piso": piso, "fila": local // columnas + 1, "columna": "INDIVIDUAL" if local % 3 == 1 else "DOBLE", "columna_numero": (local % columnas) + 1, "columnas": columnas, "individual": local % 3 == 1}

def seat_fare_centavos(base_centavos: int, id_asiento: int, tipo_bus: str = "DOS_PISOS_48") -> int:
    layout = seat_layout(id_asiento, tipo_bus)
    multiplier = Decimal("1.20") if layout["piso"] == 1 else Decimal("1.00")
    if layout["individual"]:
        multiplier *= Decimal("1.10")
    return int((Decimal(base_centavos) * multiplier).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
