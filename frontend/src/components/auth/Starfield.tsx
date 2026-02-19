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
      <div className="absolute inset-0 opacity-60">
        <div className="stars-small" />
      </div>

      {/* Layer 2: Medium stars with rotation - medium speed */}
      <div className="absolute inset-0 opacity-50">
        <div className="stars-medium" />
      </div>

      {/* Layer 3: Large purple stars - slow twinkle */}
      <div className="absolute inset-0 opacity-45">
        <div className="stars-large-purple" />
      </div>

      {/* Layer 4: Rotating purple accents */}
      <div className="absolute inset-0 opacity-35">
        <div className="stars-rotating" />
      </div>
    </div>
  )
}
