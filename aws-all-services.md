# ☁️ Lista Completa de Servicios AWS
> Guía de referencia rápida para el examen AWS Cloud Practitioner  
> Cada servicio con su función en una línea. Aprende el "para qué sirve" y podrás responder cualquier pregunta.

---

## 🖥️ CÓMPUTO

| Servicio | Descripción |
|---|---|
| **Amazon EC2** | → Servidores virtuales en la nube (máquinas virtuales) |
| **Amazon EC2 Auto Scaling** | → Escala automáticamente el número de instancias EC2 según la demanda |
| **Amazon EC2 Spot Instances** | → Instancias EC2 con descuento de hasta 90% (pueden interrumpirse) |
| **Amazon EC2 Reserved Instances** | → Instancias EC2 con descuento a cambio de comprometerse 1-3 años |
| **Amazon EC2 Dedicated Hosts** | → Servidor físico dedicado exclusivamente a ti (cumplimiento y licencias) |
| **Amazon EC2 Image Builder** | → Crea y mantiene imágenes de máquinas virtuales (AMIs) de forma automática |
| **Amazon Lightsail** | → Servidores virtuales simples y económicos para principiantes o apps pequeñas |
| **AWS Lambda** | → Ejecuta código sin gestionar servidores (serverless), pagas solo por uso |
| **AWS Batch** | → Ejecuta trabajos batch (por lotes) a cualquier escala sin gestionar servidores |
| **AWS Elastic Beanstalk** | → Despliega apps web automáticamente sin preocuparte por la infraestructura |
| **AWS Outposts** | → Infraestructura AWS instalada físicamente en tus propias instalaciones |
| **AWS Wavelength** | → Despliega apps con latencia ultra-baja dentro de redes 5G de operadoras |
| **AWS Local Zones** | → Extiende AWS a ubicaciones geográficas más cercanas a los usuarios finales |
| **Amazon Elastic Container Service (ECS)** | → Orquestación de contenedores Docker gestionada por AWS |
| **Amazon Elastic Kubernetes Service (EKS)** | → Kubernetes gestionado por AWS (orquestación de contenedores) |
| **AWS Fargate** | → Ejecuta contenedores sin gestionar servidores ni clusters (serverless containers) |
| **Amazon Elastic Container Registry (ECR)** | → Repositorio privado para guardar imágenes de contenedores Docker |
| **AWS App Runner** | → Despliega apps web y APIs desde código fuente o contenedor en segundos |
| **Amazon EC2 VM Import/Export** | → Importa máquinas virtuales desde tu entorno local a EC2 y viceversa |
| **AWS SimSpace Weaver** | → Ejecuta simulaciones espaciales dinámicas a gran escala en la nube |

---

## 💾 ALMACENAMIENTO

| Servicio | Descripción |
|---|---|
| **Amazon S3** | → Almacenamiento de objetos (archivos, imágenes, backups) escalable e ilimitado |
| **Amazon S3 Glacier** | → Almacenamiento de archivos de muy bajo coste para datos que rara vez se acceden |
| **Amazon S3 Glacier Deep Archive** | → La opción más barata de AWS para archivar datos a largo plazo |
| **Amazon EBS (Elastic Block Store)** | → Discos duros virtuales para instancias EC2 (como un SSD en la nube) |
| **Amazon EFS (Elastic File System)** | → Sistema de archivos NFS compartido y escalable para múltiples instancias EC2 |
| **Amazon FSx** | → Sistemas de archivos de alto rendimiento gestionados (Windows, Lustre, OpenZFS) |
| **Amazon FSx for Windows File Server** | → Sistema de archivos Windows nativo completamente gestionado |
| **Amazon FSx for Lustre** | → Sistema de archivos de altísimo rendimiento para HPC e integrado con S3 |
| **Amazon FSx for OpenZFS** | → Sistema de archivos OpenZFS gestionado para workloads exigentes |
| **AWS Storage Gateway** | → Conecta tu almacenamiento local con la nube AWS de forma híbrida |
| **AWS Backup** | → Centraliza y automatiza copias de seguridad de todos tus servicios AWS |
| **AWS Snow Family** | → Dispositivos físicos para migrar grandes volúmenes de datos a AWS sin internet |
| **AWS Snowcone** | → El dispositivo Snow más pequeño y portátil (hasta 14TB) para edge computing |
| **AWS Snowball** | → Dispositivo físico robusto para migrar petabytes de datos a AWS |
| **AWS Snowmobile** | → Camión con contenedor para migrar cantidades exabyte de datos a AWS |
| **Amazon S3 Transfer Acceleration** | → Acelera subidas a S3 usando los puntos de presencia de CloudFront |
| **AWS DataSync** | → Transfiere datos de forma automática y rápida entre on-premises y AWS |

