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

    // Check if user is logged in
    checkUserSession();

    // Initialize email modal
    initEmailModal();
});

// Check user session and update UI
async function checkUserSession() {
    try {
        const response = await fetch('/api/user');
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.user) {
                updateUserHeader(data.user);
                updateFavoriteCount();
            }
        }
    } catch (error) {
        console.log('Not logged in');
    }
}

// Update user header with name
function updateUserHeader(user) {
    const userHeader = document.getElementById('userHeader');
    const guestHeader = document.getElementById('guestHeader');
    const userName = document.getElementById('userName');
    
    if (userHeader && userName && guestHeader) {
        userName.textContent = user.name;
        userHeader.style.display = 'block';
        guestHeader.style.display = 'none';
    }
}

// Update favorite count
async function updateFavoriteCount() {
    try {
        const response = await fetch('/api/favorites');
        if (response.ok) {
            const data = await response.json();
            const favCount = document.getElementById('favCount');
            if (favCount && data.favorites) {
                favCount.textContent = data.favorites.length;
            }
        }
    } catch (error) {
        console.error('Error updating favorite count:', error);
    }
}

// Logout function
async function logout() {
    try {
        const response = await fetch('/api/logout', {
            method: 'POST'
        });
        if (response.ok) {
            location.reload();
        }
    } catch (error) {
        console.error('Error logging out:', error);
    }
}

// Show favorites modal with user's saved properties
async function showFavorites() {
    const favoritesModal = document.getElementById('favoritesModal');
    const favoritesContent = document.getElementById('favoritesContent');
    
    favoritesModal.style.display = 'block';
    favoritesContent.innerHTML = '<p style=\"text-align: center; color: #999;\">Loading favorites...</p>';
    
    try {
        const response = await fetch('/api/favorites');
        if (!response.ok) {
            throw new Error('Failed to load favorites');
        }
        
        const data = await response.json();
        const favorites = data.favorites || [];
        
        if (favorites.length === 0) {
            favoritesContent.innerHTML = `
                <div class="empty-favorites">
                    <p>💔 No favorites yet</p>
                    <p style="font-size: 14px;">Start adding properties to your favorites!</p>
                </div>
            `;
        } else {
            const grid = document.createElement('div');
            grid.className = 'favorites-grid';
            
            favorites.forEach(fav => {
                const item = document.createElement('div');
                item.className = 'favorite-item';
                
                item.innerHTML = `
                    <button class="favorite-remove-btn" onclick="removeFavoriteFromModal('${fav.property_url}')" title="Remove">&times;</button>
                    <img src="${fav.property_image || 'https://via.placeholder.com/300x200?text=No+Image'}" alt="${fav.property_title}">
                    <div class="favorite-item-details">
                        <div class="price">${fav.property_price}</div>
                        <h4>${fav.property_title}</h4>
                        <div class="meta">${fav.bedrooms} | ${fav.site}</div>
                        <a href="${fav.property_url}" target="_blank" class="view-button" style="display: inline-block; margin-top: 10px;">View Property</a>
                    </div>
                `;
                
                grid.appendChild(item);
            });
            
            favoritesContent.innerHTML = '';
            favoritesContent.appendChild(grid);
        }
    } catch (error) {
        console.error('Error loading favorites:', error);
        favoritesContent.innerHTML = '<p style=\"text-align: center; color: #ff4757;\">Failed to load favorites</p>';
    }
}

// Remove favorite from modal
async function removeFavoriteFromModal(propertyUrl) {
    try {
        const response = await fetch('/api/favorites/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ property_url: propertyUrl })
        });
        
        if (response.ok) {
            updateFavoriteCount();
            showFavorites(); // Refresh the favorites display
        }
    } catch (error) {
        console.error('Error removing favorite:', error);
    }
}

// Show login modal
function showLoginModal() {
    const loginModal = document.getElementById('loginModal');
    loginModal.style.display = 'block';
}

// Show register modal from header
function showRegisterFromHeader() {
    const accountModal = document.getElementById('accountModal');
    accountModal.style.display = 'block';
    // Clear any previous email
    document.getElementById('accountEmail').value = '';
    document.getElementById('accountEmail').removeAttribute('readonly');
    setTimeout(() => {
        document.getElementById('accountEmail').focus();
    }, 300);
}

// Email Modal Management
let pendingPropertyUrl = null;
let pendingPropertyData = null;
let propertyViewCount = 0;

// Helper function to show inline messages
function showMessage(elementId, message, type = 'error') {
    const messageEl = document.getElementById(elementId);
    if (messageEl) {
        messageEl.textContent = message;
        messageEl.className = `inline-message ${type} show`;
        
        // Auto-hide success messages after 3 seconds
        if (type === 'success') {
            setTimeout(() => {
                messageEl.classList.remove('show');
            }, 3000);
        }
    }
}

// Helper function to hide inline messages
function hideMessage(elementId) {
    const messageEl = document.getElementById(elementId);
    if (messageEl) {
        messageEl.classList.remove('show');
    }
}

