import { Suspense } from "react";
import dynamic from "next/dynamic";

const AudioContent = dynamic(() => import("./AudioContent"), { ssr: false });

export default function AudioPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <AudioContent />
    </Suspense>
  );
}
