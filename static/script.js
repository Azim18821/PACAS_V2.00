// Add scroll handler for results header
document.addEventListener('DOMContentLoaded', function() {
    const resultsHeader = document.querySelector('.results-header');
    let lastScrollTop = 0;

    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        // Add/remove scrolled class based on scroll position
        if (scrollTop > 100) {
            resultsHeader.classList.add('scrolled');
        } else {
            resultsHeader.classList.remove('scrolled');
        }

        lastScrollTop = scrollTop;
    });
});

const site = document.getElementById("site");
const minPrice = document.getElementById("min_price");
const maxPrice = document.getElementById("max_price");
const listingType = document.getElementById("listing_type");
const sortBy = document.getElementById("sort_by");
const resultsContainer = document.getElementById("results");
const paginationContainer = document.getElementById("pagination");
const progressDiv = document.getElementById("progress");
const showMoreButton = document.getElementById("show-more");
const resultsCount = document.getElementById("results-count");

let currentPage = 1; // For UI pagination
let scrapedPage = 1; // For backend scraping
let PageWeAreOn = 1; // For UI tracking
const listingsPerPage = 6;
let currentListings = [];
let currentSearchParams = null;
let isLoadingMore = false;
let lastScrapedPage = 1; // Track the last page scraped from the server

// Cache the property grid template
const propertyGridTemplate = document.createElement('div');
propertyGridTemplate.className = 'property-grid';

// Cache the property template
const propertyTemplate = document.createElement('div');
propertyTemplate.className = 'property fade-in';