---

## 🗄️ BASES DE DATOS

| Servicio | Descripción |
|---|---|
| **Amazon RDS** | → Base de datos relacional gestionada (MySQL, PostgreSQL, Oracle, SQL Server...) |
| **Amazon Aurora** | → Base de datos relacional de alto rendimiento compatible con MySQL y PostgreSQL |
| **Amazon Aurora Serverless** | → Aurora que escala automáticamente según el uso, incluso a cero |
| **Amazon DynamoDB** | → Base de datos NoSQL serverless de altísima velocidad y escala |
| **Amazon DynamoDB Accelerator (DAX)** | → Caché en memoria para DynamoDB, respuestas en microsegundos |
| **Amazon ElastiCache** | → Caché en memoria gestionada (Redis o Memcached) para acelerar apps |
| **Amazon Neptune** | → Base de datos de grafos gestionada (relaciones complejas entre datos) |
| **Amazon DocumentDB** | → Base de datos de documentos compatible con MongoDB, gestionada por AWS |
| **Amazon Keyspaces** | → Base de datos compatible con Apache Cassandra, serverless y gestionada |
| **Amazon QLDB** | → Base de datos de libro mayor (ledger) inmutable y con historial verificable |
| **Amazon Timestream** | → Base de datos de series temporales para IoT y datos con marca de tiempo |
| **Amazon MemoryDB for Redis** | → Base de datos en memoria durable y compatible con Redis |
| **Amazon Redshift** | → Data warehouse columnar para análisis de grandes volúmenes de datos |
| **Amazon RDS Proxy** | → Proxy gestionado que mejora escalabilidad y disponibilidad de RDS |

---

## 🌐 REDES Y ENTREGA DE CONTENIDO

| Servicio | Descripción |
|---|---|
| **Amazon VPC** | → Red privada virtual aislada dentro de AWS (tu propio espacio de red) |
| **Amazon CloudFront** | → CDN global que entrega contenido con baja latencia desde puntos de presencia |
| **Amazon Route 53** | → DNS escalable y de alta disponibilidad, también gestiona dominios |
| **AWS Direct Connect** | → Conexión de red dedicada y privada entre tus instalaciones y AWS |
| **AWS VPN (Site-to-Site)** | → Túnel VPN cifrado entre tu red local y AWS por internet |
| **AWS Transit Gateway** | → Hub central para conectar múltiples VPCs y redes on-premises |
| **Elastic Load Balancing (ELB)** | → Distribuye el tráfico entrante entre múltiples instancias o servicios |
| **AWS Global Accelerator** | → Mejora la disponibilidad y rendimiento de apps globales usando la red de AWS |
| **Amazon API Gateway** | → Crea, publica y gestiona APIs REST, HTTP y WebSocket a escala |
| **AWS PrivateLink** | → Conecta servicios de forma privada sin exponer el tráfico a internet |
| **VPC Peering** | → Conecta dos VPCs entre sí de forma directa y privada |
| **AWS Network Firewall** | → Firewall gestionado y escalable para proteger tus VPCs |
| **AWS Shield** | → Protección contra ataques DDoS (Shield Standard gratis, Advanced de pago) |
| **AWS WAF** | → Firewall de aplicaciones web para filtrar tráfico malicioso HTTP |
| **Amazon VPC Lattice** | → Conecta, asegura y monitoriza servicios entre múltiples cuentas y VPCs |

---

## 🔐 SEGURIDAD, IDENTIDAD Y CUMPLIMIENTO

