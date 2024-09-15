import { Suspense } from 'react';
import AuthContent from './AuthContent';

export default function AuthPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <AuthContent />
    </Suspense>
  );
}