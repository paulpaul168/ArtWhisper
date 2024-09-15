"use client";

import React, { useRef, useState, useEffect } from "react";
import { Loader } from "lucide-react";
import { useRouter } from "next/navigation";
import { findSimilarArtwork } from "@/app/api";
import { toast } from "react-hot-toast";

export default function CameraPage() {
  const router = useRouter();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [showLoading, setShowLoading] = useState(false);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);

  const captureImage = async () => {
    if (!videoRef.current) {
      toast.error("Camera not initialized. Please try again.");
      return;
    }

    setShowLoading(true);
    try {
      const canvas = document.createElement("canvas");
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      canvas.getContext("2d")?.drawImage(videoRef.current, 0, 0);

      const capturedImageUrl = canvas.toDataURL("image/jpeg");
      setCapturedImage(capturedImageUrl);

      canvas.toBlob(async (blob) => {
        if (blob) {
          const result = await findSimilarArtwork(blob);
          if (result.similar_artwork_id) {
            router.push(`/artwork?id=${result.similar_artwork_id}`);
          } else {
            toast.error("No matching artwork found");
          }
        } else {
          toast.error("Failed to capture image");
        }
        setTimeout(() => setShowLoading(false), 300);
        setCapturedImage(null);
      }, "image/jpeg");
    } catch (error) {
      toast.error("An error occurred. Please try again.");
      setTimeout(() => setShowLoading(false), 300);
      setCapturedImage(null);
    }
  };

  useEffect(() => {
    const initializeCamera = async () => {
      await startCamera();
    };

    initializeCamera();

    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (error) {
      toast.error(
        "Error accessing camera. Please allow access to camera in your browser settings",
        {
          id: "camera-error",
        },
      );
    }
  };

  return (
    <div
      className="fixed inset-0 w-full h-full overflow-hidden"
      onClick={captureImage}
    >
      {capturedImage ? (
        <img
          src={capturedImage}
          alt="Captured"
          className="absolute top-0 left-0 w-full h-full object-cover"
        />
      ) : (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          className="absolute top-0 left-0 w-full h-full object-cover"
        />
      )}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-64 h-64 relative flex items-center justify-center">
          <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-white rounded-tl-lg"></div>
          <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-white rounded-tr-lg"></div>
          <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-white rounded-bl-lg"></div>
          <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-white rounded-br-lg"></div>
          {showLoading ? (
            <Loader className="h-8 w-8 text-white animate-spin" />
          ) : (
            <p className="text-white text-xl font-semibold opacity-70">
              Click to scan
            </p>
          )}
        </div>
      </div>
      <div className="absolute inset-0 bg-black opacity-0 pointer-events-none" />
    </div>
  );
}
