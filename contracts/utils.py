from datetime import datetime
from pathlib import Path
import arrow

class ContractUtils:
    def validate_date(self, energy_bill_date):
        #dd/mm/aaaa, mmm/aaaa, mm/aaaa
        if isinstance(energy_bill_date, datetime):
            return energy_bill_date.date()
        try:
            date_obj = arrow.get(energy_bill_date, [
                "MMM/YYYY",         
                "MM/YYYY",           
                "MMM/YY",           
                "DD/MM/YYYY", 
                "YYYY-MM-DD", 
                "YYYY-MM"
            ], locale='pt_br')
        except: 
            return energy_bill_date

        return date_obj.date()


    def check_file_extension(self, file_name):
        return Path(file_name).suffix[1:].lower()
