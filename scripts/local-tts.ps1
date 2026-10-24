param([string]$TextFile,[string]$OutputFile)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$taskSynth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
 $taskVoices = $taskSynth.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -like 'zh*' }
 if ($taskVoices.Count -gt 0) { $taskSynth.SelectVoice($taskVoices[0].VoiceInfo.Name) }
 $taskSynth.SetOutputToWaveFile($OutputFile)
 $taskSynth.Speak([IO.File]::ReadAllText($TextFile))
} finally { $taskSynth.Dispose() }