function initEmailModal() {
    const modal = document.getElementById('emailModal');
    const accountModal = document.getElementById('accountModal');
    const loginModal = document.getElementById('loginModal');
    const favoritesModal = document.getElementById('favoritesModal');
    const closeBtn = document.querySelector('.email-modal-close');
    const accountCloseBtn = document.querySelector('.account-modal-close');
    const loginCloseBtn = document.querySelector('.login-modal-close');
    const favoritesCloseBtn = document.querySelector('.favorites-modal-close');
    const emailForm = document.getElementById('emailForm');
    const accountForm = document.getElementById('accountForm');
    const loginForm = document.getElementById('loginForm');

    // Load view count from localStorage
    propertyViewCount = parseInt(localStorage.getItem('propertyViewCount') || '0');

    // Close modals
    if (closeBtn) {
        closeBtn.onclick = function() {
            modal.style.display = 'none';
            hideMessage('emailModalMessage');
            pendingPropertyUrl = null;
            pendingPropertyData = null;
        };
    }

    // Close account modal
    if (accountCloseBtn) {
        accountCloseBtn.onclick = function() {
            accountModal.style.display = 'none';
            hideMessage('accountModalMessage');
        };
    }

    // Close login modal
    if (loginCloseBtn) {
        loginCloseBtn.onclick = function() {
            loginModal.style.display = 'none';
            hideMessage('loginModalMessage');
        };
    }

    // Close favorites modal
    if (favoritesCloseBtn) {
        favoritesCloseBtn.onclick = function() {
            favoritesModal.style.display = 'none';
        };
    }

    // Close modals when clicking outside
    window.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
        if (event.target === accountModal) {
            accountModal.style.display = 'none';
        }
        if (event.target === loginModal) {
            loginModal.style.display = 'none';
        }
        if (event.target === favoritesModal) {
            favoritesModal.style.display = 'none';
        }
    };

    // Show register modal from login
    const showRegisterLink = document.getElementById('showRegisterLink');
    if (showRegisterLink) {
        showRegisterLink.onclick = function(e) {
            e.preventDefault();
            loginModal.style.display = 'none';
            accountModal.style.display = 'block';
            const email = document.getElementById('loginEmail').value.trim();
            if (email && email.includes('@')) {
                document.getElementById('accountEmail').value = email;
            }
        };
    }

    // Handle login form submission
    if (loginForm) {
        loginForm.onsubmit = async function(e) {
            e.preventDefault();
            
            const email = document.getElementById('loginEmail').value.trim();
            const password = document.getElementById('loginPassword').value.trim();
            
            if (!email || !password) {
                showMessage('loginModalMessage', 'Please enter email and password', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    loginModal.style.display = 'none';
                    updateUserHeader(result.user);
                    updateFavoriteCount();
                    showMessage('loginModalMessage', '✓ Logged in successfully!', 'success');
                } else {
                    showMessage('loginModalMessage', result.error || 'Login failed', 'error');
                }
            } catch (error) {
                showMessage('loginModalMessage', 'Login failed. Please try again.', 'error');
            }
        };
    }

    // Create account link in initial modal
    const createAccountLink = document.getElementById('createAccountLink');
    if (createAccountLink) {
        createAccountLink.onclick = function(e) {
            e.preventDefault();
            const email = document.getElementById('modalEmail').value.trim();
            
            if (!email || !email.includes('@')) {
                showMessage('emailModalMessage', 'Please enter your email first', 'error');
                document.getElementById('modalEmail').focus();
                return;
            }
            
            // Save email and show account modal
            localStorage.setItem('userEmail', email);
            modal.style.display = 'none';
            hideMessage('accountModalMessage');
            document.getElementById('accountEmail').value = email;
            document.getElementById('accountEmail').setAttribute('readonly', true);
            accountModal.style.display = 'block';
            
            setTimeout(() => {
                document.getElementById('accountName').focus();
            }, 300);
        };
    }

    // Close modal when clicking X
    if (closeBtn) {
        closeBtn.onclick = function() {
            modal.style.display = 'none';
            hideMessage('emailModalMessage');
            pendingPropertyUrl = null;
            pendingPropertyData = null;
        };
    }

    // Close modal when clicking outside
    window.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
            pendingPropertyUrl = null;
            pendingPropertyData = null;
        }
    };

    // Handle email form submission
    if (emailForm) {
        emailForm.onsubmit = async function(e) {
            e.preventDefault();
            
            const email = document.getElementById('modalEmail').value.trim();
            const phone = document.getElementById('modalPhone').value.trim();
            const wantsCallback = document.getElementById('agentCallbackCheckbox').checked;
            
            if (!email || !email.includes('@')) {
                showMessage('emailModalMessage', 'Please enter a valid email address', 'error');
                return;
            }

            // Validate phone if provided
            if (phone && !isValidUKPhone(phone)) {
                showMessage('emailModalMessage', 'Please enter a valid UK phone number (e.g., 07123456789 or 020 1234 5678)', 'error');
                return;
            }

            // Save email to localStorage
            localStorage.setItem('userEmail', email);
            if (phone) {
                localStorage.setItem('userPhone', phone);
            }

            // Increment view count
            propertyViewCount++;
            localStorage.setItem('propertyViewCount', propertyViewCount.toString());

            // Capture the lead
            try {
                await captureLeadAndRedirect(email, phone, wantsCallback, pendingPropertyData);
            } catch (error) {
                console.error('Error capturing lead:', error);
                // Still redirect even if tracking fails
                window.open(pendingPropertyUrl, '_blank');
                modal.style.display = 'none';
            }
        };
    }

    // Handle account form submission
    let verificationSent = false;
    let verificationVerified = false;
    
    if (accountForm) {
        accountForm.onsubmit = async function(e) {
            e.preventDefault();
            
            const name = document.getElementById('accountName').value.trim();
            const email = document.getElementById('accountEmail').value.trim();
            const phone = document.getElementById('accountPhone').value.trim();
            const password = document.getElementById('accountPassword').value.trim();
            const submitBtn = document.getElementById('accountSubmitBtn');
            
            if (!email || !email.includes('@')) {
                showMessage('accountModalMessage', 'Please enter a valid email address', 'error');
                return;
            }
            
            if (!password || password.length < 6) {
                showMessage('accountModalMessage', 'Password must be at least 6 characters', 'error');
                return;
            }
            
            if (!isValidUKPhone(phone)) {
                showMessage('accountModalMessage', 'Please enter a valid UK phone number (e.g., 07123456789 or 020 1234 5678)', 'error');
                return;
            }

            // Step 1: Send verification code
            if (!verificationSent) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Sending Code...';
                
                try {
                    const response = await fetch('/api/send-verification-code', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email: email })
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        verificationSent = true;
                        document.getElementById('verificationSection').style.display = 'block';
                        document.getElementById('verificationEmailDisplay').textContent = email;
                        submitBtn.textContent = 'Verify & Create Account';
                        submitBtn.disabled = false;
                        showMessage('accountModalMessage', '✓ Verification code sent! Check your email.', 'success');
                        
                        // For development - log the code
                        if (result.debug_code) {
                            console.log('DEBUG: Verification code:', result.debug_code);
                        }
                        
                        setTimeout(() => {
                            document.getElementById('verificationCode').focus();
                        }, 300);
                    } else {
                        throw new Error(result.error || 'Failed to send code');
                    }
                } catch (error) {
                    showMessage('accountModalMessage', error.message || 'Failed to send verification code', 'error');
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Create Free Account';
                }
                return;
            }
            
            // Step 2: Verify code
            if (verificationSent && !verificationVerified) {
                const code = document.getElementById('verificationCode').value.trim();
                
                if (!code || code.length !== 6) {
                    showMessage('accountModalMessage', 'Please enter the 6-digit code', 'error');
                    return;
                }
                
                submitBtn.disabled = true;
                submitBtn.textContent = 'Verifying...';
                
                try {
                    const response = await fetch('/api/verify-code', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email: email, code: code })
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        verificationVerified = true;
                        showMessage('accountModalMessage', '✓ Email verified! Creating account...', 'success');
                        
                        // Register the user with password
                        const registerResponse = await fetch('/api/register', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                email: email,
                                password: password,
                                name: name,
                                phone: phone
                            })
                        });
                        
                        const registerResult = await registerResponse.json();
                        
                        if (registerResponse.ok) {
                            // Store in localStorage
                            localStorage.setItem('userName', name);
                            localStorage.setItem('userPhone', phone);
                            localStorage.setItem('accountCreated', 'true');
                            localStorage.setItem('emailVerified', 'true');
                            
                            // Capture lead for tracking
                            await captureAccountLead(name, email, phone);
                            
                            setTimeout(() => {
                                accountModal.style.display = 'none';
                                
                                // Update UI with logged in user
                                updateUserHeader(registerResult.user);
                                updateFavoriteCount();
                                
                                // Reset for next time
                                verificationSent = false;
                                verificationVerified = false;
                                document.getElementById('verificationSection').style.display = 'none';
                                submitBtn.textContent = 'Create Free Account';
                                
                                // Redirect to pending property
                                if (pendingPropertyUrl) {
                                    window.open(pendingPropertyUrl, '_blank');
                                    pendingPropertyUrl = null;
                                    pendingPropertyData = null;
                                }
                            }, 1500);
                        } else {
                            throw new Error(registerResult.error || 'Failed to create account');
                        }
                    } else {
                        throw new Error(result.error || 'Invalid code');
                    }
                } catch (error) {
                    showMessage('accountModalMessage', error.message || 'Verification failed', 'error');
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Verify & Create Account';
                }
                return;
            }
        };
    }
    
    // Handle resend code button
    const resendCodeBtn = document.getElementById('resendCodeBtn');
    if (resendCodeBtn) {
        resendCodeBtn.onclick = async function() {
            const email = document.getElementById('accountEmail').value.trim();
            resendCodeBtn.disabled = true;
            resendCodeBtn.textContent = 'Sending...';
            
            try {
                const response = await fetch('/api/send-verification-code', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showMessage('accountModalMessage', '✓ New code sent!', 'success');
                    if (result.debug_code) {
                        console.log('DEBUG: New verification code:', result.debug_code);
                    }
                    
                    // Re-enable after 30 seconds
                    setTimeout(() => {
                        resendCodeBtn.disabled = false;
                        resendCodeBtn.textContent = 'Resend Code';
                    }, 30000);
                } else {
                    throw new Error(result.error || 'Failed to resend');
                }
            } catch (error) {
                showMessage('accountModalMessage', error.message || 'Failed to resend code', 'error');
                resendCodeBtn.disabled = false;
                resendCodeBtn.textContent = 'Resend Code';
            }
        };
    }
}