function updatePriceDropdowns() {
    const selectedSite = site.value;

    if (listingType.value === "rent") {
        if (selectedSite === 'zoopla') {
            minPrice.innerHTML = `
                <option value="">Min</option>
                <option value="100">£100 pcm</option>
                <option value="200">£200 pcm</option>
                <option value="300">£300 pcm</option>
                <option value="400">£400 pcm</option>
                <option value="500">£500 pcm</option>
                <option value="600">£600 pcm</option>
                <option value="700">£700 pcm</option>
                <option value="800">£800 pcm</option>
                <option value="900">£900 pcm</option>
                <option value="1000">£1,000 pcm</option>
                <option value="1250">£1,250 pcm</option>
                <option value="1500">£1,500 pcm</option>
                <option value="1750">£1,750 pcm</option>
                <option value="2000">£2,000 pcm</option>
                <option value="2500">£2,500 pcm</option>
                <option value="3000">£3,000 pcm</option>
                <option value="4000">£4,000 pcm</option>
                <option value="5000">£5,000 pcm</option>
                <option value="7500">£7,500 pcm</option>
                <option value="10000">£10,000 pcm</option>
                <option value="15000">£15,000 pcm</option>
                <option value="20000">£20,000 pcm</option>
            `;
            maxPrice.innerHTML = `
                <option value="">Max</option>
                <option value="200">£200 pcm</option>
                <option value="300">£300 pcm</option>
                <option value="400">£400 pcm</option>
                <option value="500">£500 pcm</option>
                <option value="600">£600 pcm</option>
                <option value="700">£700 pcm</option>
                <option value="800">£800 pcm</option>
                <option value="900">£900 pcm</option>
                <option value="1000">£1,000 pcm</option>
                <option value="1250">£1,250 pcm</option>
                <option value="1500">£1,500 pcm</option>
                <option value="1750">£1,750 pcm</option>
                <option value="2000">£2,000 pcm</option>
                <option value="2500">£2,500 pcm</option>
                <option value="3000">£3,000 pcm</option>
                <option value="4000">£4,000 pcm</option>
                <option value="5000">£5,000 pcm</option>
                <option value="7500">£7,500 pcm</option>
                <option value="10000">£10,000 pcm</option>
                <option value="15000">£15,000 pcm</option>
                <option value="20000">£20,000 pcm</option>
                <option value="25000">£25,000 pcm</option>
            `;
        } else {
            minPrice.innerHTML = `
                <option value="">Min</option>
                <option value="500">£500 pcm</option>
                <option value="1000">£1,000 pcm</option>
                <option value="1500">£1,500 pcm</option>
                <option value="2000">£2,000 pcm</option>
                <option value="3000">£3,000 pcm</option>
            `;
            maxPrice.innerHTML = `
                <option value="">Max</option>
                <option value="1500">£1,500 pcm</option>
                <option value="2500">£2,500 pcm</option>
                <option value="5000">£5,000 pcm</option>
                <option value="10000">£10,000 pcm</option>
            `;
        }
    } else {
        if (selectedSite === 'zoopla') {
            minPrice.innerHTML = `
                <option value="">Min</option>
                <option value="50000">£50,000</option>
                <option value="60000">£60,000</option>
                <option value="70000">£70,000</option>
                <option value="80000">£80,000</option>
                <option value="90000">£90,000</option>
                <option value="100000">£100,000</option>
                <option value="110000">£110,000</option>
                <option value="120000">£120,000</option>
                <option value="130000">£130,000</option>
                <option value="140000">£140,000</option>
                <option value="150000">£150,000</option>
                <option value="160000">£160,000</option>
                <option value="170000">£170,000</option>
                <option value="180000">£180,000</option>
                <option value="190000">£190,000</option>
                <option value="200000">£200,000</option>
                <option value="250000">£250,000</option>
                <option value="300000">£300,000</option>
                <option value="400000">£400,000</option>
                <option value="500000">£500,000</option>
                <option value="600000">£600,000</option>
                <option value="700000">£700,000</option>
                <option value="800000">£800,000</option>
                <option value="900000">£900,000</option>
                <option value="1000000">£1,000,000</option>
            `;
            maxPrice.innerHTML = `
                <option value="">Max</option>
                <option value="60000">£60,000</option>
                <option value="70000">£70,000</option>
                <option value="80000">£80,000</option>
                <option value="90000">£90,000</option>
                <option value="100000">£100,000</option>
                <option value="110000">£110,000</option>
                <option value="120000">£120,000</option>
                <option value="130000">£130,000</option>
                <option value="140000">£140,000</option>
                <option value="150000">£150,000</option>
                <option value="160000">£160,000</option>
                <option value="170000">£170,000</option>
                <option value="180000">£180,000</option>
                <option value="190000">£190,000</option>
                <option value="200000">£200,000</option>
                <option value="250000">£250,000</option>
                <option value="300000">£300,000</option>
                <option value="400000">£400,000</option>
                <option value="500000">£500,000</option>
                <option value="600000">£600,000</option>
                <option value="700000">£700,000</option>
                <option value="800000">£800,000</option>
                <option value="900000">£900,000</option>
                <option value="1000000">£1,000,000</option>
                <option value="1500000">£1,500,000</option>
                <option value="2000000">£2,000,000</option>
                <option value="3000000">£3,000,000</option>
                <option value="4000000">£4,000,000</option>
                <option value="5000000">£5,000,000</option>
            `;
        } else {
            minPrice.innerHTML = `
                <option value="">Min</option>
                <option value="50000">£50,000</option>
                <option value="100000">£100,000</option>
                <option value="200000">£200,000</option>
                <option value="300000">£300,000</option>
                <option value="500000">£500,000</option>
            `;
            maxPrice.innerHTML = `
                <option value="">Max</option>
                <option value="300000">£300,000</option>
                <option value="500000">£500,000</option>
                <option value="1000000">£1,000,000</option>
                <option value="2000000">£2,000,000</option>
            `;
        }
    }
}

// Add event listener for site changes
site.addEventListener("change", updatePriceDropdowns);
// Add event listener for listing type changes
listingType.addEventListener("change", updatePriceDropdowns);
// Initial call to set up dropdowns
updatePriceDropdowns();

