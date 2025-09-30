document.addEventListener('DOMContentLoaded', function() {
  try {
    const path = window.location.pathname || '';
    const hasParams = !!window.location.search;
    if (path.startsWith('/results') && hasParams) {
      fetch(`/query/${window.location.search}`)
        .then(response => {
          if (!response.ok) {
            return response.json().then(err => {
              throw new Error(err.error || 'Search failed');
            });
          }
          return response.json();
        })
        .then(data => {
          if (typeof window.renderMapResults === 'function') {
            window.renderMapResults(data);
          } else {
            console.warn('renderMapResults is not available');
          }
        })
        .catch(error => {
          alert(error.message || 'An error occurred during search');
          console.error('Search error:', error);
        });
    }
  } catch (err) {
    console.error('Failed to initialize results fetch:', err);
  }
});
