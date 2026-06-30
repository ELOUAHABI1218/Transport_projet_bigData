
# TAASIM – Urban Mobility Platform (Real-Time Taxi Dispatching)

## 📌 Description
TAASIM est une plateforme de simulation de mobilité intelligente pour la ville de **Casablanca**. Face à l'absence de données GPS historiques et au manque de visibilité en temps réel sur l'offre et la demande de transport, la plateforme simule des trajectoires réalistes et propose un système d'appariement dynamique entre les passagers et les taxis disponibles.

---

## 🎯 Objectifs
- Simuler des trajectoires GPS réalistes pour Casablanca (via remapping des données de Porto)
- Traiter les données en temps réel avec **Kafka** et **Flink**
- Apparier automatiquement les demandes de courses avec les taxis disponibles
- Prédire la demande par zone et par heure (modèle ML)
- Visualiser les métriques opérationnelles via **Grafana**
- Exposer une **API REST sécurisée** (FastAPI + JWT)

---

## 🏗️ Architecture Technique

| Couche | Technologie | Rôle |
|--------|-------------|------|
| **Stockage** | MinIO | Data Lake pour les données brutes et transformées |
| **Traitement batch** | PySpark | Nettoyage, remapping géographique, entraînement ML |
| **Ingestion temps réel** | Apache Kafka | Réception des positions GPS et demandes de courses |
| **Traitement streaming** | Apache Flink | Normalisation, agrégation, appariement |
| **Persistance** | Apache Cassandra | Stockage des positions, courses et métriques |
| **API Backend** | FastAPI | Exposition des endpoints sécurisés |
| **Visualisation** | Grafana | Dashboard temps réel |

---

## 🔄 Pipeline de Données

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TAASIM - ARCHITECTURE COMPLÈTE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    1. COUCHE BATCH (Spark)                            │   │
│  │    - Nettoyage des données Porto (1,7M trajets)                     │   │
│  │    - Remapping géographique Porto → Casablanca (89 688 trajets)     │   │
│  │    - Entraînement du modèle ML (GBT) sur données NYC                │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    2. COUCHE STREAMING (Kafka + Flink)                │   │
│  │    Topics Kafka : raw.gps, raw.trips, processed.demand              │   │
│  │    Jobs Flink : Normalisation, Agrégation, Appariement              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    3. COUCHE DE PERSISTANCE                          │   │
│  │    Apache Cassandra : positions GPS, courses, métriques             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    4. COUCHE DE VISUALISATION                         │   │
│  │    FastAPI (API REST sécurisée) + Grafana Dashboard                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Résultats

| Métrique | Résultat |
|----------|----------|
| Trajets générés pour Casablanca | **89 688** |
| Taux de succès du remapping | **89,7%** |
| Temps d'appariement | **< 5 secondes** |
| Amélioration du modèle ML (RMSE) | **63,9%** vs baseline |
| Distance moyenne de snapping | 138 mètres |

---

## 🛠️ Stack Technique

| Composant | Version |
|-----------|---------|
| Apache Spark | 3.2+ |
| Apache Kafka | 3.0+ |
| Apache Flink | 1.14+ |
| Apache Cassandra | 4.0+ |
| MinIO | Latest |
| FastAPI | 0.85+ |
| Grafana | 9.0+ |
| Docker | 20.10+ |
| Python | 3.8+ |

---

## 🚀 Installation et Déploiement

### Prérequis
- Docker & Docker Compose
- Python 3.8+
- Java 11+

### Lancer le projet
```bash
# 1. Cloner le repository
git clone https://github.com/samiraelyaagoubi2022/TAASIM-Urban-Mobility-Platform.git

# 2. Lancer les services avec Docker Compose
docker-compose up -d

# 3. Vérifier les services
docker-compose ps

# 4. Lancer l'API FastAPI
uvicorn api.main:app --reload --port 8000
```

---

## 📦 Structure du projet
```
TAASIM/
├── batch/               # Scripts Spark (nettoyage, remapping, ML)
├── streaming/           # Jobs Flink (normalisation, agrégation, matching)
├── kafka/               # Configuration Kafka
├── cassandra/           # Schémas Cassandra
├── api/                 # FastAPI (backend)
├── grafana/             # Dashboards Grafana
├── docker-compose.yml   # Orchestration des services
└── README.md
```

---

## 🔐 API Endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/auth/token` | POST | Authentification JWT |
| `/api/v1/trips` | POST | Création d'une course |
| `/api/v1/trips/{id}` | GET | Consultation d'une course |
| `/api/v1/vehicles/zone/{id}` | GET | Véhicules actifs par zone (admin) |
| `/api/demand/forecast` | POST | Prédiction de la demande (ML) |

---

## 📈 Perspectives d'amélioration
- Résoudre l'incompatibilité de versions Spark pour intégrer le modèle ML dans l'API
- Ajouter un panel de comparaison ML vs réel dans Grafana
- Enrichir les données avec des sources météo
- Améliorer le modèle avec plus de features

---

## 👥 Auteurs
- **Samira EL YAAGOUBI**
- **Fatima NABATI**
- **Ghizlane EL OUAHABI**

**Encadrement** : Mohamed El Marouani  
**Date** : 2025 - 2026

---

## 📜 Licence
Projet réalisé dans le cadre d'un projet académique.

