# PostToolUse hook: formats the edited file with StyLua if it is a .lua/.luau file.
# Never blocks Claude: always exits 0.
try {
	$payload = [Console]::In.ReadToEnd() | ConvertFrom-Json
	$file = $payload.tool_input.file_path
	if ($file -and $file -match '\.luau?$' -and (Test-Path -LiteralPath $file)) {
		$projectDir = if ($env:CLAUDE_PROJECT_DIR) { $env:CLAUDE_PROJECT_DIR } else { $payload.cwd }
		if ($projectDir) { Set-Location -LiteralPath $projectDir }
		stylua --search-parent-directories -- $file 2>&1 | Out-Null
	}
} catch {}
exit 0
