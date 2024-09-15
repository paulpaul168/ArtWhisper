import React, { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Mic, Square } from "lucide-react";
import { toast } from "react-hot-toast";

interface AudioRecordButtonProps {
  onRecordingComplete: (blob: Blob) => void;
}

export function AudioRecordButton({
  onRecordingComplete,
}: AudioRecordButtonProps) {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        onRecordingComplete(blob);
        chunksRef.current = [];
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
      toast.error(
        "Error accessing microphone, please allow access to microphone in your browser settings",
      );
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <Button
      onClick={toggleRecording}
      variant={isRecording ? "destructive" : "default"}
      className="w-16 h-16 rounded-full p-0"
    >
      {isRecording ? (
        <Square className="h-6 w-6" />
      ) : (
        <Mic className="h-6 w-6" />
      )}
    </Button>
  );
}
