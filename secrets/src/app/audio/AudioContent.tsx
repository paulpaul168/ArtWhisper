'use client'

import { Button } from "@/components/ui/button";
import {
    Card
} from "@/components/ui/card"
import { Play } from "lucide-react";
import { useSearchParams } from 'next/navigation'
import React, { useState, useEffect } from 'react';
import { getAudioForArtwork } from "../api";

interface AudioElement {
    id: number;
    filename: string;
    image_id: number;
    user_id: number;
    created_at: string;
}

export default function AudioContent() {
    const [audioElements, setAudioElements] = useState<AudioElement[] | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    const searchParams = useSearchParams()
    const image_id = searchParams.get('id')

    useEffect(() => {
        if (image_id) {
            getAudioForArtwork(parseInt(image_id))
                .then(data => {
                    setAudioElements(data);
                    setLoading(false);
                })
                .catch(error => {
                    setError(error as Error);
                    setLoading(false);
                });
        }
    }, [image_id]);

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error.message}</div>;
    if (!audioElements || audioElements.length === 0) return <div>No audio elements found.</div>;

    return (
        <div className="flex flex-col items-center justify-center min-h-screen w-full p-4">
            {audioElements.map(audioElement => (
                <Card key={audioElement.id} className="flex flex-row items-center justify-between w-full mb-4 p-4">
                    <span className="text-center">Card Content</span>
                    <Button
                        className="w-16 h-16 rounded-full p-0"
                        size="icon"
                    >
                        <Play className="h-6 w-6" />
                    </Button>
                </Card>
            ))}
        </div>
    )
}





