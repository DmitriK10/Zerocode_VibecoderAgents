#!/bin/bash
# update_container.sh - обновление контейнера с проверкой

CONTAINER_NAME="crewai-bot"
IMAGE_NAME="dmitriiek/crewai-telegram-bot:latest"

echo "$(date): Начинаем обновление контейнера $CONTAINER_NAME"

# Останавливаем и удаляем старый контейнер
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Pull нового образа с проверкой
echo "$(date): Pull образа $IMAGE_NAME"
if ! docker pull $IMAGE_NAME; then
    echo "$(date): ОШИБКА: не удалось скачать образ $IMAGE_NAME"
    exit 1
fi

# Запускаем новый контейнер
echo "$(date): Запуск нового контейнера $CONTAINER_NAME"
if ! docker run -d --name $CONTAINER_NAME --restart unless-stopped --env-file /root/.env $IMAGE_NAME; then
    echo "$(date): ОШИБКА: не удалось запустить контейнер"
    exit 1
fi

echo "$(date): Контейнер успешно обновлён"