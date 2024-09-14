import { Suspense } from 'react';
import dynamic from 'next/dynamic';

const ArtworkContent = dynamic(() => import('./ArtworkContent'), { ssr: false });

export default function ArtworkPage() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <ArtworkContent />
        </Suspense>
    );
}
