@echo off
REM Aufgerufen von schtasks 'Halo_Pro_Archiv_Update' alle 30 Min — siehe setup_archiv_schtasks.py
REM Output landet in Logs\halo_archiv_schtasks.log; Indexer-eigene Logs in Logs\halo_pro_archiv_index.log

D:\Anthropic_Claude\Programme\Python\python.exe D:\Anthropic_Claude\Halo_Pro\Scripts\halo_pro_archiv_index.py update >> D:\Anthropic_Claude\Halo_Pro\Logs\halo_archiv_schtasks.log 2>&1
exit /b %ERRORLEVEL%
