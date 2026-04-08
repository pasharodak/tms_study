# Full run: start stack, populate DB, train model, then show how to request recommendations.
# Run from project root: .\run.ps1

Set-Location $PSScriptRoot

Write-Host "1. Starting containers (db + app)..." -ForegroundColor Cyan
docker-compose up -d --build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n2. Waiting for DB to be ready..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

Write-Host "`n3. Populating database (db_populate container)..." -ForegroundColor Cyan
docker-compose run --rm db_populate
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n4. Training model..." -ForegroundColor Cyan
docker-compose run --rm app python -m app.model_pipeline
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n5. Restarting app to load artifacts..." -ForegroundColor Cyan
docker-compose restart app
Start-Sleep -Seconds 5

Write-Host "`nDone. Request top 10 recommendations (example):" -ForegroundColor Green
Write-Host 'Invoke-RestMethod -Method POST -Uri "http://localhost:8000/recommend" -ContentType "application/json" -Body ''{"movie_ids":[862,8844,31357],"top_n":10}''' -ForegroundColor Yellow
Write-Host "`nOr: GET http://localhost:8000/health  |  Docs: http://localhost:8000/docs" -ForegroundColor Gray
