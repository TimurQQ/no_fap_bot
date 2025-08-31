import boto3
import os
import json
import zipfile
import tempfile
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
            noFapLogger.warning("S3 backup is disabled, skipping upload")
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
            noFapLogger.warning("S3 backup is disabled, cannot download")
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
    
    def upload_folder_as_zip(self, folder_path: str, s3_key: str) -> dict:
        """
        Загружает папку в S3 как ZIP архив.
        
        Args:
            folder_path: Путь к папке для архивирования
            s3_key: Ключ в S3 для сохранения архива
            
        Returns:
            dict: Информация о загруженном архиве или пустой словарь при ошибке
        """
        if not self.enabled:
            noFapLogger.warning("S3 backup is disabled, cannot upload folder")
            return {}
            
        if not os.path.exists(folder_path):
            noFapLogger.error(f"Folder not found: {folder_path}")
            return {}
            
        try:
            # Создаем временный ZIP файл
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
                temp_zip_path = temp_zip.name
            
            # Архивируем папку
            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Сохраняем относительный путь в архиве
                        arcname = os.path.relpath(file_path, folder_path)
                        zipf.write(file_path, arcname)
            
            # Получаем информацию о созданном архиве
            zip_size = os.path.getsize(temp_zip_path)
            files_count = len([f for _, _, files in os.walk(folder_path) for f in files])
            
            # Загружаем в S3
            self.s3_client.upload_file(temp_zip_path, self.bucket_name, s3_key)
            
            # Удаляем временный файл
            os.unlink(temp_zip_path)
            
            upload_info = {
                'source_folder': folder_path,
                's3_key': s3_key,
                'zip_size': zip_size,
                'files_count': files_count,
                'upload_time': datetime.now()
            }
            
            noFapLogger.info(f"Folder uploaded to S3: {s3_key} ({files_count} files, {zip_size} bytes)")
            return upload_info
            
        except Exception as e:
            # Очищаем временный файл при ошибке
            if 'temp_zip_path' in locals() and os.path.exists(temp_zip_path):
                os.unlink(temp_zip_path)
            noFapLogger.error(f"Error uploading folder to S3: {e}")
            return {}
    
    def download_and_extract_zip(self, s3_key: str, extract_path: str) -> dict:
        """
        Скачивает ZIP архив из S3 и извлекает его содержимое.
        
        Args:
            s3_key: Ключ ZIP архива в S3
            extract_path: Путь для извлечения содержимого
            
        Returns:
            dict: Информация о скачанном архиве или пустой словарь при ошибке
        """
        if not self.enabled:
            noFapLogger.warning("S3 backup is disabled, cannot download")
            return {}
            
        try:
            # Создаем временный файл для скачивания
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
                temp_zip_path = temp_zip.name
            
            # Скачиваем архив из S3
            self.s3_client.download_file(self.bucket_name, s3_key, temp_zip_path)
            
            # Создаем директорию для извлечения
            os.makedirs(extract_path, exist_ok=True)
            
            # Извлекаем архив
            with zipfile.ZipFile(temp_zip_path, 'r') as zipf:
                zipf.extractall(extract_path)
                files_count = len(zipf.namelist())
            
            # Получаем размер архива
            zip_size = os.path.getsize(temp_zip_path)
            
            # Удаляем временный файл
            os.unlink(temp_zip_path)
            
            download_info = {
                's3_key': s3_key,
                'extract_path': extract_path,
                'zip_size': zip_size,
                'files_count': files_count,
                'download_time': datetime.now()
            }
            
            noFapLogger.info(f"Archive downloaded and extracted: {s3_key} -> {extract_path} ({files_count} files)")
            return download_info
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                noFapLogger.error(f"Archive not found in S3: {s3_key}")
            else:
                noFapLogger.error(f"S3 ClientError during download: {e}")
            return {}
        except Exception as e:
            # Очищаем временный файл при ошибке
            if 'temp_zip_path' in locals() and os.path.exists(temp_zip_path):
                os.unlink(temp_zip_path)
            noFapLogger.error(f"Error downloading archive from S3: {e}")
            return {}


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


