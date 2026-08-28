# Reavaliação humana cega

O desfecho principal do estudo (nível de compreensão do raciocínio probabilístico, escala N0–N4) foi reconstruído por reavaliação humana. A razão foram duas limitações apontadas na revisão por pares:

1. **Grupos avaliados de formas diferentes.** No desenho original, o grupo socrático era avaliado turno a turno por um classificador de IA; o expositivo, uma única vez, sobre uma explicação final.
2. **Nota de IA sem validação humana.** Ninguém verificou as classificações automáticas (risco de viés de "LLM-as-a-judge").

## 1. Rubrica usada (Quadro 2 do artigo)

| Nível | Rótulo | Critério |
|---|---|---|
| N0 | Sem justificativa | Nenhuma justificativa adequada ou demonstração consistente da cadeia causal. |
| N1 | Intuitivo incorreto | Resposta intuitiva, porém incorreta (ex.: tratar as duas portas restantes como equiprováveis). |
| N2 | Parcialmente correto | Raciocínio em parte correto, sem articulação completa da solução. |
| N3 | Correto sem demonstração causal | Conclusão correta (trocar é a estratégia superior), sem demonstrar a cadeia causal que a sustenta. |
| N4 | Correto com demonstração causal | Conclusão correta com demonstração explícita da cadeia causal: probabilidade inicial de 1/3 na porta escolhida e transferência dos 2/3 após o apresentador abrir uma porta. |

Critério-fonte: a mesma rubrica de `evaluate_expository_rubric` (ver `docs/prompts.md`, Seção 9), estendida para leitura humana do transcript completo no grupo socrático.

## 2. Amostra reavaliada

Todos os participantes com ao menos um turno registrado (n = 30: 12 do grupo socrático, 18 do expositivo), com ou sem nota de IA no desenho original. Isso amplia a cobertura em relação aos 25 participantes com `rubric_level` recuperável pela IA, incluindo quem nunca produziu uma explicação final que acionasse a avaliação automática.

## 3. Material apresentado a cada avaliador

- **Grupo expositivo:** a explicação final solicitada ao término da sessão.
- **Grupo socrático:** o transcript completo da sessão. Este grupo não gera uma explicação final isolada; a compreensão aparece ao longo do diálogo.

## 4. Como o cegamento foi feito

1. Extração de todos os turnos de `session_turns`, com metadados de `participants`.
2. Geração de um código aleatório sequencial (`P01`–`P30`) por participante, com linhas embaralhadas, sem relação com `participant_id`, `group_name` ou ordem cronológica.
3. Duas planilhas a partir da mesma base:
   - **Planilha cega** (entregue aos avaliadores): `código_cego` + transcript formatado como diálogo + colunas vazias para o nível (N0–N4).
   - **Chave de mapeamento** (só com o pesquisador): `código_cego` → `participant_id` → `group_name` → `rubric_level` original da IA.

## 5. Avaliadores

Dois colegas de curso do pesquisador, sem envolvimento no desenvolvimento do sistema, nos prompts ou na hipótese do estudo. Cada um recebeu apenas a planilha cega e o Quadro 2, sem saber a condição experimental de cada participante nem a nota original da IA. A rubrica foi aplicada de forma independente, sem consulta mútua.

**Limitação:** nenhum avaliador tem formação avançada em avaliação educacional ou em pesquisa sobre o problema de Monty Hall; ambos são estudantes de graduação em Ciência da Computação, com domínio do critério lógico-matemático, mas sem treino formal em avaliação qualitativa de discurso.

## 6. Concordância entre avaliadores

| Métrica | Valor |
|---|---|
| Kappa de Cohen (não ponderado) | 0,788 |
| Kappa ponderado (linear) | 0,848 |
| Kappa ponderado (quadrático) | 0,885 |
| Concordância exata | 83,3% (25/30) |

Valores da classificação independente, sem rodada de discussão prévia. Restaram 5 discordâncias: 4 com diferença de 1 nível (esperado em rubrica ordinal) e 1 maior (P13, diferença de 3 níveis). P13 foi consensuado como N0 após análise conjunta: o participante nunca articulou entendimento com as próprias palavras, só confirmou passivamente ("Yes"/"No") as explicações do tutor. As outras 4 foram resolvidas por consenso direto.

## 7. Validação: nota humana consensuada vs. nota original da IA

Restrita aos 25 participantes com classificação original:

- Kappa ponderado (linear), humano consensuado vs. IA: **0,39** (moderado)
- Concordância exata: 36%
- Diferença média (humano − IA) por grupo:
  - Socrático: +0,25 nível (viés pequeno)
  - Expositivo: **+1,08 nível** (a IA subavaliou este grupo em relação ao julgamento humano)

O achado é reportado no artigo (Seção 6.1) como evidência direta de viés de avaliador em contexto de LLM-as-a-judge e como explicação plausível para a perda de significância estatística na comparação principal após a correção do desfecho.

## 8. Comparação entre grupos após a reconstrução

| | N | Mediana | Mann-Whitney U | p | r (rank-biserial) | IC 95% (bootstrap, 10.000 reamostragens) |
|---|---|---|---|---|---|---|
| Socrático | 12 | 2,0 | U = 132,0 | p = 0,309 | r = 0,22 | [-0,20, 0,61] |
| Expositivo | 18 | 1,0 | | | | |

Para empates, usou-se a correção padrão de variância (`scipy.stats.mannwhitneyu(method='auto')`).

## 9. Ética (CEP/CONEP)

A pesquisa foi conduzida como iniciativa acadêmica independente, sem vínculo institucional (orientador, universidade ou laboratório) no momento da coleta. Isso impediu a submissão formal ao sistema CEP/CONEP via Plataforma Brasil, que exige uma instituição proponente cadastrada.

Salvaguardas adotadas: consentimento livre e esclarecido (antes da coleta, em três idiomas), anonimização desde a origem (identificadores gerados pela aplicação, sem nome ou e-mail), participação voluntária com possibilidade de interrupção a qualquer momento e nenhuma coleta de dados sensíveis além do necessário.

A limitação está declarada de forma transparente no artigo (Seção 7, Limitações).

---

*Os resultados gerados por esta reavaliação estão em `data/analysis/` deste repositório.*