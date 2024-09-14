'use client'

import React, { useRef, useState, useEffect } from 'react';
import { Camera } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';
import { getArtworkEmbeddings, findSimilarArtwork } from '@/app/api';
import { toast } from 'react-hot-toast';

export default function CameraPage() {
    const router = useRouter()
    const videoRef = useRef<HTMLVideoElement>(null);
    const [stream, setStream] = useState<MediaStream | null>(null);

    useEffect(() => {
        const initializeCamera = async () => {
            await startCamera();
        };

        initializeCamera();

        return () => {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    const startCamera = async () => {
        try {
            const mediaStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
            setStream(mediaStream);
            if (videoRef.current) {
                videoRef.current.srcObject = mediaStream;
            }
        } catch (error) {
            toast.error('Error accessing camera. Please allow access to camera in your browser settings');
        }
    };

    const captureImage = async () => {
        if (!videoRef.current) {
            toast.error('Camera not initialized. Please try again.');
            return;
        }

        try {
            const canvas = document.createElement('canvas');
            canvas.width = videoRef.current.videoWidth;
            canvas.height = videoRef.current.videoHeight;
            canvas.getContext('2d')?.drawImage(videoRef.current, 0, 0);

            canvas.toBlob(async (blob) => {
                if (blob) {
                    const result = await findSimilarArtwork(blob);
                    if (result.similar_artwork_id) {
                        router.push(`/artwork?id=${result.similar_artwork_id}`);
                    } else {
                        toast.error('No matching artwork found');
                    }
                } else {
                    toast.error('Failed to capture image');
                }
            }, 'image/jpeg');
        } catch (error) {
            console.error('Error capturing or processing image:', error);
            toast.error('An error occurred. Please try again.');
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