def backup_memes_to_s3() -> None:
    """
    Создает бэкап папки с мемами в S3.
    
    Raises:
        RuntimeError: Если бэкап не удался
    """
    memes_folder = os.path.join("storage", "memes")
    
    if not os.path.exists(memes_folder):
        raise RuntimeError(f"Memes folder not found: {memes_folder}")
    
    # Создаем ключ с временной меткой
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    s3_key = f"memes_backups/memes_{timestamp}.zip"
    latest_key = "memes_backups/memes_latest.zip"
    
    # Загружаем архив с мемами
    upload_info = s3_backup_manager.upload_folder_as_zip(memes_folder, s3_key)
    
    if not upload_info:
        raise RuntimeError("Failed to upload memes backup to S3")
    
    # Также сохраняем как latest backup
    latest_info = s3_backup_manager.upload_folder_as_zip(memes_folder, latest_key)
    
    if not latest_info:
        noFapLogger.error("Failed to update latest memes backup")
    else:
        noFapLogger.info(f"Latest memes backup updated: {latest_key}")
    
    # Логируем детальную информацию
    noFapLogger.info("=" * 60)
    noFapLogger.info("📸 MEMES BACKUP REPORT")
    noFapLogger.info("=" * 60)
    noFapLogger.info(f"📁 Source Folder: {upload_info['source_folder']}")
    noFapLogger.info(f"☁️ S3 Key: {upload_info['s3_key']}")
    noFapLogger.info(f"📊 Archive Size: {upload_info['zip_size']} bytes")
    noFapLogger.info(f"🖼️ Files Count: {upload_info['files_count']} memes")
    noFapLogger.info(f"⏰ Upload Time: {upload_info['upload_time']}")
    noFapLogger.info("=" * 60)
    noFapLogger.info("✅ Memes backup completed successfully!")


def restore_memes_from_s3(memes_folder: str) -> None:
    """
    Восстанавливает папку с мемами из S3.
    
    Args:
        memes_folder: Путь к папке для восстановления мемов
        
    Raises:
        RuntimeError: Если восстановление не удалось
    """
    noFapLogger.info("🔄 Starting memes restoration from S3...")
    
    latest_key = "memes_backups/memes_latest.zip"
    
    # Скачиваем и извлекаем архив
    download_info = s3_backup_manager.download_and_extract_zip(latest_key, memes_folder)
    
    if not download_info:
        raise RuntimeError("Failed to restore memes from S3 backup")
    
    # Логируем детальную информацию
    noFapLogger.info("=" * 60)
    noFapLogger.info("📸 MEMES RESTORATION REPORT")
    noFapLogger.info("=" * 60)
    noFapLogger.info(f"☁️ S3 Key: {download_info['s3_key']}")
    noFapLogger.info(f"📁 Extract Path: {download_info['extract_path']}")
    noFapLogger.info(f"📊 Archive Size: {download_info['zip_size']} bytes")
    noFapLogger.info(f"🖼️ Files Count: {download_info['files_count']} memes")
    noFapLogger.info(f"⏰ Download Time: {download_info['download_time']}")
    noFapLogger.info("=" * 60)
    noFapLogger.info("✅ Memes successfully restored from S3 backup!")


def backup_database_to_s3():
    """
    Функция для планировщика - создает бэкап базы данных в S3.
    """
    database_path = os.path.join("storage", "all_scores_saved.json")
    
    if s3_backup_manager.upload_database_backup(database_path):
        noFapLogger.info("Scheduled database backup to S3 completed successfully")
    else:
        noFapLogger.error("Scheduled database backup to S3 failed")


def backup_all_to_s3():
    """
    Функция для планировщика - создает бэкап БД и мемов в S3.
    """
    try:
        # Бэкап базы данных
        backup_database_to_s3()
        
        # Бэкап мемов
        backup_memes_to_s3()
        
        noFapLogger.info("🎉 Complete backup (database + memes) to S3 completed successfully!")
        
    except Exception as e:
        noFapLogger.error(f"Complete backup to S3 failed: {e}")
