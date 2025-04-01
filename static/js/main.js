let currentPage = 1;
let currentSearchParams = null;
let isLoading = false;

async function searchProperties() {
    try {
        // Get search parameters
        const location = document.getElementById('location').value;
        const listingType = document.getElementById('listingType').value;
        const minPrice = document.getElementById('minPrice').value;
        const maxPrice = document.getElementById('maxPrice').value;
        const minBeds = document.getElementById('minBeds').value;
        const maxBeds = document.getElementById('maxBeds').value;
        const keywords = document.getElementById('keywords').value;
        const site = document.getElementById('site').value;

        // Reset pagination state for new search
        currentPage = 1;
        currentSearchParams = null;
        isLoading = false;

        // Show loading state
        const loadingIndicator = document.getElementById('loadingIndicator');
        loadingIndicator.style.display = 'block';

        // Clear previous results
        const resultsContainer = document.getElementById('results');
        resultsContainer.innerHTML = '';

        // Prepare search parameters
        const searchParams = {
            site: site,
            location: location,
            listing_type: listingType,
            min_price: minPrice,
            max_price: maxPrice,
            min_beds: minBeds,
            max_beds: maxBeds,
            keywords: keywords,
            current_page: 1  // Reset to first page for new search
        };

        // Store current search parameters for pagination
        currentSearchParams = searchParams;

        // Determine which endpoint to use based on site selection
        const endpoint = site === 'combined' ? '/api/search/combined' : '/api/search';

        // Make the API request
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(searchParams)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Display site statistics if this is a combined search
        if (site === 'combined' && data.site_stats) {
            displaySiteStats(data.site_stats);
        }

        // Update show more button visibility
        updateShowMoreButton(data.has_next_page);

        // Display results
        await displayResults(data.listings, data.total_found, data.total_pages, data.current_page);

    } catch (error) {
        console.error('Error:', error);
        const resultsContainer = document.getElementById('results');
        resultsContainer.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    } finally {
        // Hide loading state
        const loadingIndicator = document.getElementById('loadingIndicator');
        loadingIndicator.style.display = 'none';
    }
}

function displaySiteStats(stats) {
    const statsContainer = document.createElement('div');
    statsContainer.className = 'site-stats';
    statsContainer.innerHTML = `
        <h3>Search Statistics</h3>
        <div class="stats-grid">
            <div class="stat-item">
                <h4>Zoopla</h4>
                <p>Listings: ${stats.zoopla.listings}</p>
                <p>Total Pages: ${stats.zoopla.total_pages}</p>
                <p>Source: ${stats.zoopla.source}</p>
            </div>
            <div class="stat-item">
                <h4>Rightmove</h4>
                <p>Listings: ${stats.rightmove.listings}</p>
                <p>Total Pages: ${stats.rightmove.total_pages}</p>
                <p>Source: ${stats.rightmove.source}</p>
            </div>
        </div>
    `;
    
    // Insert stats before the results container
    const resultsContainer = document.getElementById('results');
    resultsContainer.parentNode.insertBefore(statsContainer, resultsContainer);
}

async function displayResults(listings, totalFound, totalPages, currentPage) {
    const resultsContainer = document.getElementById('results');
    const resultsCount = document.getElementById('results-count');
    
    // Update results count
    if (totalFound > 0) {
        resultsCount.textContent = `Found ${totalFound} properties`;
    } else {
        resultsCount.textContent = 'No properties found';
    }

    // Clear previous results if this is the first page
    if (currentPage === 1) {
        resultsContainer.innerHTML = '';
        currentListings = [];
    }

    if (!listings || listings.length === 0) {
        console.log('No listings found, displaying empty state');
        resultsContainer.innerHTML = `
            <div class="no-results">
                <h3>No properties found</h3>
                <p>Try adjusting your search criteria</p>
            </div>`;
        showMoreButton.style.display = 'none';
        paginationContainer.style.display = 'none';
        return;
    }

    // Store the listings in currentListings for pagination
    currentListings = listings;
    
    // Display current page of listings
    await displayCurrentPage();

    // Update scrapedPage and lastScrapedPage for backend communication
    scrapedPage = currentPage;
    lastScrapedPage = currentPage;
    
    // Update PageWeAreOn for UI purposes only
    PageWeAreOn = Math.ceil(currentListings.length / listingsPerPage) - 1;

    // Handle pagination visibility separately
    if (currentListings.length > listingsPerPage) {
        paginationContainer.style.display = 'block';
        updatePagination();
    } else {
        paginationContainer.style.display = 'none';
    }
}

async function loadMoreResults() {
    if (isLoading || !currentSearchParams || !hasMoreResults) {
        return;
    }

    try {
        isLoading = true;
        currentPage++;

        // Show loading state
        const loadingIndicator = document.getElementById('loadingIndicator');
        loadingIndicator.style.display = 'block';

        // Update search parameters with current page
        const searchParams = {
            ...currentSearchParams,
            current_page: currentPage
        };

        // Always use the next-page endpoint
        const response = await fetch('/api/search/next-page', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                search_params: searchParams,
                current_page: currentPage
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Handle errors
        if (data.error) {
            throw new Error(data.error);
        }

        // Append new results to existing listings
        const resultsContainer = document.getElementById('results');
        await displayResults(data.listings, data.total_found, data.total_pages, data.current_page);

        // Update pagination UI
        updatePaginationUI(data);

        // Update show more button visibility
        updateShowMoreButton(data.has_next_page);

    } catch (error) {
        console.error('Error:', error);
        const resultsContainer = document.getElementById('results');
        resultsContainer.innerHTML += `<div class="error">Error loading more results: ${error.message}</div>`;
    } finally {
        // Hide loading state
        const loadingIndicator = document.getElementById('loadingIndicator');
        loadingIndicator.style.display = 'none';
        isLoading = false;
    }
}

async function displayCurrentPage() {
    // Clear the results container first
    resultsContainer.innerHTML = '';
    
    // Calculate total pages based on listings per page
    const totalPages = Math.ceil(currentListings.length / listingsPerPage);
    console.log(`Total listings: ${currentListings.length}`);
    console.log(`Generating ${totalPages} pages (${listingsPerPage} listings per page)`);
    console.log(`We are on page ${PageWeAreOn} of ${totalPages - 1}`);
    
    // Create property grid
    const propertyGrid = document.createElement('div');
    propertyGrid.className = 'property-grid';
    
    const start = (currentPage - 1) * listingsPerPage;
    const end = start + listingsPerPage;
    const listingsToShow = currentListings.slice(start, end);
    
    // Add listings to grid
    listingsToShow.forEach(listing => {
        const card = createListingCard(listing);
        propertyGrid.appendChild(card);
    });

    // Add the grid to the results container
    resultsContainer.appendChild(propertyGrid);

    // Update pagination if needed
    if (currentListings.length > listingsPerPage) {
        updatePagination();
    }

    // Update Show More button visibility
    updateShowMoreButtonVisibility(totalPages);
} 