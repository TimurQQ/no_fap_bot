import boto3
import os
import json
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError
from config.config import S3_ENABLED, S3_BUCKET_NAME, S3_ACCESS_KEY, S3_SECRET_KEY, S3_REGION, S3_ENDPOINT
from logger import noFapLogger


class S3BackupManager:
    """Менеджер для резервного копирования базы данных в S3."""
    
    def __init__(self):
        self.enabled = S3_ENABLED
        self.bucket_name = S3_BUCKET_NAME
        self.s3_client = None
        
        if self.enabled:
            try:
                # Проверяем что S3_ENDPOINT задан
                if not S3_ENDPOINT:
                    raise ValueError(
                        "S3_ENDPOINT is required but not set in .env file. "
                        "Please set S3_ENDPOINT to your S3-compatible storage endpoint "
                        "(e.g., https://storage.yandexcloud.net for Yandex Cloud)"
                    )
                
                # Используем заданный endpoint
                endpoint_url = S3_ENDPOINT
                noFapLogger.info(f"Using S3 endpoint: {endpoint_url}")
                
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=S3_ACCESS_KEY,
                    aws_secret_access_key=S3_SECRET_KEY,
                    region_name=S3_REGION,
                    endpoint_url=endpoint_url
                )
                noFapLogger.info("S3 backup manager initialized successfully")
            except ValueError:
                # Пробрасываем ValueError (отсутствие S3_ENDPOINT) дальше
                raise
            except Exception as e:
                noFapLogger.error(f"Failed to initialize S3 client: {e}")
                self.enabled = False
    
    def upload_database_backup(self, database_file_path: str) -> bool:
        """
        Загружает файл базы данных в S3.
        
        Args:
            database_file_path: Путь к файлу базы данных
            
        Returns:
            bool: True если загрузка успешна, False в противном случае
        """
        if not self.enabled:
            noFapLogger.error("S3 backup is disabled, skipping upload")
            return False
            
        if not os.path.exists(database_file_path):
            noFapLogger.error(f"Database file not found: {database_file_path}")
            return False
            
        try:
            # Создаем имя файла с временной меткой
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            s3_key = f"database_backups/all_scores_saved_{timestamp}.json"
            
            # Загружаем файл в S3
            self.s3_client.upload_file(
                database_file_path,
                self.bucket_name,
                s3_key
            )
            
            noFapLogger.info(f"Database backup uploaded successfully to S3: {s3_key}")
            
            # Также сохраняем как latest backup
            latest_key = "database_backups/all_scores_saved_latest.json"
            self.s3_client.upload_file(
                database_file_path,
                self.bucket_name,
                latest_key
            )
            
            noFapLogger.info(f"Latest backup updated: {latest_key}")
            return True
            
        except FileNotFoundError:
            noFapLogger.error(f"Database file not found: {database_file_path}")
            return False
            
        except NoCredentialsError:
            noFapLogger.error("S3 credentials not found or invalid")
            return False
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                noFapLogger.error(f"S3 bucket '{self.bucket_name}' does not exist")
            elif error_code == 'AccessDenied':
                noFapLogger.error("Access denied to S3 bucket - check permissions")
            else:
                noFapLogger.error(f"S3 ClientError: {e}")
            return False
            
        except Exception as e:
            noFapLogger.error(f"Unexpected error during S3 upload: {e}")
            return False
    
    def download_latest_backup(self, download_path: str) -> dict:
        """
        Скачивает последний бэкап из S3 с информацией о ревизии.
        
        Args:
            download_path: Путь для сохранения скачанного файла
            
        Returns:
            dict: Информация о скачанном бэкапе или пустой словарь при ошибке
        """
        if not self.enabled:
            noFapLogger.error("S3 backup is disabled, cannot download")
            return {}
            
        try:
            latest_key = "database_backups/all_scores_saved_latest.json"
            
            # Получаем метаданные объекта
            head_response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=latest_key
            )
            
            # Скачиваем файл
            self.s3_client.download_file(
                self.bucket_name,
                latest_key,
                download_path
            )
            
            # Получаем информацию о содержимом для ревизии
            backup_info = {
                'source': 'S3',
                'key': latest_key,
                'size': head_response['ContentLength'],
                'last_modified': head_response['LastModified'],
                'etag': head_response['ETag'].strip('"'),
                'download_path': download_path
            }
            
            # Читаем содержимое для получения статистики
            try:
                with open(download_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    backup_info['users_count'] = len(data) if isinstance(data, dict) else 0
                    backup_info['content_preview'] = str(data)[:200] + "..." if len(str(data)) > 200 else str(data)
            except Exception as e:
                noFapLogger.error(f"Could not read backup content for stats: {e}")
                backup_info['users_count'] = 'unknown'
                backup_info['content_preview'] = 'unavailable'
            
            noFapLogger.info(f"Latest backup downloaded from S3 to: {download_path}")
            return backup_info
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                noFapLogger.error("No backup found in S3")
            else:
                noFapLogger.error(f"S3 ClientError during download: {e}")
            return {}
            
        except Exception as e:
            noFapLogger.error(f"Unexpected error during S3 download: {e}")
            return {}
    
    def list_backups(self) -> list:
        """
        Возвращает список всех бэкапов в S3.
        
        Returns:
            list: Список объектов бэкапов
        """
        if not self.enabled:
            return []
            
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="database_backups/"
            )
            
            if 'Contents' in response:
                backups = []
                for obj in response['Contents']:
                    backups.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified']
                    })
                return sorted(backups, key=lambda x: x['last_modified'], reverse=True)
            
            return []
            
        except Exception as e:
            noFapLogger.error(f"Error listing S3 backups: {e}")
            return []


