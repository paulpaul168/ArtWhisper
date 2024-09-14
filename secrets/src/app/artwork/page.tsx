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
import { Play, Pause, Info, Camera, LogIn, LogOut, Loader2, Earth } from "lucide-react";
import { useSearchParams } from 'next/navigation'
import React, { useState, useEffect, useRef } from 'react';
import { getAudioForArtwork, getImageForArtwork, uploadAudio, getAudioUrl, isLoggedIn } from "../api";
import { AudioRecordButton } from "@/components/audioRecordingButton";
import AudioWaveform from './AudioWaveform';
import { toast } from "react-hot-toast";
import Link from "next/link";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Drawer, DrawerClose, DrawerContent, DrawerDescription, DrawerFooter, DrawerHeader, DrawerTitle, DrawerTrigger } from "@/components/ui/drawer";


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
    description_page: string;
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

    const logout = () => {
        localStorage.removeItem('token');
        window.location.reload();
    };

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
        if (!image_id) {
            toast.error("No image ID available");
            return;
        }

        try {
            const audioBlob = new Blob([blob], { type: 'audio/wav' });
            const audioId = await uploadAudio(parseInt(image_id), audioBlob);
            console.log("Uploaded audio ID:", audioId);
            await fetchAudioElements();
            toast.success("Audio uploaded successfully");
        } catch (error) {
            if (error instanceof Error && error.message.includes("Unauthorized")) {
                toast.error("You are not logged in. Please log in to upload audio.");
            } else {
                toast.error("Failed to upload audio. Please try again.");
            }
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

    if (loading) return (
        <div className="flex justify-center items-center h-screen">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
    );
    if (error) return <div>Error: {error.message}</div>;
    if (!imageDetails) return <div>No artwork found.</div>;

    return (
        <div className="flex flex-col justify-start items-center min-h-screen w-full p-4  max-w-lg mx-auto">
            <div className="flex flex-row justify-between w-full mb-4">
                <Link href="/"  >
                    <Button variant="outline">
                        <Camera className="mr-2 h-4 w-4" />Scan another
                    </Button>
                </Link>
                {!isLoggedIn() ? (
                    <Link href="/auth"  >
                        <Button variant="outline">
                            <LogIn className="mr-2 h-4 w-4" />Log in
                        </Button>
                    </Link>
                ) : (
                    <Button variant="outline" onClick={() => logout()}>
                        <LogOut className="mr-2 h-4 w-4" />Log out
                    </Button>
                )}
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
                    <div className="item-start">
                        <Drawer>
                            <DrawerTrigger asChild>
                                <Button variant="secondary" className="ml-2" size="icon">
                                    <Info className="w-4 h-4" />
                                </Button>
                            </DrawerTrigger>
                            <DrawerContent>
                                <DrawerHeader>
                                    <DrawerTitle>About {imageDetails.title}</DrawerTitle>
                                    <DrawerDescription>{imageDetails.description || "No description available"}</DrawerDescription>
                                </DrawerHeader>
                                <DrawerFooter className="mb-4">
                                    <Button asChild variant="secondary">
                                        <Link href={imageDetails.description_page}>
                                            <Earth className="w-4 h-4 mr-2" />
                                            More on the belvedere page</Link>
                                    </Button>
                                </DrawerFooter>
                            </DrawerContent>
                        </Drawer>
                    </div>
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
                            <Card key={audioElement.id} className="flex flex-col items-center justify-between w-full mb-4 p-4">
                                <div className="flex flex-col items-center justify-center">
                                    <span className="text-center">Audio Recording {audioElement.id}</span>
                                </div>
                                <div className="flex flex-row items-center justify-between mt-4">
                                    <span className="mr-4 max-w-[15em]">
                                        <AudioWaveform audioId={audioElement.id} />
                                    </span>
                                    <Button
                                    className="w-12 h-12 sm:w-14 sm:h-14 rounded-full"
                                    size="icon"
                                    onClick={() => playAudio(audioElement.id)}
                                >
                                    {playingAudio === audioElement.id ? (
                                        <Pause className="h-5 w-5 sm:h-6 sm:w-6" />
                                    ) : (
                                        <Play className="h-5 w-5 sm:h-6 sm:w-6" />
                                    )}
                                </Button>
                                </div>
                            </Card>
                        ))}
                    </div>
                )}
            </div>
            <div className="m-4">
                {isLoggedIn() ? (
                    <AudioRecordButton onRecordingComplete={handleRecordingComplete} />
                ) : (
                    <div className="text-center text-muted-foreground test-sm mt-1" >
                        You are not logged in. Please log in to upload audio.
                    </div>
                )}
            </div>
        </div >
    )
}
