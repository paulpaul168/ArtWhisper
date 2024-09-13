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

interface AudioElement {
  id: number;
  filename: string;
  image_id: number;
  user_id: number;
  created_at: string;
}

export default function CameraPage() {

    const [audioElements, setAudioElements] = useState<AudioElement[] | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    const searchParams = useSearchParams()
        fetch(`http://127.0.0.1/image/{image_id}/audios`)
    const image_id = searchParams.get('id')

    useEffect(() => {
        fetch(`http://127.0.0.1:8000/docs/image/${image_id}/audios`)
          .then(response => {
            if (response.status === 404) {
                //throw new Error('Could not find any image with this id');
                return [
                    {
                      "filename": "string",
                      "image_id": 0,
                      "id": 0,
                      "user_id": 0,
                      "created_at": "2024-09-13T19:03:16.686Z"
                    },
                    {
                        "filename": "string",
                        "image_id": 1,
                        "id": 1,
                        "user_id": 1,
                        "created_at": "2024-09-13T19:03:16.686Z"
                      },
                      {
                        "filename": "string",
                        "image_id": 2,
                        "id": 2,
                        "user_id": 2,
                        "created_at": "2024-09-13T19:03:16.686Z"
                      }
                  ]
              }
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
          })
          .then(data => {
            console.log("Audio elements:", data);
            setAudioElements(data);
        })
          .catch(error => setError(error))
          .finally(() => setLoading(false));
      }, []);

      if (loading) return <div>Loading...</div>;
      if (error) return <div>Error: {error.message}</div>;
    
    return (
        <div className="flex flex-col items-center justify-center min-h-screen w-full p-4">
            {audioElements?.map(audioElement => (
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



  
    