function sortListings(listings, sortBy) {
    const sortedListings = [...listings]; // Create a copy to avoid mutating original array

    switch(sortBy) {
        case 'price_asc':
            return sortedListings.sort((a, b) => {
                const priceA = parseInt(a.price.replace(/[^0-9]/g, ''));
                const priceB = parseInt(b.price.replace(/[^0-9]/g, ''));
                return priceA - priceB;
            });
        case 'price_desc':
            return sortedListings.sort((a, b) => {
                const priceA = parseInt(a.price.replace(/[^0-9]/g, ''));
                const priceB = parseInt(b.price.replace(/[^0-9]/g, ''));
                return priceB - priceA;
            });
        case 'beds_asc':
            return sortedListings.sort((a, b) => {
                const bedsA = parseInt(a.specs?.match(/(\d+)\s*bed/i)?.[1] || 0);
                const bedsB = parseInt(b.specs?.match(/(\d+)\s*bed/i)?.[1] || 0);
                return bedsA - bedsB;
            });
        case 'beds_desc':
            return sortedListings.sort((a, b) => {
                const bedsA = parseInt(a.specs?.match(/(\d+)\s*bed/i)?.[1] || 0);
                const bedsB = parseInt(b.specs?.match(/(\d+)\s*bed/i)?.[1] || 0);
                return bedsB - bedsA;
            });
        case 'newest':
            return sortedListings; // Assuming API returns in newest first order
        case 'oldest':
            return sortedListings.reverse(); // Reverse the order for oldest
        default:
            return sortedListings;
    }
}

sortBy.addEventListener('change', () => {
    if (currentListings.length > 0) {
        currentListings = sortListings(currentListings, sortBy.value);
        currentPage = 1; // Reset to first page when sorting
        displayCurrentPage();
    }
});

async function performSearch() {
    const locationInput = document.getElementById("location").value;
    const keywords = document.getElementById("keywords").value;
    const minBeds = document.getElementById("min_beds").value;
    const maxBeds = document.getElementById("max_beds").value;
    const searchButton = document.getElementById("searchButton");
    const locationError = document.getElementById("location-error");
    const resultsContainer = document.getElementById("results");
    const resultsCount = document.getElementById("results-count");
    const progressDiv = document.getElementById("progress");


    const minBeds = document.getElementById("min_beds").value;
    const maxBeds = document.getElementById("max_beds").value;
    const keywords = document.getElementById("keywords").value;

    // Create search parameters object
    const searchParams = {
        site: document.getElementById("site").value || 'zoopla',
        location: locationInput,
        listing_type: document.getElementById("listing_type").value || 'sale',
        min_price: document.getElementById("min_price").value || '0',
        max_price: document.getElementById("max_price").value || '10000000',
        min_beds: minBeds || '0',
        max_beds: maxBeds || '10',
        keywords: keywords || '',
        sort_by: document.getElementById("sort_by").value || 'newest'
    };

    // Clear previous error, results, pagination, and count
    locationError.textContent = "";
    resultsContainer.innerHTML = "";
    paginationContainer.innerHTML = ""; // Clear pagination
    showMoreButton.style.display = "none"; // Hide show more button
    resultsCount.textContent = ""; // Clear the results count

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(searchParams)
        });

        if (!response.ok) {
            const errorText = await response.text();
            try {
                const errorJson = JSON.parse(errorText);
                throw new Error(errorJson.error || 'Search failed');
            } catch (e) {
                throw new Error('Search failed: Invalid server response');
            }
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Search error:', error);
        resultsContainer.innerHTML = `
            <div class="error-message">
                <p>An error occurred while searching. Please try again.</p>
                <p class="error-details">${error.message}</p>
            </div>`;
        throw error;
    }
    paginationContainer.innerHTML = ""; // Clear pagination
    showMoreButton.style.display = "none"; // Hide show more button
    resultsCount.textContent = ""; // Clear the results count

    if (!locationInput) {
        locationError.textContent = "Please enter a location";
        return;
    }

    // Reset pagination state
    currentPage = 1;
    scrapedPage = 1;
    lastScrapedPage = 1;
    currentListings = [];
    isLoadingMore = false;

    // Disable search button while processing
    searchButton.disabled = true;

    try {
        // Show progress indicator
        progressDiv.style.display = "block";
        progressDiv.innerHTML = "Searching for properties...";

        // Prepare search parameters
        const searchParams = {
            site: site.value || 'zoopla',
            location: locationInput || '',
            listing_type: listingType.value || 'sale',
            min_price: minPrice.value || '0',
            max_price: maxPrice.value || '10000000',
            min_beds: minBeds || '0',
            max_beds: maxBeds || '10',
            keywords: keywords || '',
            sort_by: sortBy.value || 'newest'
        };

        // Make API call
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(searchParams)
        });

        const data = await response.json();

        // Handle validation errors
        if (!response.ok) {
            if (response.status === 400 && data.error) {
                locationError.textContent = data.error;
                locationError.classList.add('show');
                document.getElementById("location").classList.add('error');
            } else {
                console.error('Search error:', data);
                resultsContainer.innerHTML = `
                    <div class="error-message">
                        <p>Error: ${data.error || 'Failed to perform search'}</p>
                    </div>`;
            }
            return;
        }

        // Handle any errors
        if (!response.ok) {
            try {
                const error = await response.json();
                showError(`An error occurred while searching. Please try again.\n\n${error.error}`);
            } catch (e) {
                showError('An error occurred while searching. Please try again.');
            }
            return;
        }

        // Update UI with results
        currentSearchParams = searchParams;
        currentListings = data.listings || [];
        currentPage = 1;
        lastScrapedPage = data.current_page || 1;

        // Update results display
        updateResults(
            currentListings,
            data.total_found || 0,
            data.total_pages || 1,
            data.current_page || 1,
            data.is_complete || false
        );

        // Update show more button visibility
        updateShowMoreButtonVisibility(data.total_pages || 1);

    } catch (error) {
        console.error('Search error:', error);
        resultsContainer.innerHTML = `
            <div class="error-message">
                <p>An error occurred while searching. Please try again.</p>
                <p class="error-details">${error.message}</p>
            </div>`;
    } finally {
        // Re-enable search button and hide progress
        searchButton.disabled = false;
        progressDiv.style.display = "none";
    }
}

