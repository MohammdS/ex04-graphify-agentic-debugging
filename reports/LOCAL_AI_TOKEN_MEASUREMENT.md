# Local AI Token Measurement

Use this when you want real token usage from your own local model instead of the
estimated comparison.

## 1. Start a local OpenAI-compatible server

Examples:

Ollama:

```powershell
ollama pull llama3.1
ollama serve
```

Then use:

```powershell
$env:OPENAI_BASE_URL = "http://localhost:11434/v1"
$env:OPENAI_API_KEY = "local-ai"
$env:OPENAI_MODEL = "llama3.1"
```

LM Studio:

1. Start the local server from LM Studio.
2. Set `OPENAI_BASE_URL` to the server URL shown by LM Studio, usually
   `http://localhost:1234/v1`.
3. Set `OPENAI_MODEL` to the loaded model name.

## 2. Run the comparison

Easiest command:

```powershell
.\scripts\run_local_comparison.ps1 -Model qwen3:8b
```

Use any Ollama model name from `ollama list`:

```powershell
.\scripts\run_local_comparison.ps1 -Model llama3.2:3b
.\scripts\run_local_comparison.ps1 -Model qwen2.5:3b
.\scripts\run_local_comparison.ps1 -Model phi3:mini
```

Run the prompt comparison 10 times and report averages:

```powershell
.\scripts\run_local_comparison.ps1 -Model qwen3:8b -Runs 10
```

Single-prompt controlled trial:

```powershell
python agent\compare_token_usage.py
```

Or pass values directly:

```powershell
python agent\compare_token_usage.py --base-url http://localhost:11434/v1 --api-key local-ai --model llama3.1
```

Direct 10-run command:

```powershell
python agent\compare_token_usage.py --base-url http://localhost:11434/v1 --api-key ollama --model qwen3:8b --runs 10
```

Agent-workflow trial:

```powershell
python agent\compare_agent_workflows.py --base-url http://localhost:11434/v1 --api-key ollama --model qwen3:8b
```

Faster local Qwen run:

```powershell
python agent\compare_agent_workflows.py --base-url http://localhost:11434/v1 --api-key ollama --model qwen3:8b --max-tokens 180 --timeout 180 --skip-verifier
```

Same run through the wrapper:

```powershell
.\scripts\run_local_comparison.ps1 -Mode workflow -Model qwen3:8b -MaxTokens 120 -Timeout 120 -SkipVerifier
```

Use this faster command if the default run takes too long. It still compares the
naive and Graphify-guided agent LLM calls, but it limits answer length and skips
running pytest twice inside the comparison. You can still run `python -m pytest
-q` separately.

## 3. Output files

The script writes:

- `data/measured-token-comparison.json`
- `reports/MEASURED_TOKEN_COMPARISON.md`

The agent-workflow trial writes:

- `data/measured-agent-workflow-comparison.json`
- `reports/MEASURED_AGENT_WORKFLOW_COMPARISON.md`

Use those files as the real measured evidence in the final submission.

Both outputs also record:

- `diagnosis_success`: whether the response identified the mutable/default
  shared-list root cause.
- `fix_success`: whether the response proposed the `None` sentinel fix.
- `success`: true only when both diagnosis and fix criteria pass.

The script does not auto-apply two generated patches. It evaluates whether each
run produced the correct debugging answer and patch plan, then the repository's
actual fixed code is verified separately with `python -m pytest -q`.

## Notes

Some local servers return `prompt_tokens`, `completion_tokens`, and
`total_tokens`. Others omit usage. If usage is missing, the script clearly marks
`usage_source` as `estimated_prompt_only` and still records a consistent prompt
size estimate.
