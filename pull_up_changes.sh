#!/usr/bin/env bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Starting deployment process...${NC}"

# 1. Обновляем код из репозитория
echo -e "${YELLOW}📥 Pulling latest changes from repository...${NC}"
git pull origin master

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to pull changes from repository${NC}"
    exit 1
fi

# 2. Останавливаем бота
echo -e "${YELLOW}🛑 Stopping bot process...${NC}"
pkill -f "no_fap.py"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Bot process stopped${NC}"
else
    echo -e "${YELLOW}⚠️  No running bot process found${NC}"
fi

# 3. Создаем локальные бэкапы
echo -e "${YELLOW}💾 Creating local backups...${NC}"

# Создаем директорию backup если её нет
mkdir -p backup

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

# Бэкап базы данных
if [ -f "storage/all_scores_saved.json" ]; then
    cp storage/all_scores_saved.json "backup/all_scores_saved_${TIMESTAMP}.json"
    cp storage/all_scores_saved.json "backup/all_scores_saved.json"
    echo -e "${GREEN}✅ Database backup: backup/all_scores_saved_${TIMESTAMP}.json${NC}"
else
    echo -e "${YELLOW}⚠️  Database file not found, skipping database backup${NC}"
fi

# Бэкап мемов
if [ -d "storage/memes" ]; then
    tar -czf "backup/memes_${TIMESTAMP}.tar.gz" -C storage memes
    tar -czf "backup/memes_latest.tar.gz" -C storage memes
    MEMES_COUNT=$(find storage/memes -type f | wc -l)
    echo -e "${GREEN}✅ Memes backup: backup/memes_${TIMESTAMP}.tar.gz (${MEMES_COUNT} files)${NC}"
else
    echo -e "${YELLOW}⚠️  Memes folder not found, skipping memes backup${NC}"
fi

# 4. Создаем S3 бэкап
echo -e "${YELLOW}☁️  Creating S3 backup...${NC}"

# Проверяем что .env файл существует
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found, skipping S3 backup${NC}"
else
    # Проверяем что S3 включен
    S3_ENABLED=$(grep "^S3_ENABLED=" .env | cut -d'=' -f2)
    if [ "$S3_ENABLED" = "true" ]; then
        poetry run python -c "
try:
    from src.utils.s3_backup import backup_all_to_s3
    backup_all_to_s3()
    print('✅ S3 backup (database + memes) completed successfully')
except Exception as e:
    print(f'❌ S3 backup failed: {e}')
    # Не останавливаем деплой если S3 бэкап не удался
"
    else
        echo -e "${YELLOW}⚠️  S3 backup disabled in .env, skipping S3 backup${NC}"
    fi
fi

# 5. Обновляем зависимости
echo -e "${YELLOW}📦 Installing/updating dependencies...${NC}"
poetry install

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi

# 6. Запускаем бота
echo -e "${YELLOW}🚀 Starting bot...${NC}"
poetry run python -B no_fap.py &

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Bot started successfully${NC}"
    echo -e "${BLUE}🎉 Deployment completed successfully!${NC}"
else
    echo -e "${RED}❌ Failed to start bot${NC}"
    exit 1
fi

# 7. Показываем статус
echo -e "${BLUE}📊 Deployment Summary:${NC}"
echo -e "  📥 Code updated: ${GREEN}✅${NC}"
echo -e "  💾 Local backups: ${GREEN}✅${NC} (database + memes)"
echo -e "  ☁️  S3 backup: ${GREEN}✅${NC} (database + memes)"
echo -e "  📦 Dependencies: ${GREEN}✅${NC}"
echo -e "  🚀 Bot started: ${GREEN}✅${NC}"