| Servicio | Descripción |
|---|---|
| **AWS IAM** | → Gestiona usuarios, roles y permisos para acceder a recursos AWS |
| **AWS IAM Identity Center (SSO)** | → Inicio de sesión único para todas tus cuentas AWS y apps empresariales |
| **Amazon Cognito** | → Autenticación e identidad para usuarios de tus aplicaciones (login de usuarios) |
| **AWS Key Management Service (KMS)** | → Crea y gestiona claves de cifrado para proteger tus datos |
| **AWS CloudHSM** | → Módulo de seguridad hardware dedicado para gestionar claves de cifrado |
| **AWS Secrets Manager** | → Guarda y rota automáticamente contraseñas, API keys y otros secretos |
| **AWS Certificate Manager (ACM)** | → Provee y gestiona certificados SSL/TLS para tus apps de forma gratuita |
| **Amazon GuardDuty** | → Detección de amenazas inteligente que monitoriza tu cuenta AWS continuamente |
| **Amazon Inspector** | → Escanea vulnerabilidades automáticamente en EC2, Lambda y ECR |
| **Amazon Macie** | → Detecta automáticamente datos sensibles (PII) almacenados en S3 con ML |
| **AWS Security Hub** | → Panel centralizado que agrega alertas de seguridad de múltiples servicios |
| **Amazon Detective** | → Analiza y visualiza datos de seguridad para investigar incidentes |
| **AWS Config** | → Registra y evalúa la configuración de tus recursos AWS a lo largo del tiempo |
| **AWS CloudTrail** | → Registra todas las llamadas a la API de tu cuenta AWS (auditoría completa) |
| **AWS Artifact** | → Portal para descargar informes de cumplimiento y auditoría de AWS |
| **AWS Audit Manager** | → Automatiza la recopilación de evidencias para auditorías y cumplimiento |
| **AWS Shield Advanced** | → Protección DDoS avanzada con soporte 24/7 del equipo de respuesta de AWS |
| **AWS Firewall Manager** | → Gestiona centralmente reglas de WAF, Shield y Security Groups en toda la org |
| **Amazon Verified Permissions** | → Gestiona autorización de permisos detallados para tus apps con Cedar |
| **AWS Signer** | → Firma criptográficamente el código para Lambda e IoT |
| **AWS Directory Service** | → Microsoft Active Directory gestionado en la nube AWS |
| **AD Connector** | → Redirige peticiones de directorio hacia tu Active Directory local sin sincronizar datos |

---

## 📊 ANÁLISIS Y BIG DATA

| Servicio | Descripción |
|---|---|
| **Amazon Athena** | → Consulta datos directamente en S3 con SQL, sin mover los datos, serverless |
| **Amazon Redshift** | → Data warehouse columnar para analítica a gran escala (petabytes) |
| **Amazon EMR** | → Clúster Hadoop/Spark gestionado para procesar grandes volúmenes de datos |
| **Amazon EMR Serverless** | → Ejecuta Spark/Hadoop sin gestionar clústeres |
| **Amazon Kinesis** | → Procesa y analiza flujos de datos y vídeo en tiempo real |
| **Amazon Kinesis Data Streams** | → Captura y almacena flujos de datos en tiempo real para procesamiento posterior |
| **Amazon Kinesis Data Firehose** | → Carga flujos de datos directamente en S3, Redshift u otros destinos |
| **Amazon Kinesis Data Analytics** | → Analiza flujos de datos en tiempo real con SQL o Apache Flink |
| **Amazon Kinesis Video Streams** | → Captura, procesa y analiza flujos de vídeo desde dispositivos |
| **AWS Glue** | → ETL serverless para preparar y transformar datos para análisis |
| **AWS Glue DataBrew** | → Limpia y normaliza datos visualmente sin escribir código |
| **Amazon QuickSight** | → Herramienta de Business Intelligence (BI) para crear dashboards y visualizaciones |
| **Amazon OpenSearch Service** | → Motor de búsqueda y análisis de logs basado en Elasticsearch |
| **AWS Lake Formation** | → Crea y gestiona un data lake seguro en días en lugar de meses |
| **Amazon DataZone** | → Cataloga, comparte y gobierna datos entre equipos y cuentas de forma segura |
| **Amazon FinSpace** | → Almacena, cataloga y analiza datos financieros específicos del sector |
| **Amazon Clean Rooms** | → Colabora y analiza datos con otras empresas sin compartir datos brutos |
| **Amazon Managed Streaming for Apache Kafka (MSK)** | → Kafka completamente gestionado para streaming de datos |

