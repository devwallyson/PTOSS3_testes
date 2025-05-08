import datetime
import logging
import time

import pandas as pd
import requests

logger = logging.getLogger("apps")


class ANEELTarifasAPI:
    def __init__(self, resource_id, base_url, max_retries=3, retry_delay=1):
        self.resource_id = resource_id
        self.base_url = base_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()

    def get_current_tariffs_distributor(self, sigla=None, cnpj=None):
        raw_tariffs = self._get_raw_distributor_tariffs(sigla=sigla, cnpj=cnpj, current=True, future=False)
        return self._process_tariffs(raw_tariffs)

    def get_future_tariffs_distributor(self, sigla=None, cnpj=None):
        raw_tariffs = self._get_raw_distributor_tariffs(sigla=sigla, cnpj=cnpj, current=False, future=True)
        return self._process_tariffs(raw_tariffs)

    def get_all_tariffs_distributor(self, sigla=None, cnpj=None):
        raw_tariffs = self._get_raw_distributor_tariffs(sigla=sigla, cnpj=cnpj, current=True, future=True)
        return self._process_tariffs(raw_tariffs)

    def get_all_distributors(self):
        sql_query = f"""
            SELECT DISTINCT
                "SigAgente" as name,
                "NumCNPJDistribuidora as cnpj"
            FROM "{self.resource_id}"
        """
        return self._execute_sql_query(sql_query)

    def get_active_distributors(self):
        today = datetime.date.today().isoformat()

        sql_query = f"""
            SELECT DISTINCT
                "SigAgente" as name,
                "NumCNPJDistribuidora" as cnpj
            FROM "{self.resource_id}"
            WHERE "DatInicioVigencia" <= '{today}' AND "DatFimVigencia" >= '{today}'
        """
        return self._execute_sql_query(sql_query)

    def _make_request(self, url):
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                result = response.json()

                if not result.get("success", False):
                    error_msg = result.get("error", {}).get("message", "Unknown API error")
                    logger.error(f"API returned error: {error_msg}")
                    raise Exception(f"API error: {error_msg}")

                return result
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"API request failed after {self.max_retries} attempts: {str(e)}")
                    raise Exception(f"Failed to query API after {self.max_retries} attempts: {str(e)}") from e
                time.sleep(self.retry_delay)

        raise Exception("Erro inesperado na requisição")

    def _execute_sql_query(self, sql_query):
        encoded_query = requests.utils.quote(sql_query)
        url = f"{self.base_url}/datastore_search_sql?sql={encoded_query}"

        try:
            response = self._make_request(url)
            if "result" in response and "records" in response["result"]:
                return response["result"]["records"]
            logger.warning("API response did not contain expected 'result.records' structure")
            return []
        except Exception as e:
            logger.error(f"SQL query execution failed: {str(e)}")
            raise

    def _get_raw_distributor_tariffs(self, sigla=None, cnpj=None, current=True, future=False):
        today = datetime.date.today().isoformat()

        sql_query = f"""
            SELECT
                "SigAgente" as name,
                "NumCNPJDistribuidora" as cnpj,
                MIN("DatInicioVigencia") as start_date,
                MAX("DatFimVigencia") as end_date,
                "DscSubGrupo" as subgroup,
                CASE
                    WHEN "DscModalidadeTarifaria" = 'Azul' THEN 'B'
                    WHEN "DscModalidadeTarifaria" = 'Verde' THEN 'G'
                    ELSE 'Geração'
                END as flag,
                MAX(
                    CASE WHEN "DscUnidadeTerciaria" = 'kW' AND "NomPostoTarifario" = 'Ponta'
                    THEN "VlrTUSD"
                    ELSE NULL END) AS peak_tusd_in_reais_per_kw,
                MAX(
                    CASE WHEN "DscUnidadeTerciaria" = 'MWh' AND "NomPostoTarifario" = 'Ponta'
                    THEN "VlrTUSD"
                    ELSE NULL END) AS peak_tusd_in_reais_per_mwh,
                MAX(
                    CASE WHEN "DscUnidadeTerciaria" = 'MWh' AND "NomPostoTarifario" = 'Ponta'
                    THEN "VlrTE"
                    ELSE NULL END) AS peak_te_in_reais_per_mwh,
                MAX(
                    CASE WHEN "DscUnidadeTerciaria" = 'kW' AND "NomPostoTarifario" = 'Fora ponta'
                    THEN "VlrTUSD"
                    ELSE NULL END) AS off_peak_tusd_in_reais_per_kw,
                MAX(
                    CASE WHEN "DscUnidadeTerciaria" = 'MWh' AND "NomPostoTarifario" = 'Fora ponta'
                    THEN "VlrTUSD"
                    ELSE NULL END) AS off_peak_tusd_in_reais_per_mwh,
                MAX(
                    CASE WHEN "DscUnidadeTerciaria" = 'MWh' AND "NomPostoTarifario" = 'Fora ponta'
                    THEN "VlrTE"
                    ELSE NULL END) AS off_peak_te_in_reais_per_mwh,
                MAX(
                    CASE WHEN "DscUnidadeTerciaria" = 'kW' AND "NomPostoTarifario" = 'Não se aplica'
                    THEN "VlrTUSD"
                    ELSE NULL END) AS na_tusd_in_reais_per_kw
            FROM "{self.resource_id}"
            WHERE 1=1
        """

        if current and future:
            sql_query += f""" AND "DatFimVigencia" > '{today}'"""
        elif current:
            sql_query += f""" AND "DatInicioVigencia" <= '{today}' AND "DatFimVigencia" >= '{today}'"""
        elif future:
            sql_query += f""" AND "DatInicioVigencia" > '{today}'"""

        if cnpj:
            sql_query += f""" AND "NumCNPJDistribuidora" = '{cnpj}'"""
        if sigla:
            sql_query += f""" AND "SigAgente" = '{sigla}'"""

        sql_query += """
            AND "DscBaseTarifaria" = 'Tarifa de Aplicação'
            AND "DscSubGrupo" IN ('A1', 'A2', 'A3', 'A3a', 'A4', 'AS')
            AND "DscModalidadeTarifaria" IN ('Azul', 'Verde', 'Geração')
            AND "NomPostoTarifario" IN ('Ponta', 'Fora ponta', 'Não se aplica')
            AND "DscClasse" = 'Não se aplica'
            AND "DscSubClasse" = 'Não se aplica'
            AND "DscDetalhe" = 'Não se aplica'
            AND "SigAgenteAcessante" = 'Não se aplica'
            GROUP BY
                "SigAgente",
                "NumCNPJDistribuidora",
                "DscSubGrupo",
                "DscModalidadeTarifaria"
            ORDER BY
                "DscSubGrupo", "DscModalidadeTarifaria"
        """

        return self._execute_sql_query(sql_query)

    def _process_tariffs(self, tariffs_raw):
        processed_tariffs = []
        generation_tariffs = {}

        for tariff in tariffs_raw:
            subgroup = tariff.get("subgroup")

            if tariff.get("flag") == "Geração" and subgroup:
                generation_tariffs[subgroup] = self._safe_float(tariff.get("na_tusd_in_reais_per_kw"))

        for tariff in tariffs_raw:
            if tariff.get("flag") not in ["B", "G"]:
                continue

            subgroup = tariff.get("subgroup")
            start_date_str = tariff.get("start_date")
            end_date_str = tariff.get("end_date")

            try:
                start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
                end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
            except ValueError as e:
                logger.error(f"Date parsing error for tariff {subgroup}: {str(e)}")
                continue

            processed_tariff = {
                "start_date": start_date,
                "end_date": end_date,
                "subgroup": subgroup,
                "flag": tariff.get("flag"),
                "peak_tusd_in_reais_per_kw": self._safe_float(tariff.get("peak_tusd_in_reais_per_kw")),
                "peak_tusd_in_reais_per_mwh": self._safe_float(tariff.get("peak_tusd_in_reais_per_mwh")),
                "peak_te_in_reais_per_mwh": self._safe_float(tariff.get("peak_te_in_reais_per_mwh")),
                "off_peak_tusd_in_reais_per_kw": self._safe_float(tariff.get("off_peak_tusd_in_reais_per_kw")),
                "off_peak_tusd_in_reais_per_mwh": self._safe_float(tariff.get("off_peak_tusd_in_reais_per_mwh")),
                "off_peak_te_in_reais_per_mwh": self._safe_float(tariff.get("off_peak_te_in_reais_per_mwh")),
                "na_tusd_in_reais_per_kw": self._safe_float(tariff.get("na_tusd_in_reais_per_kw")),
                "power_generation_tusd_in_reais_per_kw": generation_tariffs.get(subgroup, 0),
            }

            processed_tariffs.append(processed_tariff)

        return processed_tariffs

    def _safe_float(self, value):
        if value is None or value == "":
            return None
        if isinstance(value, int | float):
            return float(value)
        try:
            return float(str(value).replace(",", "."))
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to convert value '{value}' to float: {str(e)}")
            return None