function updateShowMoreButtonVisibility(totalPages) {
    if (PageWeAreOn === totalPages) {
        showMoreButton.style.display = 'block';
        showMoreButton.textContent = 'Show More Listings';
        showMoreButton.disabled = false;
        console.log('Show More button visible - we are on the final page');
    } else {
        showMoreButton.style.display = 'none';
        console.log('Show More button hidden - not on final page');
    }
}

function displayCurrentPage() {
    // Clear the results container first
    resultsContainer.innerHTML = '';

    // Calculate total pages based on listings per page
    const totalPages = Math.ceil(currentListings.length / listingsPerPage);
    console.log(`Total listings: ${currentListings.length}`);
    console.log(`Generating ${totalPages} pages (${listingsPerPage} listings per page)`);
    console.log(`We are on page ${PageWeAreOn} of ${totalPages - 1}`);

    // Create and add total results count
    // const totalResults = document.createElement('div');
    // totalResults.className = 'total-results';
    // totalResults.textContent = `Found ${currentListings.length} properties`;
    // resultsContainer.appendChild(totalResults);

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

function changePage(direction) {
    const totalPages = Math.ceil(currentListings.length / listingsPerPage);
    const newPage = currentPage + direction;

    if (newPage < 1 || newPage > totalPages) return;

    currentPage = newPage;
    PageWeAreOn = newPage; // Update PageWeAreOn when changing pages
    console.log(`Changing page to ${PageWeAreOn} of ${totalPages - 1}`);

    // Update Show More button visibility
    updateShowMoreButtonVisibility(totalPages);

    // Update the display
    displayCurrentPage();

    // Scroll to results section smoothly
    const searchResults = document.querySelector('.section');
    if (searchResults) {
        window.scrollTo({
            top: searchResults.offsetTop - 20,
            behavior: 'smooth'
        });
    }
}

function createListingCard(listing) {
    const card = document.createElement('div');
    card.className = 'property';

    // Add image
    const imageWrapper = document.createElement('div');
    imageWrapper.className = 'property-image';
    const img = document.createElement('img');
    img.src = listing.image || 'https://via.placeholder.com/300x200?text=No+Image';
    img.alt = listing.title || 'Property';
    img.onerror = () => img.src = 'https://via.placeholder.com/300x200?text=No+Image';
    imageWrapper.appendChild(img);
    card.appendChild(imageWrapper);

    // Add details container
    const details = document.createElement('div');
    details.className = 'property-details';

    // Add price
    const price = document.createElement('div');
    price.className = 'price';
    price.textContent = listing.price;
    details.appendChild(price);

    // Add title
    const title = document.createElement('h3');
    title.textContent = listing.title || listing.address;
    details.appendChild(title);

    // Add specs (bedrooms)
    if (listing.specs) {
        const specs = document.createElement('div');
        specs.className = 'specs';
        specs.textContent = listing.specs;
        details.appendChild(specs);
    }

    // Add description
    if (listing.desc) {
        const desc = document.createElement('p');
        desc.className = 'description';
        desc.textContent = listing.desc;
        details.appendChild(desc);
    }

    // Add source badge
    const source = document.createElement('div');
    source.className = 'source-badge';
    source.textContent = listing.source;
    details.appendChild(source);

    // Add view button
    const viewButton = document.createElement('a');
    viewButton.href = listing.url;
    viewButton.className = 'view-button';
    viewButton.target = '_blank';
    viewButton.rel = 'noopener noreferrer';
    viewButton.textContent = 'View Details';
    details.appendChild(viewButton);

    card.appendChild(details);
    return card;
}

function updatePagination() {
    const totalPages = Math.ceil(currentListings.length / listingsPerPage);

    paginationContainer.innerHTML = `
        <div class="pagination-controls">
            <button class="prev-btn" ${currentPage === 1 ? 'disabled' : ''}>⬅ Previous</button>
            <span>Page ${currentPage} of ${totalPages}</span>
            <button class="next-btn" ${currentPage === totalPages ? 'disabled' : ''}>Next ➡</button>
        </div>
    `;

    // Add event listeners to the new buttons
    const prevButton = paginationContainer.querySelector('.prev-btn');
    const nextButton = paginationContainer.querySelector('.next-btn');

    prevButton.addEventListener('click', () => {
        if (currentPage > 1) {
            changePage(-1);
        }
    });

    nextButton.addEventListener('click', () => {
        if (currentPage < totalPages) {
            changePage(1);
        }
    });
}

async function loadMoreResults() {
    const showMoreButton = document.getElementById('show-more');
    const resultsCount = document.getElementById('results-count');

    // Prevent duplicate requests while loading
    if (isLoadingMore) {
        return;
    }

    isLoadingMore = true;
    showMoreButton.disabled = true;
    showMoreButton.textContent = 'Loading...';

    try {
        const site = document.getElementById('site').value;
        const nextScrapedPage = scrapedPage + 1;

        // Get the current search parameters from the form
        const searchParams = {
            location: document.getElementById('location').value,
            site: site,
            listing_type: document.getElementById('listing_type').value,
            min_price: document.getElementById('min_price').value || '0',
            max_price: document.getElementById('max_price').value || '10000000',
            min_beds: document.getElementById('min_beds').value || '0',
            max_beds: document.getElementById('max_beds').value || '10',
            keywords: document.getElementById('keywords').value || ''
        };

        console.log('Loading more results:', {
            site,
            nextScrapedPage,
            scrapedPage,
            lastScrapedPage,
            PageWeAreOn,
            searchParams
        });

        const response = await fetch('/api/search/next-page', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                search_params: searchParams,
                current_page: nextScrapedPage // Use nextScrapedPage for backend communication
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error('Server error:', errorData);
            throw new Error(errorData.error || errorData.details || 'Failed to load more results');
        }

        const data = await response.json();
        console.log('Received data:', data);

        if (data.listings && data.listings.length > 0) {
            // For Zoopla, check if the new listings are valid
            if (site === 'zoopla') {
                const hasValidListings = data.listings.some(listing => 
                    listing && 
                    listing.title && 
                    listing.price && 
                    listing.url
                );

                if (!hasValidListings) {
                    console.log('Skipping empty or invalid Zoopla results');
                    // Try the next page if available
                    if (data.current_page < data.total_pages) {
                        scrapedPage = data.current_page + 1;
                        lastScrapedPage = scrapedPage;
                        showMoreButton.textContent = 'Loading Next Page...';
                        showMoreButton.disabled = false;
                        showMoreButton.style.display = 'block';
                        setTimeout(() => {
                            loadMoreResults();
                        }, 1000);
                    } else {
                        updateShowMoreButtonVisibility(data.total_pages);
                    }
                    return;
                }
            }

            // Add new listings to existing ones and sort all listings
            currentListings = sortListings([...currentListings, ...data.listings], sortBy.value);

            // Update the results count
            resultsCount.textContent = `Found ${currentListings.length} properties`;

            // Update display with all listings
            displayCurrentPage();

            // Update scrapedPage and lastScrapedPage for backend communication
            scrapedPage = data.current_page;
            lastScrapedPage = data.current_page;

            // Update PageWeAreOn for UI purposes only
            PageWeAreOn = Math.ceil(currentListings.length / listingsPerPage) - 1;

            // Update Show More button visibility
            updateShowMoreButtonVisibility(data.total_pages);
        } else {
            // If no listings found, try the next page
            if (data.current_page < data.total_pages) {
                console.log('No listings found on page', data.current_page, 'trying next page');
                scrapedPage = data.current_page + 1; // Increment scrapedPage for backend
                lastScrapedPage = scrapedPage; // Update lastScrapedPage to match
                PageWeAreOn = Math.ceil(currentListings.length / listingsPerPage) - 1; // Update PageWeAreOn for UI
                showMoreButton.textContent = 'Loading Next Page...';
                showMoreButton.disabled = false;
                showMoreButton.style.display = 'block';
                // Wait for current request to complete before trying next page
                setTimeout(() => {
                    loadMoreResults();
                }, 1000);
            } else {
                updateShowMoreButtonVisibility(data.total_pages);
            }
        }
    } catch (error) {
        console.error('Error loading more results:', error);
        showMoreButton.textContent = `Error: ${error.message}`;
        showMoreButton.disabled = false;
    } finally {
        isLoadingMore = false;
    }
}

function updateResults(listings, totalFound, totalPages, currentPage, isComplete) {
    const resultsContainer = document.getElementById("results");
    const resultsCount = document.getElementById("results-count");

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
            </div>`;        showMoreButton.style.display = 'none';
        paginationContainer.style.display = 'none';
        return;
    }

    // Check if we're getting results from Zoopla and if they're empty
    const site = document.getElementById('site').value;
    if (site === 'zoopla') {
        console.log('Checking Zoopla listings validity');
        console.log('First listing:', listings[0]);

        // More lenient validation for Zoopla listings
        const hasValidListings = listings.some(listing => {
            // Check if listing exists and has at least a title or price
            const isValid = listing && (listing.title || listing.price);
            if (!isValid) {
                console.log('Invalid listing:', listing);
            }
            return isValid;
        });

        if (!hasValidListings) {
            console.log('No valid Zoopla listings found');
            resultsContainer.innerHTML = `
                <div class="no-results">
                    <h3>No valid properties found</h3>
                    <p>Try adjusting your search criteria</p>
                </div>`;
            showMoreButton.style.display = 'none';
            paginationContainer.style.display = 'none';
            return;
        }
    }

    // Store the listings in currentListings for pagination
    currentListings = listings;

    // Store search parameters if they're not already stored
    if (!currentSearchParams) {
        currentSearchParams = {
            site: document.getElementById('site').value,
            location: document.getElementById('location').value,
            min_price: document.getElementById('min_price').value,
            max_price: document.getElementById('max_price').value,
            min_beds: document.getElementById('min_beds').value,
            max_beds: document.getElementById('max_beds').value,
            keywords: document.getElementById('keywords').value,
            listing_type: document.getElementById('listing_type').value
        };
    }

    // Display current page of listings
    displayCurrentPage();

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

// Add event listener for Show More button
document.getElementById('show-more').addEventListener('click', loadMoreResults);

// Footer Functions
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

function showPrivacyPolicy() {
    alert('Privacy Policy will be available soon. This feature is coming in a future update.');
}

function showTerms() {
    alert('Terms of Service will be available soon. This feature is coming in a future update.');
}

function showContact() {
    alert('Contact information will be available soon. This feature is coming in a future update.');
}

function showError(message) {
    // Existing showError function implementation.  Replace with your actual error display logic.
    alert(message);
}