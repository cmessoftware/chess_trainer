Write-Host "🚀 Construyendo imagen chess_trainer..."
docker-compose build chess_trainer

Write-Host "🚀 Construyendo imagen notebooks..."
docker-compose build notebooks

Write-Host "✅ Imágenes construidas, levantando contenedores..."
docker-compose up -d chess_trainer notebooks

Write-Host "🧹 Limpiando imágenes antiguas no utilizadas..."
docker image prune -a -f

Write-Host "🏁 Contenedores activos:"
docker ps
