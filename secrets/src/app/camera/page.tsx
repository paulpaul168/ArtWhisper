'use client'

import { useRef, useState } from 'react'
import { Button } from "@/components/ui/button"

export default function CameraPage() {
    const videoRef = useRef<HTMLVideoElement>(null)
    const [stream, setStream] = useState<MediaStream | null>(null)

    const startCamera = async () => {
        try {
            const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true })
            setStream(mediaStream)
            if (videoRef.current) {
                videoRef.current.srcObject = mediaStream
            }
        } catch (error) {
            console.error('Error accessing camera:', error)
        }
    }

    const stopCamera = () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop())
            setStream(null)
        }
    }

    const captureImage = () => {
        if (videoRef.current) {
            const canvas = document.createElement('canvas')
            canvas.width = videoRef.current.videoWidth
            canvas.height = videoRef.current.videoHeight
            canvas.getContext('2d')?.drawImage(videoRef.current, 0, 0)
            const imageDataUrl = canvas.toDataURL('image/jpeg')
            // Here you can send the imageDataUrl to your backend for processing
            console.log('Image captured:', imageDataUrl)
        }
    }

    return (
        <div className="flex flex-col items-center justify-center min-h-screen">
            <div className="mb-4">
                <video ref={videoRef} autoPlay playsInline className="w-[640px] h-[480px] bg-gray-200" />
            </div>
            <div className="space-x-2">
                <Button onClick={startCamera}>Start Camera</Button>
                <Button onClick={stopCamera}>Stop Camera</Button>
                <Button onClick={captureImage}>Capture Image</Button>
            </div>
        </div>
    )
}