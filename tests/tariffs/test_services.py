import pytest
from tariffs.services import ANEELTarifasAPI

class DummyAPI(ANEELTarifasAPI):
    def __init__(self):
        pass

    def _safe_float(self, value):
        return super()._safe_float(value)

def test_process_tariffs_mcdc():
    api = DummyAPI()

    # Caso 1: flag != 'Geração', subgroup = None (F, F)
    tariffs_raw = [{"flag": "B", "subgroup": None, "na_tusd_in_reais_per_kw": "1.0"}]
    result = api._process_tariffs(tariffs_raw)
    # O item é incluído, mas power_generation_tusd_in_reais_per_kw deve ser 0
    assert len(result) == 1
    assert result[0]["power_generation_tusd_in_reais_per_kw"] == 0

    # Caso 2: flag != 'Geração', subgroup = 'A1' (F, V)
    tariffs_raw = [{"flag": "B", "subgroup": "A1", "na_tusd_in_reais_per_kw": "1.0"}]
    result = api._process_tariffs(tariffs_raw)
    assert len(result) == 1
    assert result[0]["power_generation_tusd_in_reais_per_kw"] == 0

    # Caso 3: flag == 'Geração', subgroup = None (V, F)
    tariffs_raw = [{"flag": "Geração", "subgroup": None, "na_tusd_in_reais_per_kw": "2.0"}]
    result = api._process_tariffs(tariffs_raw)
    # O item não é incluído, pois flag não é 'B' ou 'G'
    assert result == []

    # Caso 4: flag == 'Geração', subgroup = 'A2' (V, V)
    tariffs_raw = [
        {"flag": "Geração", "subgroup": "A2", "na_tusd_in_reais_per_kw": "3.0"},
        {"flag": "B", "subgroup": "A2", "na_tusd_in_reais_per_kw": "1.0"}
    ]
    result = api._process_tariffs(tariffs_raw)
    # Apenas o item com flag 'B' aparece, mas o valor de geração é propagado
    assert len(result) == 1
    assert result[0]["power_generation_tusd_in_reais_per_kw"] == 3.0

    # Decisão 2: flag not in ["B", "G"] (deve ser ignorado)
    tariffs_raw = [
        {"flag": "X", "subgroup": "A3", "na_tusd_in_reais_per_kw": "4.0"},
        {"flag": "B", "subgroup": "A3", "na_tusd_in_reais_per_kw": "1.0"}
    ]
    result = api._process_tariffs(tariffs_raw)
    # O item com flag 'X' não aparece no resultado
    assert all(t["flag"] != "X" for t in result)
    assert len(result) == 1
