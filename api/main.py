from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, json, uuid
from datetime import datetime

# ── Kafka ──────────────────────────────────────────
from kafka import KafkaProducer

# ── MinIO / S3 ─────────────────────────────────────
import boto3
from botocore.client import Config

# ── Cassandra ──────────────────────────────────────
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

# ══════════════════════════════════════════════════
app = FastAPI(
    title="Taasim API",
    description="API REST pour la plateforme de transport Taasim",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config depuis variables d'environnement ────────
KAFKA_BROKER      = os.getenv("KAFKA_BROKER", "kafka:9092")
CASSANDRA_HOST    = os.getenv("CASSANDRA_HOST", "cassandra")
CASSANDRA_PORT    = int(os.getenv("CASSANDRA_PORT", 9042))
CASSANDRA_KEYSPACE= os.getenv("CASSANDRA_KEYSPACE", "taasim")
MINIO_ENDPOINT    = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY  = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY  = os.getenv("MINIO_SECRET_KEY", "minioadmin123")

# ══════════════════════════════════════════════════
# Clients (initialisés au démarrage)
# ══════════════════════════════════════════════════
producer = None
cassandra_session = None
s3_client = None

@app.on_event("startup")
async def startup():
    global producer, cassandra_session, s3_client

    # Kafka
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        print("✅ Kafka connecté")
    except Exception as e:
        print(f"⚠️  Kafka non disponible : {e}")

    # Cassandra
    try:
        cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
        cassandra_session = cluster.connect()
        # Crée le keyspace si absent
        cassandra_session.execute(f"""
            CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE}
            WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': '1'}}
        """)
        cassandra_session.set_keyspace(CASSANDRA_KEYSPACE)
        # Tables de base
        cassandra_session.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                driver_id  UUID,
                timestamp  TIMESTAMP,
                lat        DOUBLE,
                lng        DOUBLE,
                PRIMARY KEY (driver_id, timestamp)
            ) WITH CLUSTERING ORDER BY (timestamp DESC)
        """)
        cassandra_session.execute("""
            CREATE TABLE IF NOT EXISTS rides (
                ride_id    UUID PRIMARY KEY,
                driver_id  UUID,
                rider_id   UUID,
                status     TEXT,
                created_at TIMESTAMP
            )
        """)
        print("✅ Cassandra connecté")
    except Exception as e:
        print(f"⚠️  Cassandra non disponible : {e}")

    # MinIO
    try:
        s3_client = boto3.client(
            "s3",
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
            config=Config(signature_version="s3v4"),
        )
        print("✅ MinIO connecté")
    except Exception as e:
        print(f"⚠️  MinIO non disponible : {e}")


# ══════════════════════════════════════════════════
# MODÈLES
# ══════════════════════════════════════════════════
class Position(BaseModel):
    driver_id: str
    lat: float
    lng: float

class RideRequest(BaseModel):
    rider_id: str
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float


# ══════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════

@app.get("/")
def root():
    return {"status": "ok", "service": "Taasim API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {
        "kafka":     producer is not None,
        "cassandra": cassandra_session is not None,
        "minio":     s3_client is not None,
    }

# ── Positions en temps réel ────────────────────────
@app.post("/positions")
def push_position(pos: Position):
    """Envoie la position d'un chauffeur → Kafka topic 'driver-positions'"""
    event = {**pos.dict(), "timestamp": datetime.utcnow().isoformat()}
    if producer:
        producer.send("driver-positions", event)
        producer.flush()
    if cassandra_session:
        cassandra_session.execute(
            "INSERT INTO positions (driver_id, timestamp, lat, lng) VALUES (%s, %s, %s, %s)",
            (uuid.UUID(pos.driver_id), datetime.utcnow(), pos.lat, pos.lng)
        )
    return {"status": "published", "event": event}

@app.get("/positions/{driver_id}")
def get_positions(driver_id: str, limit: int = 10):
    """Récupère les dernières positions d'un chauffeur"""
    if not cassandra_session:
        raise HTTPException(503, "Cassandra non disponible")
    rows = cassandra_session.execute(
        "SELECT * FROM positions WHERE driver_id = %s LIMIT %s",
        (uuid.UUID(driver_id), limit)
    )
    return [{"driver_id": str(r.driver_id), "lat": r.lat, "lng": r.lng,
             "timestamp": str(r.timestamp)} for r in rows]

# ── Courses ────────────────────────────────────────
@app.post("/rides")
def create_ride(req: RideRequest):
    """Crée une demande de course → Kafka topic 'ride-requests'"""
    ride_id = str(uuid.uuid4())
    event = {"ride_id": ride_id, **req.dict(), "timestamp": datetime.utcnow().isoformat()}
    if producer:
        producer.send("ride-requests", event)
        producer.flush()
    if cassandra_session:
        cassandra_session.execute(
            "INSERT INTO rides (ride_id, rider_id, status, created_at) VALUES (%s, %s, %s, %s)",
            (uuid.UUID(ride_id), uuid.UUID(req.rider_id), "pending", datetime.utcnow())
        )
    return {"ride_id": ride_id, "status": "pending"}

@app.get("/rides/{ride_id}")
def get_ride(ride_id: str):
    if not cassandra_session:
        raise HTTPException(503, "Cassandra non disponible")
    row = cassandra_session.execute(
        "SELECT * FROM rides WHERE ride_id = %s", (uuid.UUID(ride_id),)
    ).one()
    if not row:
        raise HTTPException(404, "Course introuvable")
    return {"ride_id": str(row.ride_id), "status": row.status,
            "created_at": str(row.created_at)}