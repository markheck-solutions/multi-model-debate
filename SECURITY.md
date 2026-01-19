# Security Policy

## Reporting Issues

Report security issues via GitHub Issues.

## Scope

This tool runs local CLI commands to invoke AI models. It does not:
- Store credentials
- Make network requests (beyond what the model CLIs do)
- Execute arbitrary code from model responses

## Known Considerations

- Model CLI tools may have their own security policies
- Debate outputs are stored locally in `runs/` directories
- No data is sent anywhere except to the model CLIs you configure
