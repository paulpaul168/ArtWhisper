'use client'

import React, { useRef, useState, useEffect } from 'react';
import { Camera } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';

export default function CameraPage() {

    const router = useRouter()
    const videoRef = useRef<HTMLVideoElement>(null);
    const [stream, setStream] = useState<MediaStream | null>(null);

    useEffect(() => {
        startCamera();
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
            console.error('Error accessing camera:', error);
        }
    };

    const findImageinDatabase = (imageDataUrl: string) => {
        return 9
    }

    const captureImage = () => {
        if (videoRef.current) {
            const canvas = document.createElement('canvas');
            canvas.width = videoRef.current.videoWidth;
            canvas.height = videoRef.current.videoHeight;
            canvas.getContext('2d')?.drawImage(videoRef.current, 0, 0);
            const imageDataUrl = canvas.toDataURL('image/jpeg');
            console.log('Image captured:', imageDataUrl);

            const id = findImageinDatabase(imageDataUrl)
            router.push(`/artwork?id=${id}`)
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