function showEmailModal(propertyUrl, propertyData) {
    const savedEmail = localStorage.getItem('userEmail');
    const savedPhone = localStorage.getItem('userPhone');
    const accountCreated = localStorage.getItem('accountCreated');
    const viewCount = parseInt(localStorage.getItem('propertyViewCount') || '0');
    
    // Check if account already created
    if (accountCreated) {
        // Full access - just redirect
        if (savedEmail && savedPhone) {
            captureLeadAndRedirect(savedEmail, savedPhone, true, propertyData).catch(console.error);
        }
        window.open(propertyUrl, '_blank');
        return;
    }
    
    // Check if should show account creation modal (after 5 views)
    if (viewCount >= 5 && savedEmail && !savedPhone) {
        showAccountModal(propertyUrl, propertyData, savedEmail);
        return;
    }
    
    // Check if email already captured
    if (savedEmail) {
        // Email already captured, track and redirect
        propertyViewCount++;
        localStorage.setItem('propertyViewCount', propertyViewCount.toString());
        captureLeadAndRedirect(savedEmail, savedPhone, false, propertyData).catch(console.error);
        window.open(propertyUrl, '_blank');
        return;
    }

    // Show modal for first-time users
    pendingPropertyUrl = propertyUrl;
    pendingPropertyData = propertyData;
    
    const modal = document.getElementById('emailModal');
    modal.style.display = 'block';
    
    // Focus on email input
    setTimeout(() => {
        document.getElementById('modalEmail').focus();
    }, 300);
}

