/**
 * Starfield Background Component
 * 
 * Enhanced animated starfield with purple-tinted stars and subtle rotation.
 * Shows subtle twinkling and rotating stars in the background of auth pages.
 */

export function Starfield() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none">
      {/* Layer 1: Small white stars - slow twinkle */}
      <div className="absolute inset-0 opacity-40">
        <div className="stars-small" />
      </div>
      
      {/* Layer 2: Medium stars with rotation - medium speed */}
      <div className="absolute inset-0 opacity-30">
        <div className="stars-medium" />
      </div>
      
      {/* Layer 3: Large purple stars - slow twinkle */}
      <div className="absolute inset-0 opacity-25">
        <div className="stars-large-purple" />
      </div>

      {/* Layer 4: Rotating purple accents */}
      <div className="absolute inset-0 opacity-20">
        <div className="stars-rotating" />
      </div>
    </div>
  )
}
