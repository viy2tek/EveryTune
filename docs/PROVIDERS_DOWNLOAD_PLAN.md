# Provedores e arquivos — 0.4

Pedido: separar streaming pago/freemium de comunidade; consultar ambos, um grupo ou fontes individuais. Descobrir arquivos oferecidos e permitir download e ZIP dos arquivos escolhidos. Confirmado: seleção manual antes de gerar ZIP.

Implementação: manter o motor federado. Grupo de provedor é independente de categoria, credenciais e permissão de download. Restaurar no catálogo os adaptadores Spotify, Apple Music e SoundCloud com credenciais próprias, sem comprar acesso nem cobrar tokens. Filtrar o grupo no backend e na interface; preservar as marcações ao trocar foco.

Downloads são descobertos sob demanda a partir de referências emitidas pelo servidor para os resultados. Internet Archive e Commons usam metadados oficiais; Jamendo e SoundCloud dependem dos campos de autorização da origem. Audius só pode oferecer download quando todos os indicadores necessários permitem. Spotify/Apple/Deezer/YouTube não viram download exportável por terem assinatura.

Nas páginas da comunidade, identificar links explícitos de arquivos e páginas de download/espelhos, com extensão, tamanho conhecido e evidência. Mapeamento CSS configurável por fonte. Não executar JavaScript ou extrair streams protegidos. Links externos permanecem externos quando exigem interação.

Transferências usam transporte separado do cliente de metadados: HTTPS público com DNS pinado em cada redirecionamento, sem repassar autenticação a outro host, limite de tamanho e concorrência. Arquivos são preparados temporariamente e enviados como anexo. ZIP usa apenas os IDs de opções emitidas pelo servidor, nomes seguros e arquivos selecionados; não extrai pacotes. Progresso e cancelamento visíveis. Temporários são removidos por expiração/encerramento.

Verificar grupos/seleção, migração de perfis, permissões, parse de arquivos e espelhos, bloqueio de SSRF/redirecionamentos, limites, erros, cancelamento, conteúdo e nomes do ZIP com bytes sintéticos. Validar metadados reais sem baixar música de terceiros automaticamente. Testar interface e executável Windows.

Verificado: 173 testes, Edge em desktop/móvel, troca de grupos mantendo seleção, ZIP real contendo somente dois XML públicos e perfis. Downloads com conta/autenticação própria e arquivos grandes continuam sem validação ao vivo. ZIP atual reúne escolhas de um item/álbum por preparação; cesta entre vários resultados não faz parte desta entrega.