---

## 🤖 INTELIGENCIA ARTIFICIAL Y MACHINE LEARNING

| Servicio | Descripción |
|---|---|
| **Amazon SageMaker** | → Plataforma completa para construir, entrenar y desplegar modelos de ML |
| **Amazon Bedrock** | → Accede a modelos de IA generativa de terceros (Claude, Llama, etc.) via API |
| **Amazon Rekognition** | → Análisis de imágenes y vídeo con IA (detección de objetos, caras, texto) |
| **Amazon Textract** | → Extrae texto y datos de documentos escaneados con IA |
| **Amazon Comprehend** | → Análisis de texto en lenguaje natural (sentimiento, entidades, idioma) |
| **Amazon Comprehend Medical** | → Extrae información médica de texto clínico no estructurado |
| **Amazon Transcribe** | → Convierte audio a texto (reconocimiento de voz automático) |
| **Amazon Polly** | → Convierte texto a voz (síntesis de voz) |
| **Amazon Translate** | → Traducción automática de texto entre idiomas |
| **Amazon Lex** | → Crea chatbots de voz y texto (la tecnología detrás de Alexa) |
| **Amazon Kendra** | → Motor de búsqueda empresarial inteligente con ML |
| **Amazon Personalize** | → Añade recomendaciones personalizadas a tus apps (como las de Amazon.com) |
| **Amazon Forecast** | → Genera predicciones de series temporales con ML (ventas, demanda, etc.) |
| **Amazon Fraud Detector** | → Detecta fraudes online en tiempo real con ML |
| **Amazon Lookout for Metrics** | → Detecta anomalías automáticamente en métricas de negocio |
| **Amazon Lookout for Vision** | → Detecta defectos en imágenes de productos industriales con ML |
| **Amazon Lookout for Equipment** | → Detecta comportamientos anómalos en maquinaria industrial |
| **Amazon Monitron** | → Solución end-to-end para monitorizar equipos industriales y detectar anomalías |
| **Amazon Augmented AI (A2I)** | → Añade revisión humana a predicciones de ML de baja confianza |
| **Amazon CodeGuru** | → Detecta bugs y problemas de rendimiento en el código con ML |
| **Amazon DevOps Guru** | → Detecta anomalías operativas y problemas de disponibilidad con ML |
| **AWS Panorama** | → Añade visión artificial a cámaras existentes en instalaciones locales |
| **Amazon Healthlake** | → Almacena, transforma y analiza datos sanitarios en formato FHIR |
| **Amazon Titan** | → Modelos de IA generativa propios de AWS (texto, embeddings, imágenes) |
| **Amazon Q** | → Asistente de IA generativa para empresas integrado con datos propios |
| **Amazon Q Developer** | → Asistente de IA para desarrolladores (genera, explica y revisa código) |
| **AWS Neuron** | → SDK para optimizar modelos de ML en chips Trainium e Inferentia de AWS |

---

## 🔧 HERRAMIENTAS DE DESARROLLO

| Servicio | Descripción |
|---|---|
| **AWS CodeCommit** | → Repositorio Git privado y gestionado en AWS (como GitHub privado) |
| **AWS CodeBuild** | → Servicio de compilación y pruebas de código completamente gestionado |
| **AWS CodeDeploy** | → Automatiza el despliegue de código en EC2, Lambda o servidores locales |
| **AWS CodePipeline** | → Crea pipelines de CI/CD para automatizar todo el proceso de entrega de software |
| **AWS CodeArtifact** | → Repositorio de paquetes gestionado (npm, Maven, pip...) para dependencias |
| **Amazon CodeCatalyst** | → Entorno de desarrollo unificado para todo el ciclo de vida del software |
| **AWS Cloud9** | → IDE en la nube que funciona directamente en el navegador |
| **AWS CloudShell** | → Shell en el navegador con AWS CLI preinstalado para ejecutar comandos rápidos |
| **AWS X-Ray** | → Traza y depura aplicaciones distribuidas para encontrar cuellos de botella |
| **Amazon CodeWhisperer** | → Asistente de código con IA que sugiere líneas y funciones completas |
| **AWS SDK** | → Kits de desarrollo de software para usar AWS desde múltiples lenguajes |
| **AWS CLI** | → Interfaz de línea de comandos para gestionar todos los servicios AWS |

