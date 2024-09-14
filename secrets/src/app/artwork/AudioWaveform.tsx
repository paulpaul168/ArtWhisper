import React, { useRef, useEffect, useState } from 'react';
import { Play, Pause } from 'lucide-react';
import { getAudio, getAudioUrl } from '../api';

const AudioWaveform = ({ audioId }: { audioId: number }) => {
    const canvasRef = useRef(null);
    const [audioBuffer, setAudioBuffer] = useState<AudioBuffer | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);

    const audioRef = useRef<HTMLAudioElement>(null);



    useEffect(() => {
        const fetchAudio = async () => {
            const response = await getAudio(Number(audioId));
            const blob = await response;
            const arrayBuffer = await blob.arrayBuffer();
            const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
            const buffer = await audioContext.decodeAudioData(arrayBuffer);
            setAudioBuffer(buffer);
        };

        fetchAudio();
    }, [audioId]);

    useEffect(() => {
        if (audioBuffer && canvasRef.current) {
            const canvas = canvasRef.current as HTMLCanvasElement;
            const ctx = canvas.getContext('2d');
            if (!ctx) {
                console.error('Unable to get 2D context');
                return;
            }
            const data = audioBuffer.getChannelData(0);
            const step = Math.ceil(data.length / canvas.width);
            const amp = canvas.height / 2;

            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            ctx.beginPath();
            ctx.moveTo(0, amp);

            for (let i = 0; i < canvas.width - 10; i++) {
                let min = 1.0;
                let max = -1.0;
                for (let j = 0; j < step; j++) {
                    const datum = data[(i * step) + j];
                    if (datum < min) min = datum;
                    if (datum > max) max = datum;
                }
                ctx.lineTo(i, (1 + min) * amp);
                ctx.lineTo(i, (1 + max) * amp);
            }

            ctx.strokeStyle = 'grey';
            ctx.stroke();
        }
    }, [audioBuffer]);

    const togglePlayPause = () => {
        if (audioRef.current) {
            if (audioRef.current.paused) {
                audioRef.current.play();
                setIsPlaying(true);
            } else {
                audioRef.current.pause();
                setIsPlaying(false);
            }
        }
    };

    return (
        <div className="w-full max-w-3xl mx-auto">
            <canvas ref={canvasRef} width="800" height="200" className="w-full h-auto" />
            {/*<div className="mt-4 flex justify-center">
                <button
                    onClick={togglePlayPause}
                    className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                >
                    {isPlaying ? <Pause size={24} /> : <Play size={24} />}
                </button>
            </div>*/}
            <audio ref={audioRef} src={getAudioUrl(audioId)} />
        </div>
    );
};

export default AudioWaveform;