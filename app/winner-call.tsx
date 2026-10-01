import type {CSSProperties} from 'react';

export function WinnerCall({color}:{color:string}) {
  return <strong className="winner-call" style={{'--winner-party':color} as CSSProperties}>
    <svg className="winner-call-check" viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="square"/></svg>
    <span className="winner-call-copy"><span className="winner-call-kicker">Race called</span><span className="winner-call-label">Elected</span></span>
  </strong>;
}
