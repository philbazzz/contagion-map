type P = { size?: number; className?: string };

const base = (size = 16) => ({
  width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor",
  strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, "aria-hidden": true,
});

export const IconPlay = ({ size, className }: P) => (<svg {...base(size)} className={className}><path d="M7 4.5v15l12-7.5z" fill="currentColor" stroke="none" /></svg>);
export const IconPause = ({ size, className }: P) => (<svg {...base(size)} className={className}><rect x="6" y="4.5" width="4" height="15" rx="1" fill="currentColor" stroke="none" /><rect x="14" y="4.5" width="4" height="15" rx="1" fill="currentColor" stroke="none" /></svg>);
export const IconPrev = ({ size, className }: P) => (<svg {...base(size)} className={className}><path d="M18 5 9 12l9 7" /><path d="M6 5v14" /></svg>);
export const IconNext = ({ size, className }: P) => (<svg {...base(size)} className={className}><path d="m6 5 9 7-9 7" /><path d="M18 5v14" /></svg>);
export const IconReset = ({ size, className }: P) => (<svg {...base(size)} className={className}><path d="M3 12a9 9 0 1 0 3-6.7" /><path d="M3 4v5h5" /></svg>);
export const IconSearch = ({ size, className }: P) => (<svg {...base(size)} className={className}><circle cx="11" cy="11" r="6.5" /><path d="m20 20-4.2-4.2" /></svg>);
export const IconZap = ({ size, className }: P) => (<svg {...base(size)} className={className}><path d="M13 2 4 14h7l-1 8 9-12h-7z" /></svg>);
export const IconAlert = ({ size, className }: P) => (<svg {...base(size)} className={className}><path d="M12 3 2 20h20z" /><path d="M12 10v4.5" /><circle cx="12" cy="17.3" r=".6" fill="currentColor" /></svg>);
export const IconClose = ({ size, className }: P) => (<svg {...base(size)} className={className}><path d="M6 6l12 12M18 6 6 18" /></svg>);
export const IconLink = ({ size, className }: P) => (<svg {...base(size)} className={className}><path d="M14 4h6v6" /><path d="M20 4 11 13" /><path d="M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5" /></svg>);
export const IconTarget = ({ size, className }: P) => (<svg {...base(size)} className={className}><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="3" /><path d="M12 1v3M12 20v3M1 12h3M20 12h3" /></svg>);
export const IconOrbit = ({ size, className }: P) => (<svg {...base(size)} className={className}><circle cx="12" cy="12" r="2.5" /><ellipse cx="12" cy="12" rx="10" ry="4.5" transform="rotate(-25 12 12)" /></svg>);
export const IconLayers = ({ size, className }: P) => (<svg {...base(size)} className={className}><path d="m12 3 9 5-9 5-9-5z" /><path d="m3 13 9 5 9-5" /></svg>);
export const IconInfo = ({ size, className }: P) => (<svg {...base(size)} className={className}><circle cx="12" cy="12" r="9" /><path d="M12 11v6" /><circle cx="12" cy="7.5" r=".7" fill="currentColor" /></svg>);
export const IconRoute = ({ size, className }: P) => (<svg {...base(size)} className={className}><circle cx="5" cy="18" r="2" /><circle cx="19" cy="6" r="2" /><path d="M7 18h7a3 3 0 0 0 0-6h-4a3 3 0 0 1 0-6h7" /></svg>);
export const IconKey = ({ size, className }: P) => (<svg {...base(size)} className={className}><path d="M4 6h16M4 12h10M4 18h6" /></svg>);
export const IconPanel = ({ size, className }: P) => (<svg {...base(size)} className={className}><rect x="3" y="4" width="18" height="16" rx="1" /><path d="M15 4v16" /></svg>);
export const IconChevron = ({ size, className }: P) => (<svg {...base(size)} className={className}><path d="m9 6 6 6-6 6" /></svg>);
