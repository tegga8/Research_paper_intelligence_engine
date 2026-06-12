import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Research Paper Intelligence Engine',
  description: 'AI research intelligence dashboard for ArXiv fields'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