def save_csv(data, file_name="tariffs.csv"):
    df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    df.to_csv(file_name, index=False, encoding="utf-8")
    logger.info(f"Successfully saved {len(df)} records to '{file_name}'")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.FileHandler("aneel_tariffs.log"), logging.StreamHandler()],
    )

    RESOURCE_ID = "fcf2906c-7c32-4b9b-a637-054e7a5234f4"
    BASE_URL = "https://dadosabertos.aneel.gov.br/api/3/action"
    aneel_service = ANEELTarifasAPI(resource_id=RESOURCE_ID, base_url=BASE_URL)

    logging.info("=" * 80)
    logger.info(f"Inicializando serviço ANEEL: {RESOURCE_ID}")
    logging.info("=" * 80)
    logging.info("Fetching active distributors:")
    distributors = aneel_service.get_active_distributors()
    logging.info(f"Total active distributors: {len(distributors)}")
    for d in distributors:
        logging.info(f"Distributor: {d['name']}, CNPJ: {d['cnpj']}")

    logging.info("=" * 80)
    logging.info("Fetching current tariffs for active distributors")
    for d in distributors:
        logging.info("-" * 80)
        logging.info(f"Fetching current tariffs for {d['name']} (CNPJ: {d['cnpj']})")
        logging.info("-" * 80)
        try:
            current_tariffs = aneel_service.get_current_tariffs_distributor(sigla=d["name"], cnpj=d["cnpj"])
            logging.info(f"Results: {len(current_tariffs)} current tariffs")
            for tariff in current_tariffs:
                logging.info(f"Tariff: {tariff}")
        except Exception as e:
            logging.error(f"Error processing distributor {d['name']}: {str(e)}")
