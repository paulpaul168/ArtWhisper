const API_URL =
  typeof window === "undefined"
    ? process.env.NEXT_PUBLIC_API_URL
    : window.location.origin + "/api";

interface ImageDetails {
  id: number;
  url: string;
  title: string;
  description: string;
  artist: string;
}

interface ArtworkEmbedding {
  id: string;
  embedding: number[];
}

export const login = async (username: string, password: string) => {
  const response = await fetch(`${API_URL}/token`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    throw new Error("Username or password is wrong");
  }

  return response.json();
};

export const register = async (username: string, password: string) => {
  const response = await fetch(`${API_URL}/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    throw new Error("Registration failed");
  }

  return response.json();
};

export const getAudioForArtwork = async (image_id: number) => {
  const response = await fetch(`${API_URL}/image/${image_id}/audios`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (response.status === 404) {
    throw new Error("Could not find any image with this id");
  }
  if (!response.ok) throw new Error("Network response was not ok");

  return response.json();
};

export async function getImageForArtwork(id: number): Promise<ImageDetails> {
  const response = await fetch(`${API_URL}/images/${id}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch image details");
  }

  return response.json();
}

export async function getAudio(id: number): Promise<Blob> {
  const response = await fetch(`${API_URL}/audio/${id}`, {
    method: "GET",
    headers: {
      Accept: "audio/*",
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch audio file");
  }

  return response.blob();
}

export function getAudioUrl(id: number): string {
  return `${API_URL}/audio/${id}`;
}

export function isLoggedIn(): boolean {
  return localStorage.getItem("token") !== null;
}

export async function uploadAudio(
  image_id: number,
  blob: Blob
): Promise<number> {
  const formData = new FormData();
  formData.append("audio", blob, "recording.ogg");
  formData.append("image_id", image_id.toString());

  const authToken = localStorage.getItem("token");

  if (!authToken) {
    throw new Error("No authentication token found");
  }

  const response = await fetch(`${API_URL}/upload-audio/${image_id}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${authToken}`, // Add the auth token to the headers
    },
    body: formData,
  });

  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in again");
  }

  if (!response.ok) {
    throw new Error("Failed to upload audio");
  }

  const data = await response.json();
  return data.id;
}

export async function getArtworkEmbeddings(): Promise<ArtworkEmbedding[]> {
  const response = await fetch(`${API_URL}/artwork-embeddings`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch artwork embeddings");
  }

  return response.json();
}

export async function findSimilarArtwork(
  imageBlob: Blob
): Promise<{ similar_artwork_id: string | null; similarity: number }> {
  const formData = new FormData();
  formData.append("image", imageBlob, "image.jpg");

  const response = await fetch(`${API_URL}/find-similar-artwork`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Failed to find similar artwork");
  }

  return response.json();
}
