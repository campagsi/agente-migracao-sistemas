# Fluxo de perguntas para o “planejamento T6”

Você pediu um fluxo de perguntas para rodar a migração usando o planejamento T6. A ideia é ter um “roteiro” de prompts para conversar com o agente.

Sugestão de fluxo:

## Carregar contexto geral do T6

“Agente, use consultar_documentacao para resumir o planejamento T6 da migração de Certidão Imobiliária. Liste objetivos, escopo e principais telas/endpoints envolvidos.”

## Listar tarefas macro do T6

“Com base na documentação do T6, liste as tarefas técnicas principais (frontend e backend) que ainda estão pendentes ou em andamento.”

## Focar em um caso de uso / tela específica

“Dentro do planejamento T6, qual é o primeiro caso de uso/tela que você recomenda atacar agora? Use consultar_documentacao e me traga um resumo dessa tela e do fluxo.”

## Mapear endpoints e integrações

“Para essa tela/caso de uso do T6, quais endpoints do backend atual e do legado estão envolvidos? Liste alias, pacotes Oracle e funções conforme documentado em siatu-endpoints.”

## Levantar arquivos Vue 2 e Vue 3 relevantes

“Use buscar_arquivos e ler_arquivo para localizar os componentes Vue 2 dessa funcionalidade no frontend legado e me mostrar o que é mais importante do fluxo (rotas, services, componentes).”

## Planejar a migração da tela

“Com base nos arquivos do Vue 2 e no padrão do Vue 3 atual, monte um plano passo a passo para migrar essa tela no contexto do T6. Registre esse plano em docs/todo.md usando escrever_arquivo.”

## Planejar/validar endpoints no NestJS

“Verifique na documentação do T6 e em siatu-endpoints se todos os endpoints necessários já existem no backend atual. Se não existirem, liste quais endpoints novos precisam ser criados em NestJS.”

## Gerar/ajustar código (sob demanda)

“Gere uma proposta de implementação para o endpoint X no backend atual (NestJS), seguindo o padrão do projeto, mas não escreva no arquivo ainda. Quero revisar primeiro.”

## Registrar arquivos alterados

“Atualize docs/arquivos_alterados.md com a lista de arquivos que precisamos alterar para concluir esta etapa do T6.”

## Fechar o ciclo daquele pedaço do T6

“Faça um resumo do que foi decidido e do que falta fazer para concluir esta parte do planejamento T6, e registre em docs/execucoes/ usando escrever_arquivo.”
