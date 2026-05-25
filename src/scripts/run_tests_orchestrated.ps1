# Run orchestrated tests and save output
$ErrorActionPreference = 'Continue'
$pythonPath = "C:\Users\sergiosal\miniforge3\envs\chess_trainer\python.exe"

Write-Host "=== Running PlannerService Tests ===" -ForegroundColor Cyan
& $pythonPath -m pytest tests\ai_coach\orchestrated\test_planner_service.py -v --tb=short -x

Write-Host "`n=== Running ExecutorService Tests ===" -ForegroundColor Cyan  
& $pythonPath -m pytest tests\ai_coach\orchestrated\test_executor_service.py -v --tb=short -x

Write-Host "`n=== Running MemoryService Tests ===" -ForegroundColor Cyan
& $pythonPath -m pytest tests\ai_coach\orchestrated\test_memory_service.py -v --tb=short -x

Write-Host "`n=== Running Integration Tests ===" -ForegroundColor Cyan
& $pythonPath -m pytest tests\ai_coach\orchestrated\test_integration.py -v --tb=short -x

Write-Host "`n=== Test Summary ===" -ForegroundColor Green
& $pythonPath -m pytest tests\ai_coach\orchestrated\ --collect-only -q
