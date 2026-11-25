# Cloudflare Workers Free + D1 — sem Render

Esta ponte usa os mesmos endpoints do Studio atual. Não requer outro `.rbxlx`.

1. Crie uma conta Cloudflare no Workers Free e um subdomínio `workers.dev`. Dentro desta pasta, rode `npx wrangler login`, depois `npx wrangler d1 create bloodyray-jobs`. Copie o `database_id` retornado para `wrangler.toml`.
2. Rode `npx wrangler d1 execute bloodyray-jobs --remote --file=schema.sql` e `npx wrangler deploy`. Anote a URL HTTPS sem rota. `/healthz` deve responder `{"status":"ok"}`.
3. Configure `npx wrangler secret put GITHUB_TOKEN`, `npx wrangler secret put STUDIO_BRIDGE_KEY` e `npx wrangler secret put WINDOWS_DELIVERY_KEY`. O token precisa de Actions leitura/escrita só no repo. Gere duas chaves independentes com 32 caracteres ou mais. Não cole chaves no código ou chat.
4. Copie o `bloodyray-windows.yml` deste pacote para `.github/workflows/bloodyray-windows.yml` do repo `deathzoom0-ops/RDP`. Em Settings → Secrets and variables → Actions, crie a variável `BLOODYRAY_WORKER_URL` (a URL HTTPS) e o Secret `WINDOWS_DELIVERY_KEY` (mesmo valor do Worker). Esta variante envia a entrega ao D1 diretamente.
5. No Roblox, ative Allow HTTP Requests, ajuste `WindowsBridgeURL` para a URL Cloudflare e armazene o mesmo `STUDIO_BRIDGE_KEY` como Secret `STUDIO_WINDOWS_BRIDGE_KEY`, restrito ao domínio. Use a build já integrada e teste “Crie uma torre na VM”.

Se `/healthz` funcionar e não aparecer um job, investigue o token/permissões do GitHub e a presença do workflow na main. Se o job rodar mas não entregar, confira a etapa Deliver model e o segredo/URL. Status é `queued` até chegar a entrega ou até expirar após 15 minutos.

Não configure a chave Gemini nesta ponte. O protótipo gráfico separado mantém a configuração Gemini existente. O Worker executa apenas tarefas definidas e não dá controle gráfico ao chat.
