import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

i18n
    .use(initReactI18next)
    .init({
        resources: {
            en: {
                translation: {
                    "Login": "Login",
                    "Username": "Username",
                    "Password": "Password",
                    "Sign In": "Sign In",
                    "Dashboard": "Dashboard",
                    "Tenants": "Tenants",
                    "Analyses": "Analyses",
                    "Reports": "Reports",
                    "Admin": "Admin",
                    "Logout": "Logout",
                    "Loading": "Loading...",
                    "Error": "Error",
                    "Sync Users": "Sync Users",
                    "Sync Licenses": "Sync Licenses",
                    "Sync Usage": "Sync Usage",
                    "Run Analysis": "Run Analysis",
                    "Download Report": "Download Report"
                }
            },
            fr: {
                translation: {
                    "Login": "Connexion",
                    "Username": "Nom d'utilisateur",
                    "Password": "Mot de passe",
                    "Sign In": "Se connecter",
                    "Dashboard": "Tableau de bord",
                    "Tenants": "Tenants",
                    "Analyses": "Analyses",
                    "Reports": "Rapports",
                    "Admin": "Admin",
                    "Logout": "Déconnexion",
                    "Loading": "Chargement...",
                    "Error": "Erreur",
                    "Sync Users": "Synchroniser Utilisateurs",
                    "Sync Licenses": "Synchroniser Licences",
                    "Sync Usage": "Synchroniser Usage",
                    "Run Analysis": "Lancer Analyse",
                    "Download Report": "Télécharger Rapport"
                }
            }
        },
        lng: "fr",
        fallbackLng: "en",
        interpolation: {
            escapeValue: false
        }
    });

export default i18n;