---

## ⚙️ GESTIÓN Y GOBIERNO

| Servicio | Descripción |
|---|---|
| **AWS Management Console** | → Interfaz web para gestionar todos los servicios AWS visualmente |
| **AWS Organizations** | → Gestiona y consolida múltiples cuentas AWS bajo una sola organización |
| **AWS Control Tower** | → Configura y gobierna un entorno multi-cuenta seguro de forma automática |
| **AWS CloudFormation** | → Crea y gestiona infraestructura como código (IaC) con plantillas |
| **AWS CDK (Cloud Development Kit)** | → Define infraestructura como código usando lenguajes de programación reales |
| **AWS Systems Manager** | → Gestiona, configura y opera recursos AWS e instancias EC2 de forma centralizada |
| **AWS CloudWatch** | → Monitoriza métricas, logs y eventos de todos tus recursos AWS |
| **AWS CloudTrail** | → Audita todas las acciones realizadas en tu cuenta AWS (quién hizo qué y cuándo) |
| **AWS Config** | → Registra cambios en la configuración de recursos y evalúa cumplimiento |
| **AWS Trusted Advisor** | → Analiza tu cuenta y da recomendaciones de costes, seguridad, rendimiento y más |
| **AWS Well-Architected Tool** | → Evalúa tu arquitectura según las mejores prácticas del Well-Architected Framework |
| **AWS Service Catalog** | → Crea y gestiona catálogos de servicios IT aprobados para tu organización |
| **AWS License Manager** | → Gestiona licencias de software de terceros en AWS y on-premises |
| **AWS Health Dashboard** | → Muestra el estado de los servicios AWS y alertas personalizadas para tu cuenta |
| **AWS OpsWorks** | → Gestión de configuración con Chef y Puppet |
| **AWS Managed Grafana** | → Grafana gestionado para visualizar métricas operacionales y de negocio |
| **AWS Managed Prometheus** | → Prometheus gestionado para monitorización de contenedores |
| **AWS Resilience Hub** | → Evalúa y mejora la resiliencia de tus aplicaciones ante fallos |
| **AWS Fault Injection Simulator** | → Realiza experimentos de chaos engineering para probar la resiliencia |
| **Service Quotas** | → Gestiona y solicita aumentos de los límites de servicio AWS desde un panel central |
| **AWS Resource Explorer** | → Busca y descubre recursos AWS en todas tus regiones desde un solo lugar |
| **AWS Compute Optimizer** | → Recomienda el tipo de instancia óptimo para tus workloads y ahorra costes |
| **AWS Auto Scaling** | → Escala automáticamente múltiples recursos (EC2, DynamoDB, ECS...) según la demanda |

---

## 💰 GESTIÓN DE COSTES

| Servicio | Descripción |
|---|---|
| **AWS Cost Explorer** | → Visualiza, entiende y gestiona tus costes y uso de AWS a lo largo del tiempo |
| **AWS Budgets** | → Define presupuestos y recibe alertas cuando el gasto se acerca al límite |
| **AWS Cost and Usage Report (CUR)** | → Informe detallado de todo tu consumo y costes en AWS |
| **AWS Savings Plans** | → Descuentos flexibles en cómputo a cambio de comprometerse a un uso mínimo |
| **AWS Pricing Calculator** | → Estima el coste de arquitecturas AWS antes de implementarlas |
| **AWS Marketplace** | → Tienda de software de terceros listo para desplegar en AWS |
| **AWS Billing Conductor** | → Personaliza facturas para revendedores o gestión interna de costes |

---

## 📨 MENSAJERÍA E INTEGRACIÓN DE APLICACIONES

| Servicio | Descripción |
|---|---|
| **Amazon SQS** | → Cola de mensajes gestionada para desacoplar componentes de aplicaciones |
| **Amazon SNS** | → Servicio de notificaciones pub/sub para enviar mensajes a múltiples suscriptores |
| **Amazon EventBridge** | → Bus de eventos serverless para conectar apps entre sí y con servicios AWS |
| **Amazon MQ** | → Broker de mensajería gestionado compatible con ActiveMQ y RabbitMQ |
| **AWS Step Functions** | → Orquesta flujos de trabajo serverless coordinando múltiples servicios AWS |
| **Amazon AppFlow** | → Integra apps SaaS (Salesforce, SAP...) con AWS sin escribir código |
| **Amazon SES (Simple Email Service)** | → Envío masivo de emails transaccionales y de marketing a bajo coste |
| **AWS AppSync** | → Crea APIs GraphQL gestionadas en tiempo real para aplicaciones |

