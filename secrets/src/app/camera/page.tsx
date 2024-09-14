'use client'

import React, { useRef, useState, useEffect } from 'react';
import { Camera } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';
import * as tf from '@tensorflow/tfjs';
import * as mobilenet from '@tensorflow-models/mobilenet';
import { getArtworkEmbeddings } from '@/app/api';

interface ArtworkEmbedding {
    id: string;
    embedding: number[];
}

export default function CameraPage() {
    const router = useRouter()
    const videoRef = useRef<HTMLVideoElement>(null);
    const [stream, setStream] = useState<MediaStream | null>(null);
    const [model, setModel] = useState<mobilenet.MobileNet | null>(null);
    const [artworkEmbeddings, setArtworkEmbeddings] = useState<ArtworkEmbedding[]>([]);

    useEffect(() => {
        startCamera();
        loadModel();
        fetchArtworkEmbeddings();
        return () => {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    const loadModel = async () => {
        const loadedModel = await mobilenet.load();
        setModel(loadedModel);
    };

    const fetchArtworkEmbeddings = async () => {
        try {
            const embeddings = await getArtworkEmbeddings();
            setArtworkEmbeddings(embeddings);
        } catch (error) {
            console.error('Error fetching artwork embeddings:', error);
        }
    };

    const getImageEmbedding = async (imageElement: HTMLImageElement): Promise<number[]> => {
        if (!model) {
            throw new Error('Model not loaded');
        }
        const tfImg = tf.browser.fromPixels(imageElement);
        const logits = model.infer(tfImg, true);
        const embedding = await logits.data();
        tfImg.dispose();
        logits.dispose();
        return Array.from(embedding);
    };

    const cosineSimilarity = (a: number[], b: number[]): number => {
        const dotProduct = a.reduce((sum, _, i) => sum + a[i] * b[i], 0);
        const magnitudeA = Math.sqrt(a.reduce((sum, val) => sum + val * val, 0));
        const magnitudeB = Math.sqrt(b.reduce((sum, val) => sum + val * val, 0));
        return dotProduct / (magnitudeA * magnitudeB);
    };

    const findSimilarArtwork = (embedding: number[], threshold: number = 0.8): string | null => {
        let mostSimilarArtwork: string | null = null;
        let highestSimilarity = -1;

        for (const artwork of artworkEmbeddings) {
            const similarity = cosineSimilarity(embedding, artwork.embedding);
            if (similarity > highestSimilarity && similarity >= threshold) {
                highestSimilarity = similarity;
                mostSimilarArtwork = artwork.id;
            }
        }

        return mostSimilarArtwork;
    };

    const startCamera = async () => {
        try {
            const mediaStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
            setStream(mediaStream);
            if (videoRef.current) {
                videoRef.current.srcObject = mediaStream;
            }
        } catch (error) {
            console.error('Error accessing camera:', error);
        }
    };

    const captureImage = async () => {
        if (videoRef.current) {
            const canvas = document.createElement('canvas');
            canvas.width = videoRef.current.videoWidth;
            canvas.height = videoRef.current.videoHeight;
            canvas.getContext('2d')?.drawImage(videoRef.current, 0, 0);
            const imageDataUrl = canvas.toDataURL('image/jpeg');
            console.log('Image captured:', imageDataUrl);

            const img = new Image();
            img.src = imageDataUrl;
            await new Promise((resolve) => { img.onload = resolve; });

            const embedding = await getImageEmbedding(img);
            const similarArtworkId = findSimilarArtwork(embedding);

            if (similarArtworkId) {
                router.push(`/artwork?id=${similarArtworkId}`);
            } else {
                console.log('No matching artwork found');
                // Handle case when no matching artwork is found
            }
        }
    };

    return (
        <div className="relative w-screen h-screen overflow-hidden">
            <video
                ref={videoRef}
                autoPlay
                playsInline
                className="absolute top-0 left-0 w-full h-full object-cover"
            />
            <Button
                onClick={captureImage}
                className="absolute bottom-8 left-1/2 transform -translate-x-1/2 w-16 h-16 rounded-full p-0"
                size="icon"
            >
                <Camera className="h-6 w-6" />
            </Button>
        </div>
    );
}