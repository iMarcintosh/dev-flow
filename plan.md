# Per-User API Key Management

## Ziel
Jeder User kann seine eigenen API-Keys für Anthropic, OpenAI und OpenRouter in den Settings hinterlegen. Keys werden verschlüsselt gespeichert und haben Fallback zu globalen .env Keys.

## UX-Änderung: Settings Navigation
**ÄNDERUNG:** Settings-Menüpunkt aus Sidebar entfernen!
- ❌ Aktuell: Settings als separater Nav-Punkt (wie Board, Agent Hub)
- ✅ Neu: Klick auf User-Bereich (unten in Sidebar) öffnet Dropdown
  - Dropdown: "⚙️ Settings" (+ später Profile, Billing, etc.)
  - Logout-Button bleibt separat unter dem User-Bereich

**Navigation nach Änderung:**
```
Sidebar:
├── Board        (nav item)
├── Agent Hub    (nav item)
└── User Profile (klickbar → dropdown)
    ├── [Dropdown: Settings, ...]
    └── Logout Button (separat, darunter)
```

**Implementation:**
- useState für Dropdown open/closed
- Click outside zum Schließen
- Settings-Icon (⚙️) im Dropdown
- Später erweiterbar: Profile, Billing, Team Settings, etc.

## Anforderungen
✅ **Entscheidungen vom User:**
- Fallback zu .env Keys wenn User keinen eigenen Key hat
- Verschlüsselte Speicherung in der Datenbank
- Test-Funktion um Keys zu validieren

## Architektur-Überblick

### User Flow
1. User klickt auf seinen Namen/Avatar unten in der Sidebar
2. Popup/Dropdown erscheint mit: "Settings" & "Logout"
3. Klick auf "Settings" → Navigiert zu /settings
4. In Settings: API Keys Tab
5. Sieht Status: "Using global key" oder "Using personal key"
6. Gibt eigenen API Key ein für gewünschten Provider
7. Klickt "Test Key" → System testet ob Key funktioniert
8. Speichert Key → Wird verschlüsselt in DB gespeichert
9. Ab jetzt nutzen alle Agents des Users seinen persönlichen Key

### Fallback-Hierarchie
```
1. User's encrypted API key (priority)
   ↓ (if not set)
2. Global .env API key (fallback)
   ↓ (if not set)
3. Error: No API key available
```

## Implementation Plan

### Phase 0: UX Refactoring (Quick Win)
- [ ] **0.1: Sidebar Navigation Update**
  - Entferne Settings aus `navigation` Array in Sidebar.tsx
  - Mache User-Bereich klickbar (Link to /settings)
  - Optional: Dropdown Menu mit "Settings" & "Logout"
  - Teste Navigation funktioniert

### Phase 1: Database & Security (Backend)
- [ ] **1.1: Encryption Service** (`backend/app/security/encryption.py`)
  - Erstelle `encrypt_api_key()` Funktion (Fernet encryption)
  - Erstelle `decrypt_api_key()` Funktion
  - Generiere ENCRYPTION_KEY aus SECRET_KEY (deterministisch)
  - Teste mit Unit-Tests

- [ ] **1.2: Database Migration**
  - Migration: `add_encrypted_api_keys_to_users`
  - Füge Columns hinzu:
    - `encrypted_anthropic_key: String (nullable)`
    - `encrypted_openai_key: String (nullable)`
    - `encrypted_openrouter_key: String (nullable)`
  - Keine Backfill nötig (alle NULL initially)

- [ ] **1.3: User Model Update**
  - Füge Columns zu `User` model hinzu
  - Erstelle Properties für lazy decryption:
    - `anthropic_api_key` property (decrypts on access)
    - `openai_api_key` property (decrypts on access)
    - `openrouter_api_key` property (decrypts on access)

### Phase 2: API Key Service (Backend)
- [ ] **2.1: API Key Service** (`backend/app/services/api_key_service.py`)
  - `get_api_key(user_id, provider)` → Returns user key or falls back to .env
  - `set_api_key(user_id, provider, plain_key)` → Encrypts and saves
  - `delete_api_key(user_id, provider)` → Removes user's key
  - `test_api_key(provider, plain_key)` → Tests if key works
  
- [ ] **2.2: Test Endpoints** (`backend/app/api/routes/api_keys.py`)
  - `POST /api/api-keys/test` → Test a key without saving
    - Body: `{provider: "anthropic", api_key: "sk-..."}`
    - Returns: `{valid: true/false, error: "..."}`
  - `GET /api/api-keys/status` → Get status for all providers
    - Returns: `{anthropic: "personal"/"global"/"none", ...}`
  
- [ ] **2.3: CRUD Endpoints** (`backend/app/api/routes/api_keys.py`)
  - `GET /api/api-keys` → Get masked keys (show only last 4 chars)
  - `PUT /api/api-keys/{provider}` → Save encrypted key
  - `DELETE /api/api-keys/{provider}` → Remove user's key

### Phase 3: Agent Integration (Backend)
- [ ] **3.1: Update model_resolver.py**
  - Ändere `create_llm(model_name, user_id)` Signatur
  - Nutze `api_key_service.get_api_key(user_id, provider)`
  - Fallback zu `settings.{provider}_api_key` wenn User-Key nicht existiert
  
- [ ] **3.2: Update task_creator.py**
  - Übergebe `user_id` an `create_llm()`
  - Teste mit User-spezifischen Keys

- [ ] **3.3: Update chat_agent.py**
  - Übergebe `user_id` an `create_llm()`
  - Teste mit User-spezifischen Keys

