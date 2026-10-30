import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { MODELS } from '../meta'

const tip = { background: 'var(--panel-solid)', border: '1px solid var(--line)', borderRadius: 10, color: 'var(--text)', fontSize: 12 }

export function ProbChart({ results }) {
  const data = ['Low', 'Medium', 'High'].map((c) => {
    const row = { cat: c }
    MODELS.forEach((m) => { const r = results[m.key]; if (r?.status === 'ok') row[m.short] = +(r.probabilities[c.toLowerCase()] * 100).toFixed(1) })
    return row
  })
  return (
    <div className="card chart"><h3>Probability by class</h3>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} barGap={4}>
          <CartesianGrid stroke="var(--line)" vertical={false} />
          <XAxis dataKey="cat" stroke="var(--muted)" tickLine={false} axisLine={false} />
          <YAxis stroke="var(--muted)" unit="%" tickLine={false} axisLine={false} domain={[0, 100]} width={44} />
          <Tooltip contentStyle={tip} cursor={{ fill: 'var(--hover)' }} formatter={(v) => `${v}%`} />
          <Legend />
          {MODELS.map((m) => <Bar key={m.key} dataKey={m.short} fill={m.color} radius={[6, 6, 0, 0]} />)}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function AccuracyChart({ items, title = 'Test accuracy by model' }) {
  const data = MODELS.map((m) => ({ name: m.short, acc: items[m.key] ?? null, color: m.color })).filter((d) => d.acc !== null)
  return (
    <div className="card chart"><h3>{title}</h3>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data}>
          <CartesianGrid stroke="var(--line)" vertical={false} />
          <XAxis dataKey="name" stroke="var(--muted)" tickLine={false} axisLine={false} />
          <YAxis stroke="var(--muted)" unit="%" tickLine={false} axisLine={false} domain={[0, 100]} width={44} />
          <Tooltip contentStyle={tip} cursor={{ fill: 'var(--hover)' }} formatter={(v) => `${v}%`} />
          <Bar dataKey="acc" name="Accuracy" radius={[8, 8, 0, 0]} label={{ position: 'top', fill: 'var(--text)', fontSize: 12, formatter: (v) => `${v}%` }}
            shape={(p) => <rect x={p.x} y={p.y} width={p.width} height={p.height} rx="8" fill={p.payload.color} />} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
