@echo off
title Push Clean Build to Hugging Face Spaces
echo ====================================================================
echo   PUSHING CLEAN BUILD TO HUGGING FACE SPACES
echo   Space: https://huggingface.co/spaces/LeviYagami/cloud-file-deduplication
echo ====================================================================
echo.
echo If prompted for:
echo   - Username: LeviYagami
echo   - Password: Use your Hugging Face Access Token (from https://huggingface.co/settings/tokens)
echo.

git push hf hf-deploy:main --force

echo.
echo ====================================================================
echo Deployment initiated!
echo Check your Space: https://huggingface.co/spaces/LeviYagami/cloud-file-deduplication
echo ====================================================================
pause
