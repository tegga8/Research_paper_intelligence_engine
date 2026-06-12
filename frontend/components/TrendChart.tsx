'use client';
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export function TrendChart({ data }: { data: { month: string; papers: number }[] }) {
  return (
    <div className="h-72 rounded-3xl glass p-5">
      <h2 className="mb-4 text-lg font-semibold">Publication momentum</h2>
      <ResponsiveContainer width="100%" height="85%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="papers" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="month" stroke="#94a3b8" />
          <YAxis stroke="#94a3b8" />
          <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,.1)' }} />
          <Area type="monotone" dataKey="papers" stroke="#a78bfa" fill="url(#papers)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
