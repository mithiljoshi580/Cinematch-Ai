document.getElementById('btn-search')?.addEventListener('click', function() {
    const query = document.getElementById('search-input').value.trim();
    if (query) {
        fetchRecommendations(query);
    } else {
        alert("Please enter a movie name!");
    }
});

document.getElementById('search-input')?.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        document.getElementById('btn-search').click();
    }
});

function fetchRecommendations(movieTitle) {
    const movieGrid = document.getElementById('movie-grid');
    movieGrid.innerHTML = `<p class="text-center text-gray-400 col-span-3 py-10">AI is finding recommendations for "${movieTitle}"...</p>`;

    fetch(`/api/recommend?title=${encodeURIComponent(movieTitle)}`)
        .then(response => response.json())
        .then(data => {
            if (data.recommendations && data.recommendations.length > 0) {
                movieGrid.innerHTML = data.recommendations.map(movie => `
                    <div class="movie-card glass-effect rounded-xl overflow-hidden slide-up">
                        <div class="relative">
                            <img src="${movie.poster}" alt="${movie.title}" class="w-full h-64 object-cover" loading="lazy">
                            <div class="absolute top-4 right-4 bg-gray-900/80 backdrop-blur-sm px-3 py-1 rounded-full">
                                <span class="font-bold text-yellow-400">${movie.rating}</span>
                                <span class="text-gray-400 text-sm">/10</span>
                            </div>
                        </div>
                        <div class="p-6">
                            <div class="flex justify-between items-start mb-3">
                                <h4 class="font-bold text-lg truncate">${movie.title}</h4>
                                <span class="text-gray-400 text-sm">${movie.year}</span>
                            </div>
                            <p class="text-sm text-gray-400 mb-3">${movie.director}</p>
                            <p class="text-gray-300 text-sm mb-4 line-clamp-2">${movie.description}</p>
                            <div class="flex flex-wrap gap-2">
                                <span class="genre-tag px-3 py-1 rounded-full text-xs font-medium">${movie.genres}</span>
                            </div>
                        </div>
                    </div>
                `).join('');
            } else {
                movieGrid.innerHTML = `<p class="text-center text-red-400 col-span-3 py-10">No recommendations found. Try another movie!</p>`;
            }
        })
        .catch(error => {
            console.error("Error fetching recommendations:", error);
            movieGrid.innerHTML = `<p class="text-center text-red-400 col-span-3 py-10">Error connecting to AI backend.</p>`;
        });
}