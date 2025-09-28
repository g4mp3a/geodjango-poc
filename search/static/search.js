document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('search-form');
    
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(searchForm);
            const params = new URLSearchParams();
            
            // Add form data to URL parameters
            for (const [key, value] of formData.entries()) {
                if (value) {
                    params.append(key, value);
                }
            }
            
            // Submit the form via fetch
            fetch(`/query/?${params.toString()}`)
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(err => {
                            throw new Error(err.error || 'Search failed');
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    // On success, redirect to results page
                    window.location.href = '/results/';
                })
                .catch(error => {
                    // Show error message to user
                    alert(error.message || 'An error occurred during search');
                    console.error('Search error:', error);
                });
        });
    }
});
