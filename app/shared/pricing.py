from decimal import Decimal, ROUND_HALF_UP

def seat_layout(id_asiento: int, tipo_bus: str = "DOS_PISOS_48") -> dict:
    if tipo_bus == "UN_PISO_48":
        local = id_asiento - 1
        return {"piso": 1, "numero": id_asiento, "fila": local // 4 + 1, "columna": f"C{(local % 4) + 1}", "columna_numero": (local % 4) + 1, "columnas": 4, "individual": (local % 4) == 0}
    # Bus de dos pisos: 8 asientos abajo y 40 arriba, configuración 2+1.
    local = id_asiento - 1 if id_asiento <= 12 else id_asiento - 13
    # La columna individual es la posición central de cada bloque 2+1.
    piso = 1 if id_asiento <= 12 else 2
    columnas = 3 if piso == 1 else 4
    columna_numero = (local % columnas) + 1
    return {"piso": piso, "numero": local + 1, "fila": local // columnas + 1, "columna": "INDIVIDUAL" if columna_numero == 1 else "DOBLE", "columna_numero": columna_numero, "columnas": columnas, "individual": columna_numero == 1}

def seat_fare_centavos(base_centavos: int, id_asiento: int, tipo_bus: str = "DOS_PISOS_48") -> int:
    layout = seat_layout(id_asiento, tipo_bus)
    # Se conserva la zona tarifaria premium histórica (primeras 8 plazas)
    # aunque el primer piso físico ahora tenga 12 asientos.
    premium = layout["piso"] == 1 and not (tipo_bus == "DOS_PISOS_48" and id_asiento > 8)
    multiplier = Decimal("1.20") if premium else Decimal("1.00")
    if layout["individual"]:
        multiplier *= Decimal("1.10")
    return int((Decimal(base_centavos) * multiplier).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
