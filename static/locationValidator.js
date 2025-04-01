// List of valid UK locations (major cities and areas)
const validLocations = [
    // London areas
    'London', 'Central London', 'North London', 'South London', 'East London', 'West London',
    'Camden', 'Kensington', 'Chelsea', 'Westminster', 'Greenwich', 'Richmond', 'Hackney',
    
    // Major cities
    'Manchester', 'Liverpool', 'Birmingham', 'Leeds', 'Glasgow', 'Edinburgh', 'Cardiff',
    'Bristol', 'Sheffield', 'Nottingham', 'Leicester', 'Coventry', 'Hull', 'Newcastle',
    
    // Areas around major cities
    'Greater Manchester', 'Merseyside', 'West Midlands', 'West Yorkshire', 'Greater Glasgow',
    'Lothian', 'South Gloucestershire', 'South Yorkshire', 'Nottinghamshire', 'Leicestershire',
    
    // Other major areas
    'Brighton', 'Bath', 'Oxford', 'Cambridge', 'York', 'Belfast', 'Aberdeen', 'Dundee',
    'Exeter', 'Plymouth', 'Southampton', 'Portsmouth', 'Norwich', 'Leicester', 'Derby',
    
    // Counties
    'Surrey', 'Kent', 'Essex', 'Hertfordshire', 'Buckinghamshire', 'Berkshire', 'Hampshire',
    'Sussex', 'Devon', 'Cornwall', 'Somerset', 'Dorset', 'Wiltshire', 'Gloucestershire',
    'Worcestershire', 'Warwickshire', 'Staffordshire', 'Cheshire', 'Lancashire', 'Yorkshire',
    'Durham', 'Northumberland', 'Cumbria', 'Wales', 'Scotland', 'Northern Ireland'
];

// Function to validate location format
function validateLocationFormat(location) {
    if (!location || !location.trim()) {
        return "Please enter a location";
    }

    // Check for postcode format (outward code like 'M40')
    if (/^[A-Z][0-9A-Z]?[0-9]/.test(location.trim().toUpperCase())) {
        return null; // Valid postcode format
    }

    // Check for regular location format
    if (!/^[a-zA-Z\s,]+$/.test(location)) {
        return "Location must contain only letters, spaces, and commas (or be a valid postcode)";
    }

    if (location.trim().length < 2) {
        return "Location must be at least 2 characters";
    }

    return null; // No error
}

// Function to check if location is in valid locations list
function isValidLocation(location) {
    const normalizedLocation = location.trim().toLowerCase();
    return validLocations.some(validLoc => 
        validLoc.toLowerCase() === normalizedLocation ||
        normalizedLocation.includes(validLoc.toLowerCase())
    );
}

// Function to validate location length
function validateLocationLength(location) {
    return location.trim().length >= 2;
}

// Main validation function
function validateLocation(location) {
    const locationError = document.getElementById("location-error");
    
    // Clear previous error
    locationError.innerHTML = "";
    
    // Check if location is empty
    if (!location.trim()) {
        locationError.innerHTML = `
            <div class="error-message">
                <h3>Required Field</h3>
                <p>Please enter a location</p>
                <p class="error-help">Enter a valid UK location (e.g., London, Manchester, Birmingham)</p>
            </div>`;
        return false;
    }
    
    // Check location format
    const formatError = validateLocationFormat(location);
    if (formatError) {
        locationError.innerHTML = `
            <div class="error-message">
                <h3>Invalid Format</h3>
                <p>${formatError}</p>
                <p class="error-help">Example: London, Manchester, Birmingham</p>
            </div>`;
        return false;
    }
    
    // Check location length
    if (!validateLocationLength(location)) {
        locationError.innerHTML = `
            <div class="error-message">
                <h3>Too Short</h3>
                <p>Location must be at least 2 characters long</p>
                <p class="error-help">Enter a valid UK location name</p>
            </div>`;
        return false;
    }
    
    // Check if location is in valid locations list
    if (!isValidLocation(location)) {
        locationError.innerHTML = `
            <div class="error-message">
                <h3>Invalid Location</h3>
                <p>Please enter a valid UK location</p>
                <p class="error-help">Try entering a major city or area (e.g., London, Manchester, Birmingham)</p>
            </div>`;
        return false;
    }
    
    return true;
}

// Make sure the validator is available globally
window.locationValidator = {
    validateLocation,
    isValidLocation,
    validateLocationFormat,
    validateLocationLength
};

// Initialize the validator when the script loads
document.addEventListener('DOMContentLoaded', () => {
    if (!window.locationValidator) {
        console.error('Location validator not initialized properly');
    }
});

// Location validation on the frontend
document.addEventListener('DOMContentLoaded', function() {
    const locationInput = document.getElementById('location');
    const locationError = document.getElementById('location-error');
    const searchButton = document.getElementById('searchButton');

    // Function to show error message
    function showError(message) {
        locationError.textContent = message;
        locationError.classList.add('show');
        locationInput.classList.add('error');
        searchButton.disabled = true;
    }

    // Function to clear error message
    function clearError() {
        locationError.textContent = '';
        locationError.classList.remove('show');
        locationInput.classList.remove('error');
        searchButton.disabled = false;
    }

    // Validate on input
    locationInput.addEventListener('input', function() {
        const error = validateLocationFormat(this.value);
        if (error) {
            showError(error);
        } else {
            clearError();
        }
    });

    // Validate on blur (when input loses focus)
    locationInput.addEventListener('blur', function() {
        const error = validateLocationFormat(this.value);
        if (error) {
            showError(error);
        } else {
            clearError();
        }
    });

    // Clear error when input is focused
    locationInput.addEventListener('focus', function() {
        clearError();
    });
}); 