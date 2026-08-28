# Notas de qualidade de dados - `data/raw/`

Registra anomalias conhecidas nos dados brutos exportados do Supabase, para quem quiser reutilizar o dataset.

## 1. Submissões duplicadas em `evaluation_anonymized.csv`

Dois participantes (`P005` e `P026`) têm duas linhas cada em `evaluation_anonymized.csv`, com valores numéricos idênticos e texto livre (`q6_open`) igual ou quase igual, com `created_at` diferindo por menos de 2 segundos. Isso sugere duplo envio acidental do formulário (ex.: duplo clique), não duas respostas genuínas.

**As duas linhas foram mantidas no export**, como registro fiel do banco. Nas análises do artigo, a regra foi: **manter a submissão com `created_at` mais antigo**. Resultado: 17 participantes únicos com questionário respondido, como reportado na Seção 4.3 do artigo.

## 2. Participante excluído por corte temporal

Um participante (grupo expositivo, consentimento em 2026-04-18) iniciou a sessão depois do fim da coleta (16 de abril de 2026) e foi excluído dos quatro arquivos deste diretório. Filtro aplicado em todas as exportações: `consent_at < '2026-04-18 00:00:00+00'`.

## 3. Cobertura desigual da avaliação de IA

Dos 30 participantes com ao menos um turno, apenas 25 têm `rubric_level` do classificador de IA em `session_turns_anonymized.csv` (valor mais recente por participante). Os 5 restantes nunca acionaram a avaliação automática, em geral por terem abandonado a sessão sem produzir uma explicação avaliável. Esses casos foram cobertos pela reavaliação humana cega (ver `docs/blind_rating_protocol.md`), mas não têm nota de IA para comparação.