function showAccountModal(propertyUrl, propertyData, email) {
    pendingPropertyUrl = propertyUrl;
    pendingPropertyData = propertyData;
    
    const modal = document.getElementById('accountModal');
    document.getElementById('accountEmail').value = email;
    modal.style.display = 'block';
    
    // Focus on name input
    setTimeout(() => {
        document.getElementById('accountName').focus();
    }, 300);
}

function isValidUKPhone(phone) {
    // Remove spaces and common separators
    const cleaned = phone.replace(/[\s-().]/g, '');
    
    // UK phone: 10-11 digits, starts with 0 or +44
    const ukPattern = /^(0|\+44)[0-9]{9,10}$/;
    
    // Block obvious fakes
    const fakePatterns = /^(0{10,}|1{10,}|9{10,}|1234567890|0000000000)$/;
    
    return ukPattern.test(cleaned) && !fakePatterns.test(cleaned);
}

async function captureLeadAndRedirect(email, phone, wantsCallback, propertyData) {
    const modal = document.getElementById('emailModal');
    
    try {
        const response = await fetch('/api/capture-lead', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                phone: phone || '',
                wants_callback: wantsCallback,
                property_url: propertyData.url,
                property_title: propertyData.title,
                property_price: propertyData.price,
                site: propertyData.site,
                lead_type: 'property_view'
            })
        });

        if (response.ok) {
            console.log('Lead captured successfully');
        } else {
            console.warn('Failed to capture lead');
        }
    } catch (error) {
        console.error('Error capturing lead:', error);
    } finally {
        // Always redirect and close modal
        window.open(pendingPropertyUrl, '_blank');
        modal.style.display = 'none';
        pendingPropertyUrl = null;
        pendingPropertyData = null;
    }
}

async function captureAccountLead(name, email, phone) {
    try {
        const response = await fetch('/api/capture-lead', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                phone: phone,
                name: name,
                wants_callback: true,
                property_url: pendingPropertyData?.url || '',
                property_title: pendingPropertyData?.title || '',
                property_price: pendingPropertyData?.price || '',
                site: pendingPropertyData?.site || '',
                lead_type: 'account_creation'
            })
        });

        if (response.ok) {
            console.log('Account lead captured successfully');
        } else {
            console.warn('Failed to capture account lead');
        }
    } catch (error) {
        console.error('Error capturing account lead:', error);
    }
}

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
    const location = document.getElementById("location").value;
    const keywords = document.getElementById("keywords").value;
    const minBeds = document.getElementById("min_beds").value;
    const maxBeds = document.getElementById("max_beds").value;
    const searchButton = document.getElementById("searchButton");
    const locationError = document.getElementById("location-error");
    const resultsContainer = document.getElementById("results");
    const resultsCount = document.getElementById("results-count");
    const emptyState = document.getElementById("empty-state");

    // Hide empty state when search starts
    if (emptyState) {
        emptyState.style.display = "none";
    }

    // Clear previous error, results, pagination, and count
    locationError.textContent = "";
    resultsContainer.innerHTML = "";
    paginationContainer.innerHTML = ""; // Clear pagination
    showMoreButton.style.display = "none"; // Hide show more button
    resultsCount.textContent = ""; // Clear the results count

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
            site: site.value,
            location: location,
            listing_type: listingType.value,
            min_price: minPrice.value,
            max_price: maxPrice.value,
            min_beds: minBeds,
            max_beds: maxBeds,
            keywords: keywords,
            sort_by: sortBy.value
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
        if (response.status === 400 && data.error) {
            locationError.textContent = data.error;
            locationError.classList.add('show');
            document.getElementById("location").classList.add('error');
            return;
        }

        // Handle other errors
        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch results');
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
    
    // Add favorite button
    const favoriteBtn = document.createElement('button');
    favoriteBtn.className = 'favorite-btn';
    favoriteBtn.innerHTML = '♡';
    favoriteBtn.title = 'Add to favorites';
    favoriteBtn.onclick = function(e) {
        e.preventDefault();
        e.stopPropagation();
        toggleFavorite(listing, favoriteBtn);
    };
    card.appendChild(favoriteBtn);
    
    // Check if already favorited (async)
    checkIfFavorite(listing.url, favoriteBtn);
    
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
    
    // Add view button with email capture
    const viewButton = document.createElement('a');
    viewButton.href = '#';
    viewButton.className = 'view-button';
    viewButton.textContent = 'View Details';
    
    // Intercept click to show email modal
    viewButton.onclick = function(e) {
        e.preventDefault();
        showEmailModal(listing.url, {
            url: listing.url,
            title: listing.title,
            price: listing.price,
            site: listing.source
        });
    };
    
    details.appendChild(viewButton);
    
    card.appendChild(details);
    return card;
}

