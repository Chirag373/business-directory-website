/**
 * Country State City API Dropdown Integration
 * This script handles the dynamic dropdowns for country, state, and city selection
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get the dropdown elements
    const countryDropdown = document.getElementById('country');
    const stateDropdown = document.getElementById('state');
    const cityDropdown = document.getElementById('city');
    
    // Function to populate a dropdown with options
    function populateDropdown(dropdown, items, valueKey, textKey) {
        // Clear existing options except the first one
        while (dropdown.options.length > 1) {
            dropdown.remove(1);
        }
        
        // Add new options
        items.forEach(item => {
            const option = document.createElement('option');
            option.value = item[valueKey];
            option.textContent = item[textKey];
            dropdown.appendChild(option);
        });
        
        // Enable the dropdown
        dropdown.disabled = false;
    }
    
    // Function to fetch data from the server
    async function fetchData(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching data:', error);
            return [];
        }
    }
    
    // Event listener for country dropdown change
    if (countryDropdown) {
        countryDropdown.addEventListener('change', async function() {
            const countryCode = this.value;
            
            // Reset and disable state and city dropdowns
            stateDropdown.innerHTML = '<option value="">Select a State</option>';
            stateDropdown.disabled = true;
            
            cityDropdown.innerHTML = '<option value="">Select a City</option>';
            cityDropdown.disabled = true;
            
            if (countryCode) {
                // Fetch states for the selected country
                const states = await fetchData(`/api/states/${countryCode}/`);
                populateDropdown(stateDropdown, states, 'iso2', 'name');
            }
        });
    }
    
    // Event listener for state dropdown change
    if (stateDropdown) {
        stateDropdown.addEventListener('change', async function() {
            const stateCode = this.value;
            const countryCode = countryDropdown.value;
            
            // Reset and disable city dropdown
            cityDropdown.innerHTML = '<option value="">Select a City</option>';
            cityDropdown.disabled = true;
            
            if (stateCode && countryCode) {
                // Fetch cities for the selected state
                const cities = await fetchData(`/api/cities/${countryCode}/${stateCode}/`);
                populateDropdown(cityDropdown, cities, 'id', 'name');
            }
        });
    }
    
    // If the country dropdown already has a value (edit mode), trigger the change event
    if (countryDropdown && countryDropdown.value) {
        // Create and dispatch a change event
        const event = new Event('change');
        countryDropdown.dispatchEvent(event);
        
        // If the state dropdown has a saved value, select it and trigger its change event
        if (stateDropdown.dataset.current) {
            setTimeout(() => {
                stateDropdown.value = stateDropdown.dataset.current;
                stateDropdown.dispatchEvent(new Event('change'));
                
                // If the city dropdown has a saved value, select it
                if (cityDropdown.dataset.current) {
                    setTimeout(() => {
                        cityDropdown.value = cityDropdown.dataset.current;
                    }, 500);
                }
            }, 500);
        }
    }
}); 