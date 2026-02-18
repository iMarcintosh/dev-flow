/**
 * Starfield Background Component
 * 
 * Minimal animated starfield effect using pure CSS.
 * Shows subtle twinkling stars in the background of auth pages.
 */

export function Starfield() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none">
      {/* Layer 1: Small stars - slow */}
      <div className="absolute inset-0 opacity-40">
        <div className="stars-small" />
      </div>
      
      {/* Layer 2: Medium stars - medium speed */}
      <div className="absolute inset-0 opacity-30">
        <div className="stars-medium" />
      </div>
      
      {/* Layer 3: Large stars - fast */}
      <div className="absolute inset-0 opacity-20">
        <div className="stars-large" />
      </div>
    </div>
  )
}