---

## 🔌 INTEGRACIÓN HÍBRIDA Y MIGRACIÓN

| Servicio | Descripción |
|---|---|
| **AWS Migration Hub** | → Panel central para rastrear el progreso de migraciones a AWS |
| **AWS Application Migration Service (MGN)** | → Migra servidores físicos y VMs a AWS con mínima interrupción |
| **AWS Database Migration Service (DMS)** | → Migra bases de datos a AWS de forma continua y con mínimo downtime |
| **AWS Schema Conversion Tool (SCT)** | → Convierte esquemas de bases de datos al cambiar de motor (ej: Oracle a Aurora) |
| **AWS Application Discovery Service** | → Descubre y analiza tus aplicaciones on-premises para planificar la migración |
| **AWS Server Migration Service (SMS)** | → Migra máquinas virtuales desde VMware/Hyper-V a AWS (reemplazado por MGN) |
| **AWS DataSync** | → Transfiere datos entre almacenamiento on-premises y AWS de forma rápida y segura |
| **AWS Transfer Family** | → Transfiere archivos a S3 y EFS con SFTP, FTPS y FTP gestionado |
| **AWS Direct Connect** | → Conexión de red privada y dedicada entre tu centro de datos y AWS |
| **AWS VPN** | → Túnel cifrado por internet entre tu red local y tu VPC en AWS |
| **VMware Cloud on AWS** | → Ejecuta entornos VMware nativos directamente sobre infraestructura AWS |

---

## 📱 FRONTEND Y APLICACIONES MÓVILES

| Servicio | Descripción |
|---|---|
| **AWS Amplify** | → Plataforma completa para construir y desplegar apps web y móviles fullstack |
| **Amazon API Gateway** | → Crea y gestiona APIs para backends de aplicaciones móviles y web |
| **AWS Device Farm** | → Prueba apps móviles y web en dispositivos reales en la nube |
| **Amazon Location Service** | → Añade funcionalidades de mapas, geolocalización y rutas a tus apps |
| **Amazon Pinpoint** | → Segmenta usuarios y envía notificaciones push, email y SMS personalizados |
| **AppStream 2.0** | → Transmite aplicaciones de escritorio Windows a cualquier navegador |
| **Amazon WorkSpaces** | → Escritorios virtuales en la nube (Virtual Desktop Infrastructure) |
| **Amazon WorkSpaces Web** | → Navegador web seguro y gestionado para acceder a apps internas |

---

## 🏭 IoT (INTERNET OF THINGS)

| Servicio | Descripción |
|---|---|
| **AWS IoT Core** | → Conecta dispositivos IoT a la nube AWS de forma segura y a escala |
| **AWS IoT Greengrass** | → Extiende AWS a dispositivos edge para cómputo y mensajería local |
| **AWS IoT Analytics** | → Analiza datos de dispositivos IoT a escala sin gestionar infraestructura |
| **AWS IoT Events** | → Detecta y responde a eventos procedentes de dispositivos IoT |
| **AWS IoT SiteWise** | → Recopila e interpreta datos de equipos industriales a escala |
| **AWS IoT TwinMaker** | → Crea gemelos digitales de sistemas del mundo real (fábricas, edificios...) |
| **AWS IoT FleetWise** | → Recopila y transfiere datos de vehículos a la nube en tiempo casi real |
| **AWS IoT Device Defender** | → Audita y monitoriza la seguridad de tu flota de dispositivos IoT |
| **AWS IoT Device Management** | → Incorpora, organiza, monitoriza y gestiona dispositivos IoT a escala |
| **Amazon Monitron** | → Solución completa para monitorización predictiva de equipos industriales |
| **AWS RoboMaker** | → Simula, prueba y despliega aplicaciones robóticas |

---

## 🎮 JUEGOS