# Создаем глобальный экземпляр менеджера
s3_backup_manager = S3BackupManager()


def restore_database_from_s3(database_path: str) -> None:
    """
    Восстанавливает базу данных из S3 с детальным логированием ревизии.
    
    Args:
        database_path: Путь для сохранения восстановленной базы данных
        
    Raises:
        RuntimeError: Если восстановление не удалось
    """
    noFapLogger.info("🔄 Starting database restoration from S3...")
    
    # Создаем директорию если её нет
    os.makedirs(os.path.dirname(database_path), exist_ok=True)
    
    backup_info = s3_backup_manager.download_latest_backup(database_path)
    
    if backup_info:
        # Логируем детальную информацию о восстановленной БД
        noFapLogger.info("=" * 60)
        noFapLogger.info("📋 DATABASE RESTORATION REPORT")
        noFapLogger.info("=" * 60)
        noFapLogger.info(f"🔗 Source: {backup_info['source']}")
        noFapLogger.info(f"🗂️  S3 Key: {backup_info['key']}")
        noFapLogger.info(f"📊 File Size: {backup_info['size']} bytes")
        noFapLogger.info(f"⏰ Last Modified: {backup_info['last_modified']}")
        noFapLogger.info(f"🔐 ETag (Revision): {backup_info['etag']}")
        noFapLogger.info(f"👥 Users Count: {backup_info['users_count']}")
        noFapLogger.info(f"💾 Restored to: {backup_info['download_path']}")
        noFapLogger.info("=" * 60)
        noFapLogger.info("✅ Database successfully restored from S3 backup!")
    else:
        raise RuntimeError(
            f"❌ CRITICAL ERROR: Could not restore database from S3 backup. "
            f"No backup found or S3 is not accessible. "
            f"Please check S3 configuration and ensure backup exists."
        )


def backup_database_to_s3():
    """
    Функция для планировщика - создает бэкап базы данных в S3.
    """
    database_path = os.path.join("storage", "all_scores_saved.json")
    
    if s3_backup_manager.upload_database_backup(database_path):
        noFapLogger.info("Scheduled database backup to S3 completed successfully")
    else:
        noFapLogger.error("Scheduled database backup to S3 failed")
