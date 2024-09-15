import React, { useRef, useEffect, useState } from "react";
import { getAudio, getAudioUrl } from "../api";
import { Button } from "@/components/ui/button";
import { Play, Pause } from "lucide-react";
import { useTheme } from "next-themes";

const AudioWaveform = ({ audioId }: { audioId: number }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [audioBuffer, setAudioBuffer] = useState<AudioBuffer | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const animationRef = useRef<number>();
  const { theme, systemTheme } = useTheme();


  useEffect(() => {
    const fetchAudio = async () => {
      const response = await getAudio(Number(audioId));
      const blob = await response;
      const arrayBuffer = await blob.arrayBuffer();
      const audioContext = new (window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext })
          .webkitAudioContext)();
      const buffer = await audioContext.decodeAudioData(arrayBuffer);
      setAudioBuffer(buffer);
      setDuration(buffer.duration);
    };

    fetchAudio();
  }, [audioId]);

  useEffect(() => {
    if (audioBuffer && canvasRef.current) {
      drawWaveform();
    }
  }, [audioBuffer]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => {
      setCurrentTime(audio.currentTime);
      if (audio.currentTime >= audio.duration) {
        setIsPlaying(false);
        setCurrentTime(audio.duration); // Set to exact duration
        cancelAnimationFrame(animationRef.current!);
      } else {
        animationRef.current = requestAnimationFrame(updateTime);
      }
    };

    if (isPlaying) {
      audio.play();
      animationRef.current = requestAnimationFrame(updateTime);
    } else {
      audio.pause();
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPlaying]);

  const togglePlayPause = () => {
    if (currentTime >= duration) {
      setCurrentTime(0);
      if (audioRef.current) {
        audioRef.current.currentTime = 0;
      }
    }
    setIsPlaying(!isPlaying);
  };

  const drawWaveform = () => {
    if (!audioBuffer || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      console.error("Unable to get 2D context");
      return;
    }

    const data = audioBuffer.getChannelData(0);
    const step = Math.ceil(data.length / canvas.width);
    const amp = canvas.height / 2;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Determine the current effective theme
    const effectiveTheme = theme === 'system' ? systemTheme : theme;

    // Draw background waveform
    ctx.beginPath();
    ctx.moveTo(0, amp);

    for (let i = 0; i < canvas.width; i++) {
      let min = 1.0;
      let max = -1.0;
      for (let j = 0; j < step; j++) {
        const datum = data[i * step + j];
        if (datum < min) min = datum;
        if (datum > max) max = datum;
      }
      ctx.lineTo(i, (1 + min) * amp);
      ctx.lineTo(i, (1 + max) * amp);
    }

    ctx.strokeStyle = effectiveTheme === 'dark' ? "rgba(128, 128, 128, 0.5)" : "rgba(200, 200, 200, 0.5)";
    ctx.stroke();

    // Draw progress
    const progress = Math.min(currentTime / duration, 1); // Ensure progress doesn't exceed 1
    const progressWidth = Math.floor(canvas.width * progress);

    ctx.beginPath();
    ctx.moveTo(0, amp);

    for (let i = 0; i < progressWidth; i++) {
      let min = 1.0;
      let max = -1.0;
      for (let j = 0; j < step; j++) {
        const datum = data[i * step + j];
        if (datum < min) min = datum;
        if (datum > max) max = datum;
      }
      ctx.lineTo(i, (1 + min) * amp);
      ctx.lineTo(i, (1 + max) * amp);
    }

    ctx.strokeStyle = effectiveTheme === 'dark' ? "white" : "black";
    ctx.stroke();
  };

  useEffect(() => {
    drawWaveform();
  }, [currentTime, audioBuffer, theme]);

  return (
    <div className="w-full flex items-center justify-between">
      <canvas
        ref={canvasRef}
        width="600"
        height="100"
        className="w-full h-auto"
      />
      <Button
        className="w-12 h-12 sm:w-14 sm:h-14 rounded-full flex-shrink-0 ml-2"
        size="icon"
        onClick={togglePlayPause}
        disabled={currentTime >= duration && !isPlaying}
      >
        {isPlaying ? (
          <Pause className="h-5 w-5 sm:h-6 sm:w-6" />
        ) : (
          <Play className="h-5 w-5 sm:h-6 sm:w-6" />
        )}
      </Button>
      <audio ref={audioRef} src={getAudioUrl(audioId)} />
    </div>
  );
};

export default AudioWaveform;