# Worker Windows para o agente externo

Este pacote contém um protótipo de agente local e não ativa RDP. Ele substitui o teste de infraestrutura do workflow antigo por uma verificação curta para uma VM Windows sob seu controle. Não usa Roblox.

1. Desative o workflow antigo. Se ele foi executado, remova o nó temporário do Tailscale e revogue chaves reutilizáveis expostas a esse ambiente. Nunca reutilize a senha publicada.
2. Em uma VM sua, instale o Tailscale e autentique a máquina na sua rede. Se precisar de RDP para administração, mantenha NLA ativa, use uma conta dedicada e limite o acesso pelas regras do Tailscale e do firewall. Não exponha 3389 à internet.
3. Use um repositório privado. Registre um runner Windows self-hosted com o rótulo `ai-sandbox`, restrito a esse repositório. Não aceite jobs de pull requests não confiáveis.
4. Copie `.github/workflows/validar-worker.yml` para o repositório e execute manualmente em Actions. O teste não instala nada, não solicita senha e não prolonga runners hospedados.
5. Próxima etapa: instalar o agente externo em uma sessão Windows interativa com conta padrão. O runner de CI pode estar numa sessão de serviço e não substitui o desktop do agente. A automação gráfica e o roteador estão no protótipo; checkpoint persistente ainda não está implementado.

## Protótipo de controle gráfico

Na sessão interativa da VM (não no serviço do runner), instale Python e rode:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe agent.py
```

Antes da última linha, configure no ambiente pelo menos uma chave: `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY` ou `GROQ_API_KEY`. Use armazenamento de segredos local; não grave chaves no repo. `AGENT_ROUTES` define a ordem `provedor:modelo,provedor:modelo`, usando modelos com visão e acesso na sua conta. Por exemplo, comece com um provedor e uma rota. O protótipo não foi ativado nem validado na sua VM. Use só desktop e dados de teste; as capturas saem da VM para o provedor. Instalações e elevação ficam com o operador neste protótipo.
