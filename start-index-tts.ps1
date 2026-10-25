param([string]$RuntimeRoot='D:\AI-Runtime\shishi-indextts')
$ErrorActionPreference='Stop'
$taskSource=Join-Path $RuntimeRoot 'sources\index-tts-minimal'
$taskPython=Join-Path $RuntimeRoot 'venv-reuse\Scripts\python.exe'
$taskModels=Join-Path $RuntimeRoot 'models\IndexTTS-2.5'
$taskReference=Join-Path $RuntimeRoot 'voices\voice_01.wav'
$taskBridge=Join-Path $PSScriptRoot 'scripts\index_tts_bridge.py'
$taskLogs=Join-Path $RuntimeRoot 'logs'
foreach($taskPath in @($taskPython,(Join-Path $taskModels 'config.yaml'),(Join-Path $taskModels 'gpt.pth'),(Join-Path $taskModels 'codec.pth'),(Join-Path $taskModels 's2mel.pth'),(Join-Path $taskModels 'hf_cache\w2v-bert-2.0\model.safetensors'),(Join-Path $taskModels 'hf_cache\bigvgan\bigvgan_generator.pt'),(Join-Path $taskModels 'hf_cache\campplus_cn_common.bin'),$taskReference,$taskBridge)){
 if(-not (Test-Path -LiteralPath $taskPath)){throw "IndexTTS resource missing: $taskPath"}
}
New-Item -ItemType Directory -Path $taskLogs -Force | Out-Null
$taskPidFile=Join-Path $taskLogs 'bridge.pid'
if(Test-Path -LiteralPath $taskPidFile){
 $taskPreviousPid=0
 if([int]::TryParse((Get-Content -LiteralPath $taskPidFile -Raw).Trim(),[ref]$taskPreviousPid)){
  $taskPrevious=Get-CimInstance Win32_Process -Filter ('ProcessId='+$taskPreviousPid) -ErrorAction SilentlyContinue
  if($taskPrevious -and $taskPrevious.CommandLine -like ('*'+$taskBridge+'*')){Write-Output 'IndexTTS already started or loading.';exit 0}
 }
}
$env:HF_HOME=Join-Path $RuntimeRoot 'cache\huggingface'
$env:MODELSCOPE_CACHE=Join-Path $RuntimeRoot 'cache\modelscope'
$env:PYTHONUTF8='1'
$taskCudaLibraries='D:\AI\conda\envs\digital-human\Library\bin'
if(Test-Path -LiteralPath $taskCudaLibraries){$env:PATH=$taskCudaLibraries+';'+$env:PATH}
$taskFfmpeg='D:\ffmpeg\ffmpeg-2026-03-09-git-9b7439c31b-essentials_build\bin'
if(Test-Path -LiteralPath $taskFfmpeg){$env:PATH=$taskFfmpeg+';'+$env:PATH}
$taskArguments=@('-u',('"'+$taskBridge+'"'),'--repo',('"'+$taskSource+'"'),'--model-dir',('"'+$taskModels+'"'),'--reference',('"'+$taskReference+'"'),'--cache',('"'+(Join-Path $RuntimeRoot 'audio-cache')+'"'),'--version','2.5','--port','9880')
$taskProcess=Start-Process -FilePath $taskPython -ArgumentList $taskArguments -WorkingDirectory $taskSource -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskLogs 'stdout.log') -RedirectStandardError (Join-Path $taskLogs 'stderr.log') -PassThru
Set-Content -LiteralPath $taskPidFile -Value $taskProcess.Id
Write-Output 'IndexTTS launched. Wait for model loading, then check service readiness.'