### Phase 4: Frontend UI (Frontend)
- [ ] **4.1: API Keys Tab in Settings**
  - Erstelle `APIKeysSection.tsx` Component
  - Drei Sections: Anthropic, OpenAI, OpenRouter
  - Jede Section zeigt:
    - Status Badge ("Personal Key" / "Global Fallback" / "Not Configured")
    - Masked Key anzeigen (z.B. "sk-ant-...xyz123")
    - Input Field (type="password") für neuen Key
    - "Test" Button (prüft Key ohne zu speichern)
    - "Save" Button (verschlüsselt und speichert)
    - "Delete" Button (entfernt User-Key, fällt auf Global zurück)

- [ ] **4.2: API Queries** (`frontend/src/services/queries.ts`)
  - `useApiKeyStatus()` → Holt Status für alle Provider
  - `useTestApiKey()` → Mutation zum Testen eines Keys
  - `useUpdateApiKey()` → Mutation zum Speichern
  - `useDeleteApiKey()` → Mutation zum Löschen

- [ ] **4.3: UI/UX Polish**
  - Success/Error Toasts für Test/Save/Delete
  - Loading States während Test/Save
  - Validation: API Key Format prüfen (z.B. `sk-ant-` für Anthropic)
  - Confirm Dialog beim Löschen
  - Show/Hide Toggle für Password Fields

### Phase 5: Testing & Documentation
- [ ] **5.1: Backend Tests**
  - Unit Tests für encryption/decryption
  - Integration Tests für API Key endpoints
  - Test Fallback-Logik (User-Key → Global-Key → Error)

- [ ] **5.2: Frontend Tests**
  - Test APIKeysSection Component
  - Test Key Masking (nur letzten 4 Zeichen sichtbar)

- [ ] **5.3: Documentation**
  - Update TESTING-GUIDE.md mit API Key Setup
  - Update README.md mit Security-Hinweisen
  - Dokumentiere Encryption Approach

## Security Considerations

### Encryption
```python
from cryptography.fernet import Fernet
import base64
import hashlib

# Generate deterministic key from SECRET_KEY
def get_encryption_key(secret: str) -> bytes:
    return base64.urlsafe_b64encode(
        hashlib.sha256(secret.encode()).digest()
    )

# Encrypt
fernet = Fernet(encryption_key)
encrypted = fernet.encrypt(plain_key.encode())

# Decrypt
decrypted = fernet.decrypt(encrypted).decode()
```

### Database Schema
```sql
ALTER TABLE users ADD COLUMN encrypted_anthropic_key VARCHAR(512);
ALTER TABLE users ADD COLUMN encrypted_openai_key VARCHAR(512);
ALTER TABLE users ADD COLUMN encrypted_openrouter_key VARCHAR(512);
```

### API Key Masking (Frontend)
```typescript
function maskApiKey(key: string): string {
  if (!key) return "Not set";
  if (key.length < 8) return "****";
  return `${key.slice(0, 7)}...${key.slice(-4)}`;
}
// "sk-ant-api03_abc123xyz789" → "sk-ant-...z789"
```

## UI Mockup: Sidebar User Menu
```
┌──────────────────────────┐
│ Board                    │
│ Agent Hub                │
├──────────────────────────┤
│                          │
│ [D] demo@devflow.dev     │ ← Klickbar!
│     demo                 │
│                          │
│  On Click: Dropdown      │
│  ┌────────────────────┐  │
│  │ ⚙️  Settings       │  │
│  └────────────────────┘  │
│                          │
│  🚪 Logout (Button)      │ ← Separat, darunter
└──────────────────────────┘
```

## UI Mockup: Settings API Keys Tab
```
┌─────────────────────────────────────────┐
│ API Keys                                │
├─────────────────────────────────────────┤
│                                         │
│ 🔑 Anthropic (Claude)                  │
│ Status: ✅ Using personal key           │
│ Current: sk-ant-...xyz123               │
│                                         │
│ New API Key:                            │
│ [••••••••••••••••••••] 👁️             │
│ [Test]  [Save]  [Delete]                │
│                                         │
├─────────────────────────────────────────┤
│ 🔑 OpenAI (GPT)                        │
│ Status: 🌐 Using global fallback        │
│ Current: sk-...abc456 (global)          │
│                                         │
│ New API Key:                            │
│ [                      ] 👁️            │
│ [Test]  [Save]                          │
│                                         │
├─────────────────────────────────────────┤
│ 🔑 OpenRouter                          │
│ Status: ❌ Not configured               │
│                                         │
│ New API Key:                            │
│ [                      ] 👁️            │
│ [Test]  [Save]                          │
└─────────────────────────────────────────┘
```

## Database Structure (After Migration)
```
users
├── id (UUID)
├── email
├── preferred_models (JSON)
├── encrypted_anthropic_key (VARCHAR, nullable) ⬅️ NEW
├── encrypted_openai_key (VARCHAR, nullable)    ⬅️ NEW
├── encrypted_openrouter_key (VARCHAR, nullable) ⬅️ NEW
└── ...
```

## Next Steps
1. ✅ Review Plan mit User
2. Phase 0: Sidebar UX Refactoring (Quick Win, kann sofort gemacht werden)
3. Phase 1: Database & Security
4. Schrittweise weitere Phasen implementieren
5. Zwischen Phasen committen

## Offene Fragen
- ✅ Dropdown Menu für User-Bereich (Settings + später mehr)
- ✅ Logout bleibt separater Button
- ❓ Sollen auch alte Keys rotiert werden können? (Nice-to-have)
- ❓ Key-History/Audit-Log? (Security-Feature, optional)
- ❓ Rate-Limiting für Key-Tests? (Prevent API abuse)
