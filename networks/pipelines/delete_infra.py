#!/usr/bin/env python3
"""
Script de limpieza de recursos AWS para la práctica de Pipeline
Elimina recursos de S3, Glue, Athena y QuickSight

Uso:
    python cleanup_aws_pipeline.py --bucket-name TU_BUCKET --database-name TU_DATABASE

Flags opcionales:
    --dry-run : Muestra qué se eliminaría sin eliminarlo realmente
    --keep-bucket : Mantiene el bucket S3 (solo vacía su contenido)
    --region : Especifica la región (default: us-east-1)
"""

import boto3
import argparse
import sys
from botocore.exceptions import ClientError

class AWSCleaner:
    def __init__(self, region='us-east-1', dry_run=False):
        self.region = region
        self.dry_run = dry_run
        self.s3 = boto3.client('s3', region_name=region)
        self.glue = boto3.client('glue', region_name=region)
        self.athena = boto3.client('athena', region_name=region)
        self.quicksight = boto3.client('quicksight', region_name=region)
        
        # Contadores
        self.deleted_count = {
            's3_objects': 0,
            's3_buckets': 0,
            'glue_tables': 0,
            'glue_databases': 0,
            'glue_crawlers': 0,
            'athena_workgroups': 0,
            'athena_queries': 0,
            'quicksight_datasets': 0
        }
    
    def print_action(self, action, resource, name):
        """Imprime la acción que se va a realizar"""
        prefix = "[DRY-RUN]" if self.dry_run else "[DELETE]"
        print(f"{prefix} {action}: {resource} -> {name}")
    
    def delete_s3_bucket_contents(self, bucket_name):
        """Vacía todo el contenido de un bucket S3"""
        print(f"\n{'='*60}")
        print(f"Limpiando bucket S3: {bucket_name}")
        print(f"{'='*60}")
        
        try:
            # Verificar que el bucket existe
            self.s3.head_bucket(Bucket=bucket_name)
            
            # Listar y eliminar todos los objetos
            paginator = self.s3.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name)
            
            for page in pages:
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    self.print_action("Eliminando objeto", "S3", obj['Key'])
                    if not self.dry_run:
                        self.s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
                    self.deleted_count['s3_objects'] += 1
            
            # Eliminar versiones si hay versionado
            try:
                paginator = self.s3.get_paginator('list_object_versions')
                pages = paginator.paginate(Bucket=bucket_name)
                
                for page in pages:
                    # Eliminar versiones
                    if 'Versions' in page:
                        for version in page['Versions']:
                            self.print_action("Eliminando versión", "S3", 
                                            f"{version['Key']} (v{version['VersionId']})")
                            if not self.dry_run:
                                self.s3.delete_object(
                                    Bucket=bucket_name,
                                    Key=version['Key'],
                                    VersionId=version['VersionId']
                                )
                    
                    # Eliminar delete markers
                    if 'DeleteMarkers' in page:
                        for marker in page['DeleteMarkers']:
                            self.print_action("Eliminando delete marker", "S3",
                                            f"{marker['Key']}")
                            if not self.dry_run:
                                self.s3.delete_object(
                                    Bucket=bucket_name,
                                    Key=marker['Key'],
                                    VersionId=marker['VersionId']
                                )
            except ClientError:
                pass  # No hay versionado, continuar
            
            print(f"✅ Objetos eliminados del bucket: {self.deleted_count['s3_objects']}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f"⚠️  Bucket {bucket_name} no existe")
            else:
                print(f"❌ Error al limpiar bucket: {e}")
    
    def delete_s3_bucket(self, bucket_name):
        """Elimina el bucket S3 (debe estar vacío)"""
        try:
            self.print_action("Eliminando bucket", "S3", bucket_name)
            if not self.dry_run:
                self.s3.delete_bucket(Bucket=bucket_name)
            self.deleted_count['s3_buckets'] += 1
            print(f"✅ Bucket eliminado: {bucket_name}")
        except ClientError as e:
            print(f"❌ Error al eliminar bucket: {e}")
    
    def delete_glue_tables(self, database_name):
        """Elimina todas las tablas de una base de datos Glue"""
        print(f"\n{'='*60}")
        print(f"Eliminando tablas de Glue en: {database_name}")
        print(f"{'='*60}")
        
        try:
            # Listar todas las tablas
            paginator = self.glue.get_paginator('get_tables')
            pages = paginator.paginate(DatabaseName=database_name)
            
            for page in pages:
                for table in page['TableList']:
                    table_name = table['Name']
                    self.print_action("Eliminando tabla", "Glue", table_name)
                    if not self.dry_run:
                        self.glue.delete_table(
                            DatabaseName=database_name,
                            Name=table_name
                        )
                    self.deleted_count['glue_tables'] += 1
            
            print(f"✅ Tablas eliminadas: {self.deleted_count['glue_tables']}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityNotFoundException':
                print(f"⚠️  Base de datos {database_name} no existe")
            else:
                print(f"❌ Error al eliminar tablas: {e}")
    
    def delete_glue_database(self, database_name):
        """Elimina la base de datos Glue"""
        try:
            self.print_action("Eliminando database", "Glue", database_name)
            if not self.dry_run:
                self.glue.delete_database(Name=database_name)
            self.deleted_count['glue_databases'] += 1
            print(f"✅ Base de datos eliminada: {database_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityNotFoundException':
                print(f"⚠️  Base de datos {database_name} no existe")
            else:
                print(f"❌ Error al eliminar database: {e}")
    
    def delete_glue_crawlers(self, prefix=None):
        """Elimina crawlers de Glue (opcionalmente filtrando por prefijo)"""
        print(f"\n{'='*60}")
        print(f"Eliminando crawlers de Glue")
        print(f"{'='*60}")
        
        try:
            # Listar crawlers
            paginator = self.glue.get_paginator('get_crawlers')
            pages = paginator.paginate()
            
            for page in pages:
                for crawler in page['Crawlers']:
                    crawler_name = crawler['Name']
                    
                    # Filtrar por prefijo si se especifica
                    if prefix and not crawler_name.startswith(prefix):
                        continue
                    
                    self.print_action("Eliminando crawler", "Glue", crawler_name)
                    if not self.dry_run:
                        # Detener crawler si está corriendo
                        try:
                            self.glue.stop_crawler(Name=crawler_name)
                            print(f"  ⏸️  Deteniendo crawler primero...")
                        except ClientError:
                            pass  # Ya está detenido
                        
                        self.glue.delete_crawler(Name=crawler_name)
                    self.deleted_count['glue_crawlers'] += 1
            
            print(f"✅ Crawlers eliminados: {self.deleted_count['glue_crawlers']}")
            
        except ClientError as e:
            print(f"❌ Error al eliminar crawlers: {e}")
    
    def delete_athena_named_queries(self, prefix=None):
        """Elimina named queries guardadas en Athena"""
        print(f"\n{'='*60}")
        print(f"Eliminando named queries de Athena")
        print(f"{'='*60}")
        
        try:
            # Listar named queries
            paginator = self.athena.get_paginator('list_named_queries')
            pages = paginator.paginate()
            
            for page in pages:
                for query_id in page['NamedQueryIds']:
                    # Obtener detalles de la query
                    response = self.athena.get_named_query(NamedQueryId=query_id)
                    query_name = response['NamedQuery']['Name']
                    
                    # Filtrar por prefijo si se especifica
                    if prefix and not query_name.startswith(prefix):
                        continue
                    
                    self.print_action("Eliminando named query", "Athena", query_name)
                    if not self.dry_run:
                        self.athena.delete_named_query(NamedQueryId=query_id)
                    self.deleted_count['athena_queries'] += 1
            
            print(f"✅ Named queries eliminadas: {self.deleted_count['athena_queries']}")
            
        except ClientError as e:
            print(f"❌ Error al eliminar named queries: {e}")
    
    def cleanup_quicksight_datasets(self, aws_account_id, prefix=None):
        """Elimina datasets de QuickSight"""
        print(f"\n{'='*60}")
        print(f"Eliminando datasets de QuickSight")
        print(f"{'='*60}")
        
        try:
            # Listar datasets
            response = self.quicksight.list_data_sets(AwsAccountId=aws_account_id)
            
            for dataset in response.get('DataSetSummaries', []):
                dataset_id = dataset['DataSetId']
                dataset_name = dataset['Name']
                
                # Filtrar por prefijo si se especifica
                if prefix and not dataset_name.startswith(prefix):
                    continue
                
                self.print_action("Eliminando dataset", "QuickSight", dataset_name)
                if not self.dry_run:
                    self.quicksight.delete_data_set(
                        AwsAccountId=aws_account_id,
                        DataSetId=dataset_id
                    )
                self.deleted_count['quicksight_datasets'] += 1
            
            print(f"✅ Datasets eliminados: {self.deleted_count['quicksight_datasets']}")
            
        except ClientError as e:
            print(f"⚠️  Error al eliminar datasets de QuickSight: {e}")
            print("   (Esto es normal si no has usado QuickSight)")
    
    def print_summary(self):
        """Imprime resumen de recursos eliminados"""
        print(f"\n{'='*60}")
        print("RESUMEN DE LIMPIEZA")
        print(f"{'='*60}")
        
        if self.dry_run:
            print("⚠️  MODO DRY-RUN: No se eliminó nada realmente\n")
        
        print(f"Objetos S3 eliminados:        {self.deleted_count['s3_objects']}")
        print(f"Buckets S3 eliminados:        {self.deleted_count['s3_buckets']}")
        print(f"Tablas Glue eliminadas:       {self.deleted_count['glue_tables']}")
        print(f"Databases Glue eliminadas:    {self.deleted_count['glue_databases']}")
        print(f"Crawlers Glue eliminados:     {self.deleted_count['glue_crawlers']}")
        print(f"Named queries Athena:         {self.deleted_count['athena_queries']}")
        print(f"Datasets QuickSight:          {self.deleted_count['quicksight_datasets']}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Limpia recursos AWS de la práctica de Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--bucket-name',
        required=True,
        help='Nombre del bucket S3 a limpiar (ej: practica-s3-raw-glue-athena-qs-tunombre)'
    )
    
    parser.add_argument(
        '--database-name',
        required=True,
        help='Nombre de la base de datos Glue (ej: practica_raw_db_tunombre)'
    )
    
    parser.add_argument(
        '--crawler-prefix',
        default='crawler_practica',
        help='Prefijo de los crawlers a eliminar (default: crawler_practica)'
    )
    
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='Región de AWS (default: us-east-1)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Modo prueba: muestra qué se eliminaría sin eliminarlo'
    )
    
    parser.add_argument(
        '--keep-bucket',
        action='store_true',
        help='Mantiene el bucket S3 (solo vacía su contenido)'
    )
    
    parser.add_argument(
        '--aws-account-id',
        help='ID de cuenta AWS (necesario solo para limpiar QuickSight)'
    )
    
    args = parser.parse_args()
    
    # Confirmación
    if not args.dry_run:
        print(f"\n⚠️  ADVERTENCIA: Vas a ELIMINAR los siguientes recursos:")
        print(f"   - Bucket S3: {args.bucket_name}")
        print(f"   - Base de datos Glue: {args.database_name}")
        print(f"   - Crawlers con prefijo: {args.crawler_prefix}")
        print(f"   - Región: {args.region}")
        print()
        
        confirm = input("¿Estás seguro? Escribe 'SI' para confirmar: ")
        if confirm != 'SI':
            print("❌ Cancelado por el usuario")
            sys.exit(0)
    
    # Crear cleaner
    cleaner = AWSCleaner(region=args.region, dry_run=args.dry_run)
    
    print(f"\n🧹 Iniciando limpieza de recursos AWS...")
    if args.dry_run:
        print("📋 MODO DRY-RUN: Solo se mostrarán las acciones sin ejecutarlas\n")
    
    # Ejecutar limpieza
    try:
        # 1. Limpiar S3
        cleaner.delete_s3_bucket_contents(args.bucket_name)
        
        if not args.keep_bucket:
            cleaner.delete_s3_bucket(args.bucket_name)
        else:
            print(f"ℹ️  Manteniendo bucket {args.bucket_name} (--keep-bucket activado)")
        
        # 2. Limpiar Glue
        cleaner.delete_glue_tables(args.database_name)
        cleaner.delete_glue_database(args.database_name)
        cleaner.delete_glue_crawlers(prefix=args.crawler_prefix)
        
        # 3. Limpiar Athena
        cleaner.delete_athena_named_queries(prefix='practica')
        
        # 4. Limpiar QuickSight (si se proporciona account ID)
        if args.aws_account_id:
            cleaner.cleanup_quicksight_datasets(
                aws_account_id=args.aws_account_id,
                prefix='ds_sales'
            )
        
        # Resumen
        cleaner.print_summary()
        
        if args.dry_run:
            print("💡 Ejecuta sin --dry-run para eliminar realmente los recursos")
        else:
            print("✅ ¡Limpieza completada!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Limpieza interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error durante la limpieza: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()