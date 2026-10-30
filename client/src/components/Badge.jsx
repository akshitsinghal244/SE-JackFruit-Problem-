import { CAT_CLASS } from '../meta'
export default function Badge({ cat, big }) {
  if (!cat) return <span className="badge none">-</span>
  const c = CAT_CLASS[cat] || 'none'
  return <span className={`badge ${c}${big ? ' big' : ''}`}><i />{cat}</span>
}
