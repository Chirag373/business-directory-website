import requests

class CountryStateCityAPI:
    """
    A utility class to interact with the Country State City API
    https://countrystatecity.in/
    """
    BASE_URL = "https://api.countrystatecity.in/v1"
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "X-CSCAPI-KEY": api_key
        }
    
    def get_countries(self):
        """Get all countries"""
        url = f"{self.BASE_URL}/countries"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return []
    
    def get_states(self, country_code):
        """Get all states for a country"""
        if not country_code:
            return []
        url = f"{self.BASE_URL}/countries/{country_code}/states"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return []
    
    def get_cities(self, country_code, state_code):
        """Get all cities for a state"""
        if not country_code or not state_code:
            return []
        url = f"{self.BASE_URL}/countries/{country_code}/states/{state_code}/cities"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return [] 