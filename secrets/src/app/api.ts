const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ImageDetails {
    id: number;
    url: string;
    title: string;
    description: string;
    author: string;
}


export const login = async (username: string, password: string) => {
    const response = await fetch(`${API_URL}/token`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
        throw new Error('Login failed');
    }

    return response.json();
};

export const register = async (username: string, password: string) => {
    const response = await fetch(`${API_URL}/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
        throw new Error('Registration failed');
    }

    return response.json();
};

export const getAudioForArtwork = async (image_id: number) => {
    const response = await fetch(`${API_URL}/image/${image_id}/audios`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    });

    if (response.status === 404) {
        throw new Error('Could not find any image with this id');
    }
    if (!response.ok) throw new Error('Network response was not ok');

    return response.json();
};

export async function getImageForArtwork(id: number): Promise<ImageDetails> {
    const response = await fetch(`${API_URL}/images/${id}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    });

    if (!response.ok) {
        throw new Error('Failed to fetch image details');
    }

    return response.json();
}
