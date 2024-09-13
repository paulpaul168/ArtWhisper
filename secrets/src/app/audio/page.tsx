'use client'


import { useSearchParams } from 'next/navigation'

export default function CameraPage() {
    const searchParams = useSearchParams()
    const id = searchParams.get('id')
    
    return (
        <div className="flex flex-col items-center justify-center min-h-screen">
            <p>Name: {id}</p>
        </div>
    )
}