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
import { Play, Pause, ChevronLeft, Info, Camera } from "lucide-react";
import { useSearchParams } from 'next/navigation'
import React, { useState, useEffect, useRef } from 'react';
import { getAudioForArtwork, getImageForArtwork, uploadAudio, getAudioUrl } from "../api";
import { AudioRecordButton } from "@/components/audioRecordingButton";
import AudioWaveform from './AudioWaveform';
import Link from "next/link";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import Image from "next/image"


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
    const [playingAudio, setPlayingAudio] = useState<number | null>(null);
    const audioRef = useRef<HTMLAudioElement | null>(null);

    const searchParams = useSearchParams()
    const image_id = searchParams.get('id')

    const fetchAudioElements = async () => {
        if (image_id) {
            try {
                const data = await getAudioForArtwork(parseInt(image_id));
                setAudioElements(data);
            } catch (error) {
                console.error("Error fetching audio elements:", error);
                setError(error as Error);
            }
        }
    };

    useEffect(() => {
        if (image_id) {
            const id = parseInt(image_id);
            Promise.all([getImageForArtwork(id), fetchAudioElements()])
                .then(([imageData]) => {
                    setImageDetails(imageData);
                    setLoading(false);
                })
                .catch(error => {
                    setError(error as Error);
                    setLoading(false);
                });
        }
    }, [image_id]);

    const handleRecordingComplete = async (blob: Blob) => {
        console.log('Recording completed, blob size:', blob.size);
        try {
            const audioBlob = new Blob([blob], { type: 'audio/wav' }); // Create a new Blob with the correct type
            if (image_id) {
                const audioId = await uploadAudio(parseInt(image_id), audioBlob);
                console.log("Uploaded audio ID:", audioId);
                // Refresh the list of audio recordings
                await fetchAudioElements();
            } else {
                console.error("No image ID available");
            }
        } catch (error) {
            console.error("Error uploading audio:", error);
        }
    };

    const playAudio = (audioId: number) => {
        const audioUrl = getAudioUrl(audioId);

        if (playingAudio === audioId) {
            // Pause the currently playing audio
            audioRef.current?.pause();
            setPlayingAudio(null);
        } else {
            // Stop the previously playing audio (if any)
            audioRef.current?.pause();

            // Create and play the new audio
            const newAudio = new Audio(audioUrl);
            newAudio.addEventListener('ended', () => setPlayingAudio(null));
            newAudio.play();

            // Update the audioRef and playingAudio state
            audioRef.current = newAudio;
            setPlayingAudio(audioId);
        }
    };

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error.message}</div>;
    if (!imageDetails) return <div>No artwork found.</div>;

    return (
        <div className="flex flex-col justify-start items-center min-h-screen w-full p-4  max-w-lg mx-auto">
            <div className="w-full mb-4">
                <Link href="/"  >
                    <Button variant="secondary">
                        <Camera className="mr-2 h-4 w-4" />Scan another
                    </Button>
                </Link>
            </div>
            <div className="w-full h-auto">
                {/* <AspectRatio ratio={9 / 9} className="mb-4"> */}
                <img src={imageDetails.url} alt={imageDetails.title} className="w-full max-h-[100vw] rounded-lg object-cover mb-4" />
                {/* </AspectRatio> */}
                <div className="flex flex-row justify-between">
                    <div className="flex-grow">
                        <h2 className="text-xl font-semibold mb-1">
                            {imageDetails.title}
                        </h2>
                        <span className="text-muted-foreground">by {imageDetails.artist}</span>
                    </div>
                    <Button variant="secondary" size="icon">
                        <Info className="w-4 h-4" />
                    </Button>
                </div>
            </div>

            <div className="text-center flex-grow flex flex-col justify-center mt-8 w-full">
                <h2 className="text-xl font-semibold">Audio Recordings</h2>
                {(!audioElements || audioElements.length === 0) ? (
                    <div className="text-center text-muted-foreground test-sm mt-1" >
                        There aren't any audio recordings.
                        <br />
                        But you can be the first! 😉
                    </div>
                ) : (
                    <div className="w-full space-y-4 mt-4">
                        {audioElements.map(audioElement => (
                            <Card key={audioElement.id} className="flex flex-row items-center justify-between w-full mb-4 p-4">
                                <span className="text-center">Audio Recording {audioElement.id}</span>
                                <Button
                                    className="w-12 h-12 sm:w-14 sm:h-14 rounded-full p-0"
                                    size="icon"
                                    onClick={() => playAudio(audioElement.id)}
                                >
                                    {playingAudio === audioElement.id ? (
                                        <Pause className="h-5 w-5 sm:h-6 sm:w-6" />
                                    ) : (
                                        <Play className="h-5 w-5 sm:h-6 sm:w-6" />
                                    )}
                                </Button>
                            </Card>
                        ))}
                    </div>
                )}
            </div>
            <div className="m-4">
                <AudioRecordButton onRecordingComplete={handleRecordingComplete} />
            </div>
        </div>
    )
}