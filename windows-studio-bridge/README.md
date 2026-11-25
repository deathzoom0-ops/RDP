# Ponte Windows do BloodyRay Studio (MVP)

1. Copie `.github/workflows/bloodyray-windows.yml` para a branch `main` de `deathzoom0-ops/RDP`. O workflow é separado do RDP e não usa Tailscale, senhas nem o `.bat`. Permita que ele rode em Actions.
2. Implante este diretório em um serviço com HTTPS: `pip install -r requirements.txt`, depois `gunicorn -w 1 --threads 4 -b 0.0.0.0:8080 bridge:app`. Configure `GITHUB_TOKEN` com permissões de Actions leitura e escrita somente no repo, e `STUDIO_BRIDGE_KEY` com um valor aleatório de pelo menos 32 caracteres. `GITHUB_REPO` é opcional. Não compartilhe segredos no chat, no código ou nos logs.
3. Na experiência Roblox, ative HTTP Requests, crie um Secret `STUDIO_WINDOWS_BRIDGE_KEY` com o mesmo valor da ponte e restrinja-o ao domínio da ponte. Em `ServerScriptService > BloodyRayServer`, adicione o atributo string `WindowsBridgeURL` com `https://seu-dominio` (sem caminho).
4. Abra o chat RayCore do BloodyRay e peça “Crie uma torre na VM” ou “Gere um arco no Windows”. O editor consulta automaticamente por até 40 tentativas; se necessário, pergunte “Qual o status da VM?”. Ao ficar pronto, importa o `.rbxmx` na cena. Pedidos como “Instale na VM” são identificados, mas bloqueados como não suportados. Em edição compartilhada, a peça inserida na cena é visível a outros editores, mas o ticket é vinculado a quem pediu.

Escopo: três presets permitidos, uma tarefa ativa por jogador, fila limitada, tickets e entregas em SQLite com expiração de 15 min. Não há desktop persistente, comando arbitrário, RDP nem execução de código enviado pelo jogador. Monte um volume persistente e configure `BRIDGE_DB=/data/jobs.sqlite3` (gravável pelo usuário da ponte) para manter os tickets em reinicializações. Isso não preserva a máquina do GitHub nem a sessão Roblox. Para máxima segurança em produção, restrinja quem pode chamar o recurso, revise o workflow e fixe dependências por versões verificadas.

## Teste do Blender no runner

No chat, peça **Crie um cubo chanfrado no Blender da VM**. O job baixa o Blender portátil oficial 4.3.2, verifica SHA-256, executa a operação em modo headless e devolve um OBJ triangulado. A instalação solicitada por texto livre continua indisponível. O download acontece dentro do próprio job e não persiste no próximo runner. Pode demorar vários minutos.

A ponte também pode ser construída com `docker build -t bloodyray-bridge .`; forneça os segredos pela configuração do host e exponha o serviço somente por HTTPS. Não publique um endpoint sem autenticação.
