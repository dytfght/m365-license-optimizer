# Frontend - M365 License Optimizer

## 📋 Vue d'ensemble

Frontend React/Next.js pour l'application M365 License Optimizer. Interface utilisateur moderne et responsive pour la gestion des licences Microsoft 365.

## 🚀 Technologies

- **Framework**: Next.js 14 (Pages Router)
- **Langage**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Query (TanStack Query) + Context API
- **Internationalisation**: react-i18next (FR/EN)
- **Composants**: Lucide React icons
- **Tests**: Jest + React Testing Library

## 📁 Structure du projet

```
frontend/
├── src/
│   ├── components/      # Composants UI réutilisables
│   │   ├── ErrorMessage.tsx
│   │   ├── LoadingSpinner.tsx
│   │   ├── LoginForm.tsx
│   │   └── Navbar.tsx
│   ├── context/         # React Context (Auth)
│   │   └── AuthContext.tsx
│   ├── pages/          # Routes Next.js
│   │   ├── _app.tsx    # Configuration globale
│   │   ├── _document.tsx # Structure HTML
│   │   ├── index.tsx   # Redirection vers /login
│   │   ├── login.tsx   # Page de connexion
│   │   ├── dashboard.tsx # Liste des tenants
│   │   ├── tenants/[id].tsx # Détails tenant & sync
│   │   ├── analyses/[tenantId].tsx # Analyses
│   │   ├── reports/[analysisId].tsx # Rapports
│   │   └── admin/sku-mapping.tsx # Admin SKU
│   ├── services/       # Intégration API
│   │   ├── api.ts      # Client Axios + intercepteurs
│   │   ├── authService.ts
│   │   ├── tenantService.ts
│   │   ├── analysisService.ts
│   │   ├── reportService.ts
│   │   └── skuMappingService.ts
│   ├── types/          # Types TypeScript
│   │   └── index.ts
│   ├── styles/         # Styles globaux
│   │   └── globals.css
│   └── i18n.ts         # Configuration i18n
├── public/             # Assets statiques
├── tests/              # Tests unitaires
├── Dockerfile          # Build Docker
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── next.config.js
```

## 🛠️ Installation locale

### Prérequis
- Node.js 18+
- npm

### Étapes

```bash
# 1. Aller dans le dossier frontend
cd frontend

# 2. Installer les dépendances
npm install

# 3. Créer le fichier .env.local
cp .env.local.example .env.local
# Éditer .env.local si nécessaire

# 4. Démarrer en mode développement
npm run dev
```

Le frontend sera accessible sur **http://localhost:3000**

## 🐳 Utilisation avec Docker

```bash
# Depuis la racine du projet
docker-compose up frontend
```

Le frontend utilise automatiquement l'URL du backend configurée dans `docker-compose.yml`.

## 🔧 Scripts disponibles

```bash
# Développement
npm run dev         # Démarre le serveur de développement

# Build
npm run build       # Compile pour la production
npm run start       # Démarre le serveur de production

# Qualité de code
npm run lint        # ESLint
npm run type-check  # Vérification TypeScript

# Tests
npm test            # Exécute les tests Jest
```

## 🌐 Variables d'environnement

### .env.local (développement local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Docker (docker-compose.yml)
```env
NEXT_PUBLIC_API_URL=http://backend:8000/api/v1
```

## 📄 Pages principales

### Authentification
- **`/login`**: Page de connexion avec JWT

### Dashboard
- **`/dashboard`**: Liste des tenants avec actions rapides

### Gestion des tenants
- **`/tenants/[id]`**: 
  - Sync Users (Microsoft Graph)
  - Sync Licenses
  - Sync Usage (28 jours)

### Analyses
- **`/analyses/[tenantId]`**:
  - Lancer une nouvelle analyse
  - Historique des analyses
  - Statut (pending, in_progress, completed, failed)

### Rapports
- **`/reports/[analysisId]`**:
  - Générer PDF
  - Générer Excel
  - Télécharger rapports existants

### Administration
- **`/admin/sku-mapping`**:
  - Statistiques SKU mapping
  - Sync products Partner Center
  - Sync compatibility rules

## 🎨 Design System

### Couleurs Tailwind personnalisées

```javascript
colors: {
  primary: '#0066CC'  // Microsoft Blue
  secondary: '#6B7280'  // Gray
}
```

Utilisation dans les composants:
- `bg-primary`, `text-primary`, `hover:bg-blue-600`
- `border-primary`, `ring-primary`

## 🔒 Sécurité

### JWT Authentication
- Token stocké dans `localStorage`
- Injection automatique via intercepteur Axios
- Redirection automatique sur 401

### Protected Routes
- `AuthProvider` vérifie l'authentification
- Routes protégées redirigent vers `/login`

## 🌍 Internationalisation

Support FR/EN avec `react-i18next`:

```typescript
const { t } = useTranslation();
<h1>{t('Dashboard')}</h1>  // FR: "Tableau de bord" / EN: "Dashboard"
```

Changement de langue via le bouton Globe dans la Navbar.

## 🧪 Tests

```bash
# Tests unitaires
npm test

# Coverage
npm test -- --coverage
```

Fichiers de tests dans `tests/`:
- `LoginForm.test.tsx`
- `Navbar.test.tsx`
- `authService.test.ts`
- `tenantService.test.ts`

## 🚚 Déploiement

### Build Docker

```bash
# Avec build args
docker build \\
  --build-arg NEXT_PUBLIC_API_URL=http://backend:8000/api/v1 \\
  -t m365-frontend .

# Exécuter
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://backend:8000/api/v1 m365-frontend
```

### Production

```bash
npm run build
npm run start
```

## 🔄 Intégration API

Tous les services utilisent l'instance Axios centralisée (`api.ts`) avec:
- Configuration base URL via `NEXT_PUBLIC_API_URL`
- Intercepteur request: injection JWT
- Intercepteur response: gestion 401 (logout automatique)

### Exemple d'appel API

```typescript
import { tenantService } from '@/services/tenantService';
import { useQuery } from '@tanstack/react-query';

const { data: tenants } = useQuery({
  queryKey: ['tenants'],
  queryFn: tenantService.getAll
});
```

## 📝 Conventions de code

- **TypeScript strict**: Tous les fichiers en `.ts` ou `.tsx`
- **Composants fonctionnels**: Avec React Hooks
- **React Query**: Pour tout le server state
- **Tailwind CSS**: Pour tous les styles (pas de CSS modules)
- **i18n**: Toutes les chaînes UI doivent être traduites

## 🆘 Troubleshooting

### Erreur de compilation
```bash
# Supprimer .next et node_modules
rm -rf .next node_modules
npm install
npm run dev
```

### Erreur 404
Vérifier que:
- Le fichier existe dans `/pages/`
- Le nom du fichier est correct (routes dynamiques: `[id].tsx`)
- Le build Next.js est à jour

### Erreur d'API
Vérifier:
- `NEXT_PUBLIC_API_URL` est correctement définie
- Le backend est accessible
- Le token JWT est valide

## 📚 Documentation complémentaire

- [Next.js Documentation](https://nextjs.org/docs)
- [React Query](https://tanstack.com/query/latest)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [react-i18next](https://react.i18next.com/)
