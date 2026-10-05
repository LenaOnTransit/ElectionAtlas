import type {CSSProperties} from 'react';

export function calledRowStyle(color:string):CSSProperties {return {'--winner-party':color,backgroundColor:color+'14',borderLeft:'5px solid '+color} as CSSProperties;}

export function WinnerCall({color,label="Elected",kicker="Race called"}:{color:string;label?:string;kicker?:string}) {
  return <strong className="winner-call" style={{'--winner-party':color} as CSSProperties}>
    <svg className="winner-call-check" viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="square"/></svg>
    <span className="winner-call-copy"><span className="winner-call-kicker">{kicker}</span><span className="winner-call-label">{label}</span></span>
  </strong>;
}
