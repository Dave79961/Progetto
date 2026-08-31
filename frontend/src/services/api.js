const API_BASE_URL = 'http://127.0.0.1:5000/api';

async function request(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        headers: {
            'Content-Type': 'application/json',
            ...(options.headers || {}),
        },
        ...options,
    });

    if (!response.ok) {
        throw new Error(
            `Errore API ${response.status}: ${response.statusText}`
        );
    }

    return response.json();
}

export function getAuctionRankings() {
    return request('/auction');
}

export function getSuggestedLineup() {
    return request('/lineup');
}

export function getMarketMoves() {
    return request('/market');
}