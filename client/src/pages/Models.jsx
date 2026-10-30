import { useEffect, useState } from 'react'
import { api } from '../api'
import { AccuracyChart } from '../components/Charts'
import { MODELS } from '../meta'

export default function Models() {
  const [info, setInfo] = useState(null)
  const [err, setErr] = useState('')
  useEffect(() => { api.modelsInfo().then(setInfo).catch((e) => setErr(e.message)) }, [])
  const acc = info ? Object.fromEntries(info.filter((i) => i.status === 'ok').map((i) => [i.model, i.accuracy])) : {}
  return (
    <>
      <header className="page-h"><div><h1>Models</h1><p className="muted">Each model runs as its own microservice. Accuracy is measured on the held-out last 3 months of data.</p></div></header>
      {err && <div className="alert bad">{err}</div>}
      <div className="grid3 models">
        {MODELS.map((m) => {
          const i = info?.find((x) => x.model === m.key)
          return (
            <div key={m.key} className="card mc" style={{ '--accent': m.color }}>
              <div className="mc-head"><span className="dot" style={{ background: m.color }} /><div><b>{m.name}</b><small>{m.blurb}</small></div></div>
              {!info ? <div className="skeleton" style={{ height: 140 }} /> : i.status !== 'ok' ? <div className="alert bad">Service unavailable</div> : (
                <dl className="kv"><dt>Algorithm</dt><dd>{i.algorithm}</dd><dt>Version</dt><dd>{i.version}</dd><dt>Accuracy</dt><dd><b>{i.accuracy}%</b></dd><dt>Macro-F1</dt><dd>{i.macro_f1}</dd><dt>Trained on</dt><dd>{i.trained_on}</dd></dl>
              )}
            </div>
          )
        })}
      </div>
      {info && <AccuracyChart items={acc} title="Accuracy comparison" />}
    </>
  )
}