// Toggle favorite status
async function toggleFavorite(listing, button) {
    try {
        // Check if user is logged in
        const userResponse = await fetch('/api/user');
        if (!userResponse.ok) {
            // Not logged in - show login modal
            showLoginModal();
            return;
        }
        
        const isActive = button.classList.contains('active');
        
        if (isActive) {
            // Remove from favorites
            const response = await fetch('/api/favorites/remove', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ property_url: listing.url })
            });
            
            if (response.ok) {
                button.classList.remove('active');
                button.innerHTML = '♡';
                button.title = 'Add to favorites';
                updateFavoriteCount();
            }
        } else {
            // Add to favorites
            const response = await fetch('/api/favorites/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    property_url: listing.url,
                    property_title: listing.title,
                    property_price: listing.price,
                    property_image: listing.image,
                    site: listing.source,
                    bedrooms: listing.specs || '',
                    location: listing.address || ''
                })
            });
            
            if (response.ok) {
                button.classList.add('active');
                button.innerHTML = '♥';
                button.title = 'Remove from favorites';
                updateFavoriteCount();
            }
        }
    } catch (error) {
        console.error('Error toggling favorite:', error);
    }
}

// Check if property is favorited
async function checkIfFavorite(propertyUrl, button) {
    try {
        const response = await fetch('/api/favorites/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ property_url: propertyUrl })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.is_favorite) {
                button.classList.add('active');
                button.innerHTML = '♥';
                button.title = 'Remove from favorites';
            }
        }
    } catch (error) {
        console.log('Not logged in or error checking favorite');
    }
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
            </div>`;
        showMoreButton.style.display = 'none';
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
    const modal = document.createElement('div');
    modal.className = 'email-modal';
    modal.style.display = 'block';
    modal.innerHTML = `
        <div class="email-modal-content legal-modal">
            <span class="email-modal-close" onclick="this.parentElement.parentElement.remove()">&times;</span>
            <h2>Privacy Policy</h2>
            <div class="legal-content">
                <p><strong>Last Updated: January 4, 2026</strong></p>
                
                <h3>1. Introduction</h3>
                <p>PacasHomes, operated by Aztura LTD ("we", "our", "us"), respects your privacy. This policy explains how we collect, use, and protect your personal data in compliance with UK GDPR and Data Protection Act 2018.</p>
                
                <h3>2. Data We Collect</h3>
                <p><strong>Account Information:</strong></p>
                <ul>
                    <li>Email address (required for account creation and property alerts)</li>
                    <li>Name (optional, for personalization)</li>
                    <li>Phone number (optional, for property inquiries)</li>
                    <li>Password (stored encrypted using bcrypt hashing)</li>
                </ul>
                
                <p><strong>Usage Data:</strong></p>
                <ul>
                    <li>Search preferences and history</li>
                    <li>Favorited properties</li>
                    <li>Page views and click data (stored locally)</li>
                    <li>Browser type and IP address (server logs)</li>
                </ul>
                
                <h3>3. How We Use Your Data</h3>
                <ul>
                    <li>To provide property search aggregation services</li>
                    <li>To save your favorite properties and preferences</li>
                    <li>To send verification emails and property alerts (with your consent)</li>
                    <li>To improve our service and user experience</li>
                    <li>To comply with legal obligations</li>
                </ul>
                
                <h3>4. Data Sharing</h3>
                <p>We do NOT sell your personal data. We may share data only:</p>
                <ul>
                    <li><strong>With property websites:</strong> When you click "View Details", you are redirected to the original listing on Rightmove, Zoopla, or OpenRent. Their privacy policies apply thereafter.</li>
                    <li><strong>Email service provider:</strong> MailerSend (for verification emails only)</li>
                    <li><strong>Legal requirements:</strong> If required by law or to protect our legal rights</li>
                </ul>
                
                <h3>5. Your Rights (UK GDPR)</h3>
                <p>You have the right to:</p>
                <ul>
                    <li><strong>Access:</strong> Request a copy of your personal data</li>
                    <li><strong>Rectification:</strong> Correct inaccurate data</li>
                    <li><strong>Erasure:</strong> Request deletion of your account and data</li>
                    <li><strong>Portability:</strong> Receive your data in a portable format</li>
                    <li><strong>Object:</strong> Opt-out of marketing communications</li>
                    <li><strong>Withdraw consent:</strong> At any time</li>
                </ul>
                <p>To exercise these rights, contact us at: <a href="mailto:privacy@pacashomes.co.uk">privacy@pacashomes.co.uk</a></p>
                
                <h3>6. Data Security</h3>
                <p>We implement industry-standard security measures:</p>
                <ul>
                    <li>Passwords encrypted with bcrypt hashing</li>
                    <li>Secure HTTPS connection</li>
                    <li>Regular security audits</li>
                    <li>Limited data retention (accounts inactive for 2+ years may be deleted)</li>
                </ul>
                
                <h3>7. Cookies</h3>
                <p>We use essential cookies for:</p>
                <ul>
                    <li>Session management (login state)</li>
                    <li>Property view tracking (stored locally in your browser)</li>
                </ul>
                <p>We do not use advertising or tracking cookies from third parties.</p>
                
                <h3>8. Children's Privacy</h3>
                <p>Our service is not intended for users under 18. We do not knowingly collect data from children.</p>
                
                <h3>9. Changes to This Policy</h3>
                <p>We may update this policy. Significant changes will be notified via email.</p>
                
                <h3>10. Contact Us</h3>
                <p>For privacy concerns: <a href="mailto:privacy@pacashomes.co.uk">privacy@pacashomes.co.uk</a></p>
                <p>Company: Aztura LTD<br>
                Company No: 16805710</p>
            </div>
        </div>
    `;
    modal.onclick = function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    };
    document.body.appendChild(modal);
}

function showTerms() {
    const modal = document.createElement('div');
    modal.className = 'email-modal';
    modal.style.display = 'block';
    modal.innerHTML = `
        <div class="email-modal-content legal-modal">
            <span class="email-modal-close" onclick="this.parentElement.parentElement.remove()">&times;</span>
            <h2>Terms of Service</h2>
            <div class="legal-content">
                <p><strong>Last Updated: January 4, 2026</strong></p>
                
                <h3>1. Acceptance of Terms</h3>
                <p>By accessing PacasHomes, operated by Aztura LTD, you agree to these Terms of Service. If you disagree, please do not use our service.</p>
                
                <h3>2. Description of Service</h3>
                <p>PacasHomes is a property search aggregator that:</p>
                <ul>
                    <li>Collects publicly available property listings from Rightmove, Zoopla, and OpenRent</li>
                    <li>Provides a unified search interface</li>
                    <li>Redirects users to original listings for full details and contact</li>
                    <li><strong>Does NOT host, sell, or manage properties directly</strong></li>
                </ul>
                
                <h3>3. Important Disclaimers</h3>
                <p><strong>⚠️ WE ARE AN AGGREGATOR, NOT A PROPERTY AGENT</strong></p>
                <ul>
                    <li>All properties are listed and managed by third-party agents</li>
                    <li>We are not responsible for property accuracy, availability, or condition</li>
                    <li>Prices, descriptions, and images are sourced from third-party sites and may be outdated</li>
                    <li>Always verify details directly with the listing agent</li>
                </ul>
                
                <h3>4. Trademark Notice</h3>
                <p>Rightmove®, Zoopla®, and OpenRent® are registered trademarks of their respective owners. PacasHomes is not affiliated with, endorsed by, or sponsored by these companies. We use their names solely for descriptive purposes to indicate data sources.</p>
                
                <h3>5. Data Sources & Attribution</h3>
                <p>Property data is aggregated from publicly available listings on:</p>
                <ul>
                    <li><strong>Rightmove</strong> - rightmove.co.uk</li>
                    <li><strong>Zoopla</strong> - zoopla.co.uk</li>
                    <li><strong>OpenRent</strong> - openrent.com</li>
                </ul>
                <p>Each listing displays a source badge. Clicking "View Details" redirects you to the original listing where the respective site's terms apply.</p>
                
                <h3>6. User Accounts</h3>
                <p><strong>Account Creation:</strong></p>
                <ul>
                    <li>You must provide accurate information</li>
                    <li>You must verify your email address</li>
                    <li>You are responsible for password security</li>
                    <li>One account per person</li>
                </ul>
                
                <p><strong>Account Termination:</strong></p>
                <ul>
                    <li>You may delete your account at any time</li>
                    <li>We may suspend accounts that violate these terms</li>
                    <li>Inactive accounts (2+ years) may be deleted</li>
                </ul>
                
                <h3>7. Acceptable Use</h3>
                <p><strong>You MAY:</strong></p>
                <ul>
                    <li>Search for properties for personal use</li>
                    <li>Save favorites and create alerts</li>
                    <li>Share individual listings with others</li>
                </ul>
                
                <p><strong>You MAY NOT:</strong></p>
                <ul>
                    <li>Use our service for commercial resale or redistribution</li>
                    <li>Scrape, copy, or automate data extraction from our site</li>
                    <li>Create fake accounts or spam our system</li>
                    <li>Attempt to hack, disrupt, or overload our servers</li>
                    <li>Violate any applicable laws or regulations</li>
                </ul>
                
                <h3>8. Limitation of Liability</h3>
                <p><strong>PacasHomes is provided "AS IS" without warranties.</strong></p>
                <ul>
                    <li>We do not guarantee listing accuracy or availability</li>
                    <li>We are not liable for property transaction disputes</li>
                    <li>We are not responsible for third-party website content or policies</li>
                    <li>Our total liability is limited to £100 or fees paid (if any)</li>
                </ul>
                
                <h3>9. Intellectual Property</h3>
                <ul>
                    <li><strong>Our content:</strong> PacasHomes logo, design, and code are our property</li>
                    <li><strong>Listing content:</strong> Belongs to respective property sites and agents</li>
                    <li>You may not reproduce our site design or branding</li>
                </ul>
                
                <h3>10. Changes to Terms</h3>
                <p>We may update these terms. Continued use after changes constitutes acceptance. Significant changes will be notified via email.</p>
                
                <h3>11. Governing Law</h3>
                <p>These terms are governed by the laws of England and Wales. Disputes will be resolved in UK courts.</p>
                
                <h3>12. Contact</h3>
                <p>For terms questions: <a href="mailto:legal@pacashomes.co.uk">legal@pacashomes.co.uk</a></p>
                <p>Company: Aztura LTD<br>
                Company No: 16805710</p>
            </div>
        </div>
    `;
    modal.onclick = function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    };
    document.body.appendChild(modal);
}

function showContact() {
    const modal = document.createElement('div');
    modal.className = 'email-modal';
    modal.style.display = 'block';
    modal.innerHTML = `
        <div class="email-modal-content legal-modal">
            <span class="email-modal-close" onclick="this.parentElement.parentElement.remove()">&times;</span>
            <h2>Contact Us</h2>
            <div class="legal-content">
                <p>We'd love to hear from you! Reach out for any questions, concerns, or feedback.</p>
                
                <h3>📧 Email Contacts</h3>
                <ul>
                    <li><strong>General Inquiries:</strong> <a href="mailto:info@pacashomes.co.uk">info@pacashomes.co.uk</a></li>
                    <li><strong>Technical Support:</strong> <a href="mailto:support@pacashomes.co.uk">support@pacashomes.co.uk</a></li>
                    <li><strong>Privacy Matters:</strong> <a href="mailto:privacy@pacashomes.co.uk">privacy@pacashomes.co.uk</a></li>
                    <li><strong>Legal & Terms:</strong> <a href="mailto:legal@pacashomes.co.uk">legal@pacashomes.co.uk</a></li>
                    <li><strong>Takedown Requests:</strong> <a href="mailto:takedown@pacashomes.co.uk">takedown@pacashomes.co.uk</a></li>
                </ul>
                
                <h3>🏢 Company Information</h3>
                <p><strong>Company Name:</strong> Aztura LTD<br>
                <strong>Company No:</strong> 16805710<br>
                <strong>Operating Name:</strong> PacasHomes</p>
                
                <h3>⚠️ Important Notes</h3>
                <p><strong>About Property Listings:</strong></p>
                <ul>
                    <li>We do NOT manage or own any listed properties</li>
                    <li>For property inquiries, contact the listing agent directly via Rightmove, Zoopla, or OpenRent</li>
                    <li>Click "View Details" on any listing to reach the original agent</li>
                </ul>
                
                <h3>🕐 Response Time</h3>
                <p>We aim to respond within 48 hours on business days (Monday-Friday).</p>
                
                <h3>💡 Frequently Asked Questions</h3>
                <p><strong>Q: Can I list my property on PacasHomes?</strong><br>
                A: No, we are an aggregator only. Please list on Rightmove, Zoopla, or OpenRent and it will appear here automatically.</p>
                
                <p><strong>Q: Why isn't my search showing results?</strong><br>
                A: Try broadening your search criteria. Some areas may have limited listings available.</p>
                
                <p><strong>Q: How do I delete my account?</strong><br>
                A: Email <a href="mailto:privacy@pacashomes.co.uk">privacy@pacashomes.co.uk</a> with your account email.</p>
                
                <p><strong>Q: Are listings real-time?</strong><br>
                A: Listings are refreshed regularly but may not be instant. Always verify on the source website.</p>
            </div>
        </div>
    `;
    modal.onclick = function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    };
    document.body.appendChild(modal);
}
function showTakedownPolicy() {
    const modal = document.createElement('div');
    modal.className = 'email-modal';
    modal.style.display = 'block';
    modal.innerHTML = `
        <div class="email-modal-content legal-modal">
            <span class="email-modal-close" onclick="this.parentElement.parentElement.remove()">&times;</span>
            <h2>Takedown Policy & Copyright Notice</h2>
            <div class="legal-content">
                <p><strong>Last Updated: January 4, 2026</strong></p>
                
                <h3>1. Our Role as an Aggregator</h3>
                <p>PacasHomes, operated by Aztura LTD, is a property search aggregator that displays publicly available property listings from third-party websites including Rightmove, Zoopla, and OpenRent. We:</p>
                <ul>
                    <li>Do NOT own, manage, or have any affiliation with the listed properties</li>
                    <li>Do NOT host original property content</li>
                    <li>Redirect users to the original source for full details and contact</li>
                    <li>Display source attribution on every listing</li>
                </ul>
                
                <h3>2. Copyright & Intellectual Property</h3>
                <p>We respect the intellectual property rights of others. All property listings, images, descriptions, and related content are the property of:</p>
                <ul>
                    <li>The respective property listing websites (Rightmove, Zoopla, OpenRent)</li>
                    <li>The property agents and landlords who created the listings</li>
                    <li>Any applicable copyright holders</li>
                </ul>
                
                <h3>3. Takedown Request Process</h3>
                <p>If you believe that content displayed on PacasHomes infringes your copyright, intellectual property rights, or is displayed without proper authorization, please submit a takedown request.</p>
                
                <p><strong>To submit a takedown request, email: <a href="mailto:takedown@pacashomes.co.uk">takedown@pacashomes.co.uk</a></strong></p>
                
                <p>Please include the following information:</p>
                <ul>
                    <li><strong>Your Contact Information:</strong> Name, email address, phone number, and mailing address</li>
                    <li><strong>Content Identification:</strong> URL of the specific listing(s) on PacasHomes you want removed</li>
                    <li><strong>Copyright/Rights Information:</strong> Description of the copyrighted work or rights being infringed</li>
                    <li><strong>Ownership Proof:</strong> Evidence that you own the rights to the content (e.g., you are the property agent, photographer, or copyright holder)</li>
                    <li><strong>Good Faith Statement:</strong> A statement that you have a good faith belief that the use is not authorized</li>
                    <li><strong>Accuracy Statement:</strong> A statement, under penalty of perjury, that the information in your notice is accurate</li>
                    <li><strong>Signature:</strong> Your physical or electronic signature</li>
                </ul>
                
                <h3>4. Our Response Timeline</h3>
                <ul>
                    <li><strong>Acknowledgment:</strong> Within 48 hours of receiving your request</li>
                    <li><strong>Review:</strong> We will review your claim within 3-5 business days</li>
                    <li><strong>Action:</strong> If valid, content will be removed from our cache within 24 hours</li>
                    <li><strong>Notification:</strong> You will receive confirmation once action is taken</li>
                </ul>
                
                <h3>5. Important Notes</h3>
                <p><strong>Cache & Temporary Storage:</strong></p>
                <ul>
                    <li>Listings are cached for up to 24 hours for performance</li>
                    <li>After removal, content may persist in cache temporarily</li>
                    <li>Clearing cache expires listings after 24 hours automatically</li>
                </ul>
                
                <p><strong>Source Website:</strong></p>
                <ul>
                    <li>Removing content from PacasHomes does NOT remove it from the original source (Rightmove, Zoopla, OpenRent)</li>
                    <li>You must contact the original website directly to remove the listing at its source</li>
                    <li>We recommend addressing the issue with the source website first</li>
                </ul>
                
                <h3>6. Counter-Notifications</h3>
                <p>If you believe content was removed in error, you may submit a counter-notification to <a href="mailto:legal@pacashomes.co.uk">legal@pacashomes.co.uk</a> with:</p>
                <ul>
                    <li>Your contact information</li>
                    <li>Identification of the removed content</li>
                    <li>A statement that the content was removed by mistake</li>
                    <li>Your consent to jurisdiction of UK courts</li>
                    <li>Your physical or electronic signature</li>
                </ul>
                
                <h3>7. Repeat Infringers</h3>
                <p>We will terminate accounts of users who are repeat copyright infringers where appropriate.</p>
                
                <h3>8. False Claims</h3>
                <p><strong>Warning:</strong> Submitting false or fraudulent takedown requests may result in legal liability. Only submit requests if you have a legitimate claim.</p>
                
                <h3>9. Alternative Resolution</h3>
                <p>For property agents and websites:</p>
                <ul>
                    <li>We are open to discussing partnerships and authorized data access</li>
                    <li>Contact <a href="mailto:partnerships@pacashomes.co.uk">partnerships@pacashomes.co.uk</a> for collaboration opportunities</li>
                    <li>We respect robots.txt and can implement specific exclusions upon request</li>
                </ul>
                
                <h3>10. Contact Information</h3>
                <ul>
                    <li><strong>Takedown Requests:</strong> <a href="mailto:takedown@pacashomes.co.uk">takedown@pacashomes.co.uk</a></li>
                    <li><strong>Legal Matters:</strong> <a href="mailto:legal@pacashomes.co.uk">legal@pacashomes.co.uk</a></li>
                    <li><strong>General Inquiries:</strong> <a href="mailto:info@pacashomes.co.uk">info@pacashomes.co.uk</a></li>
                    <li><strong>Company:</strong> Aztura LTD</li>
                    <li><strong>Company No:</strong> 16805710</li>
                </ul>
                
                <h3>11. Governing Law</h3>
                <p>This policy is governed by the laws of England and Wales. All takedown requests will be processed in accordance with UK copyright law and the Copyright, Designs and Patents Act 1988.</p>
                <p><strong>Operated by:</strong> Aztura LTD (Company No: 16805710)</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                
                <p style="text-align: center; color: #666; font-size: 14px;">
                    <strong>We respect intellectual property rights and will respond promptly to valid takedown requests.</strong>
                </p>
            </div>
        </div>
    `;
    modal.onclick = function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    };
    document.body.appendChild(modal);
}