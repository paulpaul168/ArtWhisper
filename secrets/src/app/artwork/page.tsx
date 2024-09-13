'use client'

import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"
import { Play } from "lucide-react";
import { useSearchParams } from 'next/navigation'
import React, { useState, useEffect } from 'react';
import { getAudioForArtwork, getImageForArtwork } from "../api";
import { AudioRecordButton } from "@/components/audioRecordingButton";

interface AudioElement {
    id: number;
    filename: string;
    image_id: number;
    user_id: number;
    created_at: string;
}

interface ImageDetails {
    id: number;
    url: string;
    title: string;
    description: string;
    artist: string;
}

export default function ArtworkPage() {
    const [audioElements, setAudioElements] = useState<AudioElement[] | null>(null);
    const [imageDetails, setImageDetails] = useState<ImageDetails | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    const searchParams = useSearchParams()
    const image_id = searchParams.get('id')

    useEffect(() => {
        if (image_id) {
            const id = parseInt(image_id);
            Promise.all([getImageForArtwork(id), getAudioForArtwork(id)])
                .then(([imageData, audioData]) => {
                    setImageDetails(imageData);
                    setAudioElements(audioData);
                    setLoading(false);
                })
                .catch(error => {
                    setError(error as Error);
                    setLoading(false);
                });
        }
    }, [image_id]);

    const handleRecordingComplete = (blob: Blob) => {
        // Here you would typically upload the blob to your server
        console.log('Recording completed, blob size:', blob.size);
        // You might want to add the new recording to audioElements here
    };

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error.message}</div>;
    if (!imageDetails) return <div>No artwork found.</div>;

    return (
        <div className="flex flex-col items-center justify-center min-h-screen w-full p-4 pb-16 sm:pb-24 max-w-3xl mx-auto">
            <Card className="w-full mb-8">
                <CardHeader>
                    <CardTitle className="text-xl sm:text-2xl">{imageDetails.title}</CardTitle>
                    <CardDescription className="text-sm sm:text-base">by {imageDetails.artist}</CardDescription>
                </CardHeader>
                <CardContent>
                    <img src={imageDetails.url} alt={imageDetails.title} className="w-full h-auto mb-4 rounded-lg" />
                    <p className="text-sm sm:text-base">{imageDetails.description}</p>
                </CardContent>
            </Card>

            <h2 className="text-xl sm:text-2xl font-bold mb-4">Audio Recordings</h2>
            {(!audioElements || audioElements.length === 0) ? (
                <div className="text-center">No audio recordings found for this artwork.</div>
            ) : (
                <div className="w-full space-y-4">
                    {audioElements.map(audioElement => (
                        <Card key={audioElement.id} className="flex flex-row items-center justify-between w-full p-3 sm:p-4">
                            <span className="text-sm sm:text-base">Audio Recording {audioElement.id}</span>
                            <Button
                                className="w-12 h-12 sm:w-14 sm:h-14 rounded-full p-0"
                                size="icon"
                            >
                                <Play className="h-5 w-5 sm:h-6 sm:w-6" />
                            </Button>
                        </Card>
                    ))}
                </div>
            )}
            <div className="m-8">
            <AudioRecordButton onRecordingComplete={handleRecordingComplete} />
            </div>
        </div>
    )
}