| Servicio | Descripción |
|---|---|
| **Amazon GameLift** | → Hosting dedicado de servidores de juegos con escalado automático |
| **Amazon GameSparks** | → Backend serverless para juegos (tablas de clasificación, datos de jugadores, etc.) |

---

## 🎬 MEDIA Y STREAMING

| Servicio | Descripción |
|---|---|
| **Amazon Elastic Transcoder** | → Convierte archivos de vídeo a diferentes formatos para distintos dispositivos |
| **AWS Elemental MediaConvert** | → Transcripción de vídeo broadcast de alta calidad basada en archivos |
| **AWS Elemental MediaLive** | → Codifica vídeo en directo para broadcast y streaming |
| **AWS Elemental MediaPackage** | → Empaqueta y protege contenido de vídeo para distribución |
| **AWS Elemental MediaStore** | → Almacenamiento optimizado para vídeo en directo con baja latencia |
| **AWS Elemental MediaTailor** | → Inserción de anuncios personalizada en streams de vídeo |
| **Amazon Interactive Video Service (IVS)** | → Crea experiencias de streaming en directo interactivas de baja latencia |
| **Amazon Nimble Studio** | → Acelera el desarrollo de contenido creativo para VFX y animación en la nube |

---

## ⚛️ COMPUTACIÓN CUÁNTICA

| Servicio | Descripción |
|---|---|
| **Amazon Braket** | → Experimenta y desarrolla algoritmos de computación cuántica en la nube |

---

## 🛰️ ESPACIO Y SATÉLITES

| Servicio | Descripción |
|---|---|
| **AWS Ground Station** | → Controla satélites y procesa datos de satélite directamente desde AWS |

---

## 🏢 PRODUCTIVIDAD EMPRESARIAL

| Servicio | Descripción |
|---|---|
| **Amazon WorkMail** | → Servicio gestionado de email y calendario corporativo |
| **Amazon WorkDocs** | → Almacenamiento y colaboración de documentos corporativos en la nube |
| **Amazon Chime** | → Videollamadas, reuniones y chat para empresas |
| **Amazon Connect** | → Centro de contacto (call center) omnicanal en la nube |
| **Alexa for Business** | → Integra Alexa en el entorno empresarial para automatizar tareas de trabajo |
| **Amazon Honeycode** | → Crea apps web y móviles simples sin programar, desde hojas de cálculo |

---

## 🔬 INVESTIGACIÓN Y EDUCACIÓN

| Servicio | Descripción |
|---|---|
| **AWS Academy** | → Programa educativo de AWS para instituciones de enseñanza superior |
| **AWS Educate** | → Recursos y créditos gratuitos de AWS para estudiantes y educadores |
| **Amazon Corretto** | → Distribución gratuita y lista para producción de OpenJDK (Java) |

---

## 📋 RESUMEN RÁPIDO PARA EL EXAMEN

### Los "must-know" del Cloud Practitioner:

| Categoría | Servicios clave |
|---|---|
| **Cómputo** | EC2, Lambda, Elastic Beanstalk, ECS, EKS, Fargate, Lightsail, Batch |
| **Almacenamiento** | S3, EBS, EFS, Glacier, Storage Gateway, Snowball |
| **Bases de datos** | RDS, Aurora, DynamoDB, ElastiCache, Redshift |
| **Redes** | VPC, CloudFront, Route 53, ELB, Direct Connect, API Gateway |
| **Seguridad** | IAM, KMS, Cognito, GuardDuty, Inspector, Shield, WAF, CloudTrail |
| **Análisis** | Athena, Kinesis, Glue, QuickSight, EMR |
| **IA/ML** | SageMaker, Rekognition, Comprehend, Transcribe, Polly, Lex, Bedrock |
| **Gestión** | CloudWatch, CloudFormation, CloudTrail, Trusted Advisor, Organizations |
| **Migración** | DMS, Migration Hub, Snowball, DataSync |
| **Mensajería** | SQS, SNS, EventBridge, Step Functions |

---

> 💡 **Tip**: En el examen, el nombre del servicio suele darte la pista. Si ves "Managed", es que AWS gestiona la infraestructura por ti. Si ves "Serverless", no pagas por servidores inactivos. Si ves "Glacier", es almacenamiento frío y barato.
