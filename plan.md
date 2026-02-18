# Logo Integration Plan

## Aufgabe
Zwei Logos in die DevFlow App integrieren:
1. **Großes Logo** für die Login-Seite
2. **Kleines horizontales Logo** für die Sidebar

## Ordnerstruktur ✅
```
frontend/
  src/
    assets/
      images/
        logos/
          devflow-logo-large.svg (oder .png)      ← Login-Seite Logo
          devflow-logo-horizontal.svg (oder .png) ← Sidebar Logo
```

## Dateinamen
- **Login Logo:** `devflow-logo-large.svg` (oder `.png`)
  - Empfohlene Größe: 300-500px Breite
  - Wird zentral über dem Login-Formular angezeigt
  
- **Sidebar Logo:** `devflow-logo-horizontal.svg` (oder `.png`)
  - Empfohlene Größe: 150-200px Breite
  - Wird oben links in der Sidebar angezeigt

## Format
- **SVG bevorzugt** (skalierbar, sieht auf allen Bildschirmen scharf aus)
- PNG mit transparentem Hintergrund funktioniert auch

## Nächste Schritte
1. [ ] User legt Logos in `frontend/src/assets/images/logos/` ab
2. [ ] LoginPage updaten (Logo über Formular einfügen)
3. [ ] Sidebar updaten (Logo oben links einfügen)
4. [ ] Responsive Styling (Logo passt sich an verschiedene Bildschirmgrößen an)

## Technische Details
- Vite Asset Handling: `import logo from '@/assets/images/logos/...'`
- Lazy Loading für bessere Performance
- Alt-Text für Accessibility
