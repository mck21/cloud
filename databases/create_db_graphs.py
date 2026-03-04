import boto3
import json

# ── CONFIGURACIÓN ──────────────────────────────────────────────
DB_INSTANCE = "db-mck21"
DASHBOARD_NAME = "RDS-Monitorización-db-mck21"
REGION = "us-east-1"
# ───────────────────────────────────────────────────────────────

client = boto3.client("cloudwatch", region_name=REGION)

def metric_widget(title, metrics_list, y_pos, stat="Average", period=60, view="timeSeries"):
    """Genera un widget de métrica para el dashboard."""
    metrics = []
    for namespace, metric_name, dimensions in metrics_list:
        dim_list = [{"Name": k, "Value": v} for k, v in dimensions.items()]
        metrics.append([namespace, metric_name, *[item for pair in zip(
            [d["Name"] for d in dim_list],
            [d["Value"] for d in dim_list]
        ) for item in pair]])
    
    return {
        "type": "metric",
        "x": 0,
        "y": y_pos,
        "width": 24,
        "height": 6,
        "properties": {
            "title": title,
            "view": view,
            "stacked": False,
            "metrics": metrics,
            "stat": stat,
            "period": period,
            "region": REGION,
            "yAxis": {"left": {"min": 0}}
        }
    }

def rds_metric(metric_name):
    return ("AWS/RDS", metric_name, {"DBInstanceIdentifier": DB_INSTANCE})

# ── WIDGETS DEL DASHBOARD ──────────────────────────────────────
widgets = [

    # Título / texto informativo
    {
        "type": "text",
        "x": 0, "y": 0,
        "width": 24, "height": 2,
        "properties": {
            "markdown": f"# 📊 Dashboard RDS — `{DB_INSTANCE}`\nMétricas clave para monitorizar rendimiento antes y después del escalado vertical."
        }
    },

    # 1. CPU
    metric_widget(
        title="⚙️ CPUUtilization — Uso de CPU (%)",
        metrics_list=[rds_metric("CPUUtilization")],
        y_pos=2
    ),

    # 2. Memoria libre
    metric_widget(
        title="🧠 FreeableMemory — Memoria RAM libre (Bytes)",
        metrics_list=[rds_metric("FreeableMemory")],
        y_pos=8
    ),

    # 3. IOPS lectura y escritura juntos
    {
        "type": "metric",
        "x": 0, "y": 14,
        "width": 24, "height": 6,
        "properties": {
            "title": "💾 ReadIOPS / WriteIOPS — Operaciones de E/S por segundo",
            "view": "timeSeries",
            "stacked": False,
            "metrics": [
                ["AWS/RDS", "ReadIOPS",  "DBInstanceIdentifier", DB_INSTANCE],
                ["AWS/RDS", "WriteIOPS", "DBInstanceIdentifier", DB_INSTANCE]
            ],
            "stat": "Average",
            "period": 60,
            "region": REGION,
            "yAxis": {"left": {"min": 0}}
        }
    },

    # 4. DiskQueueDepth
    metric_widget(
        title="📂 DiskQueueDepth — Cola de disco (saturación)",
        metrics_list=[rds_metric("DiskQueueDepth")],
        y_pos=20
    ),

    # 5. Conexiones activas
    metric_widget(
        title="🔗 DatabaseConnections — Conexiones activas",
        metrics_list=[rds_metric("DatabaseConnections")],
        y_pos=26
    ),

    # 6. Latencia lectura y escritura juntos
    {
        "type": "metric",
        "x": 0, "y": 32,
        "width": 24, "height": 6,
        "properties": {
            "title": "⏱️ ReadLatency / WriteLatency — Latencia de disco (segundos)",
            "view": "timeSeries",
            "stacked": False,
            "metrics": [
                ["AWS/RDS", "ReadLatency",  "DBInstanceIdentifier", DB_INSTANCE],
                ["AWS/RDS", "WriteLatency", "DBInstanceIdentifier", DB_INSTANCE]
            ],
            "stat": "Average",
            "period": 60,
            "region": REGION,
            "yAxis": {"left": {"min": 0}}
        }
    },
]

# ── CREAR / ACTUALIZAR DASHBOARD ───────────────────────────────
dashboard_body = json.dumps({"widgets": widgets})

response = client.put_dashboard(
    DashboardName=DASHBOARD_NAME,
    DashboardBody=dashboard_body
)

print(f"✅ Dashboard creado/actualizado: {DASHBOARD_NAME}")
print(f"🔗 URL: https://{REGION}.console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name={DASHBOARD_NAME}")

if response.get("DashboardValidationMessages"):
    print("⚠️  Advertencias de validación:")
    for msg in response["DashboardValidationMessages"]:
        print(f"   - {msg}")
else:
    print("✔️  Sin errores de validación.")